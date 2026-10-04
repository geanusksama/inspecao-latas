"""Etapa 6 - Inspeção da linha de produção (com tela).

O que faz: lê um vídeo (ou câmera), acha e segue cada lata e, quando ela cruza a
           linha vertical amarela, decide se é conforme ou não. A lata com defeito
           aciona o sopro (saida_gpio.py) e, na tela, ganha uma bolinha vermelha.
           A lógica fica em inspecao.py; este arquivo cuida só da tela.
Parar: quando o vídeo acaba, com q ou ESC na janela, ou com Ctrl+C.
Sem tela: use o 6_inspecionar_basico.py.

Uso:
    python scripts/6_inspecionar.py                    (usa o VIDEO_PADRAO do config)
    python scripts/6_inspecionar.py outro_video.mp4
    python scripts/6_inspecionar.py 0                  (câmera 0)
"""
import sys   # sys.argv = o que foi digitado depois do nome do script (o vídeo)
import time  # relógio, para o vídeo rodar na velocidade real

import cv2                    # OpenCV: lê o vídeo, desenha e mostra a janela
from ultralytics import YOLO  # carrega o modelo treinado

# Vem do config.py: nomes e cores das classes, posição da linha, modelo e vídeo padrão
from config import CLASSES, CORES, LINHA_X, MODELO_INSPECAO, VIDEO_PADRAO
# Vem do inspecao.py: número da classe ok, fonte, rastreio, registro e detecção
from inspecao import CLASSE_OK, FONTE, Rastreio, Registro, detectar
# Vem do saida_gpio.py: o soprador
from saida_gpio import SaidaDigital

# Cores em BGR (Azul, Verde, Vermelho)
AMARELO = (0, 255, 255)
BRANCO = (255, 255, 255)
VERMELHO = (0, 0, 255)


def sincronizar(captura, fps, inicio):
    """Faz o vídeo rodar na velocidade real (nem câmera lenta, nem acelerado).

    Compara em que quadro o vídeo está com o quadro em que deveria estar pelo relógio:
        atrasado  -> pula quadros
        adiantado -> devolve quantos ms esperar antes do próximo
    Devolve: ms de espera (mínimo 1), usado no cv2.waitKey()
    """
    atual = captura.get(cv2.CAP_PROP_POS_FRAMES)
    ideal = (time.perf_counter() - inicio) * fps
    while ideal - atual > 1 and captura.grab():  # grab() pula um quadro sem decodificar
        atual += 1
    return max(1, int((atual - ideal) * 1000 / fps))


