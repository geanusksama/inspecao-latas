"""API HTTP da inspeção: recebe uma imagem e devolve as latas encontradas.

O que faz: carrega o modelo uma vez (NCNN se existir, senão best.pt) e expõe:
    GET  /saude             o serviço está no ar? qual modelo está carregado?
    POST /detectar          detecções em JSON (classe, confiança, caixa, metadados)
    POST /detectar/imagem   a mesma imagem em PNG, com as caixas e os rótulos desenhados
    GET  /docs              página Swagger para testar tudo pelo navegador

Pipeline de cada requisição:
    pré-processamento   bytes do upload → imagem OpenCV (decodificar e validar)
    inferência          YOLO (o Ultralytics redimensiona para 640 px internamente)
    pós-processamento   caixas → JSON com conforme/não conforme, ou → PNG anotado

Uso:
    uvicorn api:app --app-dir scripts --host 0.0.0.0 --port 8000      (no Docker já roda assim)
    curl -F "arquivo=@lata.jpg" http://localhost:8000/detectar
"""
import threading                 # trava: uma inferência por vez no mesmo modelo
from contextlib import asynccontextmanager

import cv2                       # decodifica a imagem recebida e desenha as caixas
import numpy as np               # transforma os bytes do upload num array para o OpenCV
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from ultralytics import YOLO

# Vem do config.py: nomes e cores das classes, confiança mínima e qual modelo usar
from config import CLASSES, CONFIANCA, CORES, MODELO_INSPECAO, MODELO_NCNN
# Vem do inspecao.py: número da classe lata_ok (as outras são defeito)
from inspecao import CLASSE_OK, FONTE

TAMANHO_MAXIMO = 10 * 1024 * 1024  # 10 MB por imagem: protege a memória da Raspberry (2 GB)
estado = {}                        # guarda o modelo carregado na inicialização
trava = threading.Lock()


@asynccontextmanager
async def ciclo_de_vida(_app):
    """Carrega o modelo uma única vez, quando o servidor sobe (e não a cada requisição)."""
    estado["modelo"] = YOLO(str(MODELO_INSPECAO), task="detect")
    estado["formato"] = "ncnn" if MODELO_INSPECAO == MODELO_NCNN else "pytorch"
    yield
    estado.clear()


app = FastAPI(title="Inspeção de Latas — Edge AI",
              description="Detecção de latas com defeito (YOLO26 + NCNN) para Raspberry Pi 5.",
              version="1.0.0", lifespan=ciclo_de_vida)


def ler_imagem(arquivo):
    """Pré-processamento: bytes do upload → imagem BGR do OpenCV.

    Recusa (HTTP 400/413) arquivos vazios, grandes demais ou que não são imagem.
    """
    dados = arquivo.file.read(TAMANHO_MAXIMO + 1)
    if not dados:
        raise HTTPException(400, "Arquivo vazio.")
    if len(dados) > TAMANHO_MAXIMO:
        raise HTTPException(413, "Imagem maior que 10 MB.")
    imagem = cv2.imdecode(np.frombuffer(dados, np.uint8), cv2.IMREAD_COLOR)
    if imagem is None:
        raise HTTPException(400, "O arquivo não é uma imagem válida (use JPG ou PNG).")
    return imagem


def inferir(imagem):
    """Inferência: roda o YOLO na imagem e devolve o resultado do Ultralytics.

    agnostic_nms: se a mesma lata vier com 2 caixas de classes diferentes, fica a mais forte.
    """
    with trava:
        return estado["modelo"].predict(imagem, conf=CONFIANCA, agnostic_nms=True, verbose=False)[0]


def para_json(resultado, imagem):
    """Pós-processamento: transforma o resultado em detecções, resumo e metadados."""
    deteccoes = []
    for classe, confianca, (x1, y1, x2, y2) in zip(resultado.boxes.cls.int().tolist(),
                                                   resultado.boxes.conf.tolist(),
                                                   resultado.boxes.xyxy.int().tolist()):
        deteccoes.append({
            "classe": CLASSES[classe],
            "confianca": round(confianca, 3),
            "conforme": classe == CLASSE_OK,
            "caixa": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
        })
    nao_conformes = sum(not d["conforme"] for d in deteccoes)
    altura, largura = imagem.shape[:2]
    return {
        "deteccoes": deteccoes,
        "resumo": {"total": len(deteccoes), "conformes": len(deteccoes) - nao_conformes,
                   "nao_conformes": nao_conformes},
        "metadados": {
            "modelo": "YOLO26n ajustado (4 classes)",
            "formato": estado["formato"],
            "imagem": {"largura": largura, "altura": altura},
            "confianca_minima": CONFIANCA,
            # tempos medidos pelo Ultralytics, em milissegundos
            "tempo_ms": {etapa: round(ms, 1) for etapa, ms in resultado.speed.items()},
        },
    }


def anotar(resultado, imagem):
    """Pós-processamento: desenha caixa + "classe confiança" de cada lata, na cor da classe."""
    for classe, confianca, (x1, y1, x2, y2) in zip(resultado.boxes.cls.int().tolist(),
                                                   resultado.boxes.conf.tolist(),
                                                   resultado.boxes.xyxy.int().tolist()):
        cor = CORES[classe]
        cv2.rectangle(imagem, (x1, y1), (x2, y2), cor, 2)
        cv2.putText(imagem, f"{CLASSES[classe]} {confianca:.2f}", (x1, max(y1 - 6, 12)),
                    FONTE, 0.5, cor, 2, cv2.LINE_AA)
    return imagem


@app.get("/saude")
def saude():
    """Diz se o serviço está no ar e qual modelo está carregado."""
    return {"status": "ok", "modelo": str(MODELO_INSPECAO.name), "formato": estado.get("formato"),
            "classes": CLASSES}


@app.post("/detectar")
def detectar(arquivo: UploadFile = File(..., description="Imagem JPG ou PNG")):
    """Detecta as latas e devolve JSON: detecções, resumo e metadados."""
    imagem = ler_imagem(arquivo)
    return para_json(inferir(imagem), imagem)


@app.post("/detectar/imagem", response_class=Response,
          responses={200: {"content": {"image/png": {}}, "description": "Imagem anotada"}})
def detectar_imagem(arquivo: UploadFile = File(..., description="Imagem JPG ou PNG")):
    """Detecta as latas e devolve a imagem em PNG com as caixas e os rótulos desenhados."""
    imagem = ler_imagem(arquivo)
    resultado = inferir(imagem)
    ok, png = cv2.imencode(".png", anotar(resultado, imagem))
    if not ok:
        raise HTTPException(500, "Falha ao gerar o PNG.")
    return Response(content=png.tobytes(), media_type="image/png")
