"""Etapa 9 - Benchmark: quanto tempo o modelo leva por imagem em cada formato.

O que faz: roda o mesmo modelo em 3 configurações, nos mesmos quadros do vídeo da esteira,
           e mede a latência (ms por imagem) e os quadros por segundo (FPS):
               PyTorch na CPU   o best.pt sem placa de vídeo
               NCNN na CPU      o formato usado no Docker e na Raspberry Pi
               PyTorch na GPU   referência do PC de desenvolvimento (se houver CUDA)
           Grava a tabela em docs/benchmark.md (usada no README).
Por quê:   a Raspberry Pi 5 não tem GPU; medir na CPU mostra o ganho real do NCNN.
"""
import platform  # nome do processador e do sistema, para registrar onde foi medido
import statistics
import time
from datetime import date

import cv2
import torch                  # só para saber se há GPU (CUDA)
from ultralytics import YOLO

# Vem do config.py: os dois modelos, o vídeo e a confiança mínima
from config import CONFIANCA, MODELO_NCNN, MODELO_TREINADO, RAIZ, VIDEO_PADRAO

QUADROS = 100      # quadros medidos
AQUECIMENTO = 10   # primeiras inferências descartadas (carregam o modelo e caches)


def ler_quadros(quantidade):
    """Pega quadros espaçados do vídeo da esteira (cenas variadas, sempre as mesmas)."""
    captura = cv2.VideoCapture(str(VIDEO_PADRAO))
    total = int(captura.get(cv2.CAP_PROP_FRAME_COUNT))
    quadros = []
    for indice in range(0, total, max(total // quantidade, 1))[:quantidade]:
        captura.set(cv2.CAP_PROP_POS_FRAMES, indice)
        ok, quadro = captura.read()
        if ok:
            quadros.append(quadro)
    captura.release()
    return quadros


def medir(modelo, quadros, dispositivo):
    """Roda o modelo em cada quadro e devolve a mediana e o percentil 95 da latência (ms)."""
    for quadro in quadros[:AQUECIMENTO]:
        modelo.predict(quadro, conf=CONFIANCA, device=dispositivo, verbose=False)
    tempos = []
    for quadro in quadros:
        inicio = time.perf_counter()
        modelo.predict(quadro, conf=CONFIANCA, device=dispositivo, verbose=False)
        tempos.append((time.perf_counter() - inicio) * 1000)
    tempos.sort()
    return statistics.median(tempos), tempos[int(len(tempos) * 0.95) - 1]


def main():
    """Mede as configurações disponíveis e grava docs/benchmark.md."""
    quadros = ler_quadros(QUADROS)
    configuracoes = [("PyTorch (best.pt)", MODELO_TREINADO, "cpu", "CPU"),
                     ("NCNN (best_ncnn_model)", MODELO_NCNN, "cpu", "CPU")]
    if torch.cuda.is_available():
        configuracoes.append(("PyTorch (best.pt)", MODELO_TREINADO, 0, f"GPU {torch.cuda.get_device_name()}"))

    linhas = []
    for nome, caminho, dispositivo, onde in configuracoes:
        if not caminho.exists():
            print(f"Pulando {nome}: {caminho} não existe")
            continue
        modelo = YOLO(str(caminho), task="detect")
        mediana, p95 = medir(modelo, quadros, dispositivo)
        linhas.append(f"| {nome} | {onde} | {mediana:.1f} | {p95:.1f} | {1000 / mediana:.1f} |")
        print(linhas[-1])

    processador = platform.processor() or platform.machine()
    texto = (f"# Benchmark de inferência\n\n"
             f"Medido em {date.today():%d/%m/%Y} | {platform.system()} {platform.release()} | "
             f"processador: {processador} | {len(quadros)} quadros 1280×720 do vídeo da esteira "
             f"(entrada do modelo: 640 px) | tempo total do `predict` (pré + inferência + pós).\n\n"
             f"| Modelo | Onde | Mediana (ms) | P95 (ms) | FPS (mediana) |\n"
             f"| --- | --- | --- | --- | --- |\n" + "\n".join(linhas) + "\n")
    destino = RAIZ / "docs" / "benchmark.md"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(texto, encoding="utf-8")
    print(f"Tabela gravada em {destino}")


if __name__ == "__main__":
    main()