def acender_luz(quadro, caixa):
    """Desenha a bolinha vermelha + "SOPRADA" acima da lata reprovada (simula o sopro)."""
    x1, y1, x2, _ = caixa
    centro = ((x1 + x2) // 2, y1 - 22)
    cv2.circle(quadro, centro, 13, VERMELHO, -1, cv2.LINE_AA)  # bolinha
    cv2.circle(quadro, centro, 13, BRANCO, 2, cv2.LINE_AA)     # borda branca
    cv2.putText(quadro, "SOPRADA", (centro[0] + 18, centro[1] + 6), FONTE, 0.55, VERMELHO, 2, cv2.LINE_AA)


def desenhar_painel(quadro, registro):
    """Desenha o placar no topo: total, conformes, não conformes e quantidade por classe."""
    total = sum(registro.por_classe.values())
    ok = registro.por_classe[CLASSE_OK]

    # Fundo escuro semitransparente: pinta uma cópia e mistura com a original
    fundo = quadro.copy()
    cv2.rectangle(fundo, (0, 0), (quadro.shape[1], 66), (30, 30, 30), -1)
    cv2.addWeighted(fundo, 0.75, quadro, 0.25, 0, quadro)

    cv2.putText(quadro, f"Total: {total}   Conformes: {ok}   Nao conformes (sopradas): {total - ok}",
                (10, 25), FONTE, 0.65, BRANCO, 2, cv2.LINE_AA)
    x = 10
    for i, nome in enumerate(CLASSES):  # uma contagem por classe, na cor da classe
        texto = f"{nome}: {registro.por_classe[i]}"
        cv2.putText(quadro, texto, (x, 52), FONTE, 0.6, CORES[i], 2, cv2.LINE_AA)
        x += cv2.getTextSize(texto, FONTE, 0.6, 2)[0][0] + 30  # próximo texto ao lado


def desenhar(quadro, deteccoes, linha, registro, avaliadas):
    """Desenha tudo na tela: linha amarela, caixas das latas e placar.

    Antes da linha: caixa fina com o que o modelo está vendo.
    Depois da linha: caixa grossa com a classe final; se reprovada, bolinha vermelha.
    """
    cv2.line(quadro, (linha, 0), (linha, quadro.shape[0]), AMARELO, 2)
    for id_lata, classe, caixa in deteccoes:
        espessura = 1
        if id_lata in avaliadas:  # já cruzou a linha
            classe, espessura = avaliadas[id_lata], 3
            if classe != CLASSE_OK:
                acender_luz(quadro, caixa)
        x1, y1, x2, y2 = caixa
        cv2.rectangle(quadro, (x1, y1), (x2, y2), CORES[classe], espessura)
        cv2.putText(quadro, CLASSES[classe], (x1, y2 + 20), FONTE, 0.55, (0, 0, 0), 5, cv2.LINE_AA)  # contorno preto
        cv2.putText(quadro, CLASSES[classe], (x1, y2 + 20), FONTE, 0.55, CORES[classe], 2, cv2.LINE_AA)
    desenhar_painel(quadro, registro)


def main():
    """Lê o vídeo, avalia as latas que cruzam a linha, sopra as reprovadas e mostra tudo na janela."""
    video = sys.argv[1] if len(sys.argv) > 1 else str(VIDEO_PADRAO)
    fonte = int(video) if video.isdigit() else video  # "0" = câmera
    captura = cv2.VideoCapture(fonte)
    modelo = YOLO(str(MODELO_INSPECAO), task="detect")  # NCNN ou best.pt (config.py)
    rastreio, registro, sopro = Rastreio(), Registro(), SaidaDigital()
    tempo_real = isinstance(fonte, str)          # arquivo: segura na velocidade real; câmera já é tempo real
    fps = captura.get(cv2.CAP_PROP_FPS) or 30   # quadros por segundo do vídeo
    inicio = None  # relógio começa só após o 1º quadro (ele é lento: carrega o modelo na GPU)
    print("Inspecionando... pressione q ou ESC na janela (ou Ctrl+C aqui) para parar.")

    try:
        while True:
            ok, quadro = captura.read()
            if not ok:  # fim do vídeo
                break
            linha = int(quadro.shape[1] * LINHA_X)  # x da linha em pixels
            deteccoes = detectar(modelo, quadro)

            for caixa, classe in rastreio.atualizar(deteccoes, linha):
                numero = registro.adicionar(quadro, caixa, classe)  # grava antes de desenhar (imagem limpa)
                if classe != CLASSE_OK:
                    sopro.soprar(numero)

            desenhar(quadro, deteccoes, linha, registro, rastreio.avaliadas)
            cv2.imshow("Inspecao", quadro)
            inicio = inicio or time.perf_counter()
            espera = sincronizar(captura, fps, inicio) if tempo_real else 1
            if cv2.waitKey(espera) & 0xFF in (ord("q"), 27):  # q ou ESC para parar
                break
    except KeyboardInterrupt:  # Ctrl+C: para a inspeção, mas ainda grava o resumo
        print("\nInspeção interrompida.")
    finally:  # roda sempre, terminando bem ou com Ctrl+C
        captura.release()
        cv2.destroyAllWindows()
        registro.fechar()


if __name__ == "__main__":
    main()
