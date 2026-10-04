"""Etapa 6 (versão básica) - Inspeção sem tela.

O que faz: a mesma inspeção do 6_inspecionar.py, mas sem janela; tudo aparece
           no terminal. É a versão para a Raspberry Pi e para o Docker.
           Cada lata com defeito aciona o sopro (saida_gpio.py) e tem suas
           imagens salvas em saida/ (inspecao.py).
Parar: quando o vídeo acaba ou com Ctrl+C (o resumo é gravado mesmo assim).

Uso:
    python scripts/6_inspecionar_basico.py              (usa o VIDEO_PADRAO do config)
    python scripts/6_inspecionar_basico.py video.mp4
    python scripts/6_inspecionar_basico.py 0            (câmera 0)
"""
import sys  # sys.argv = o que foi digitado depois do nome do script (o vídeo)

import cv2                    # OpenCV: lê o vídeo ou a câmera
from ultralytics import YOLO  # carrega o modelo treinado

# Vem do config.py: posição da linha, modelo treinado e vídeo padrão
from config import LINHA_X, MODELO_INSPECAO, VIDEO_PADRAO
# Vem do inspecao.py: número da classe ok, o rastreio, o registro e a detecção
from inspecao import CLASSE_OK, Rastreio, Registro, detectar
# Vem do saida_gpio.py: o soprador
from saida_gpio import SaidaDigital


def main():
    """Lê o vídeo quadro a quadro, avalia as latas que cruzam a linha e sopra as reprovadas."""
    video = sys.argv[1] if len(sys.argv) > 1 else str(VIDEO_PADRAO)
    captura = cv2.VideoCapture(int(video) if video.isdigit() else video)  # "0" = câmera
    modelo = YOLO(str(MODELO_INSPECAO), task="detect")  # NCNN ou best.pt (config.py)
    rastreio, registro, sopro = Rastreio(), Registro(), SaidaDigital()
    print("Inspecionando... pressione Ctrl+C para parar.")

    try:
        while True:
            ok, quadro = captura.read()
            if not ok:  # fim do vídeo
                break
            linha = int(quadro.shape[1] * LINHA_X)  # x da linha em pixels
            for caixa, classe in rastreio.atualizar(detectar(modelo, quadro), linha):
                numero = registro.adicionar(quadro, caixa, classe)
                if classe != CLASSE_OK:
                    sopro.soprar(numero)
    except KeyboardInterrupt:  # Ctrl+C: para a inspeção, mas ainda grava o resumo
        print("\nInspeção interrompida.")
    finally:  # roda sempre, terminando bem ou com Ctrl+C
        captura.release()
        registro.fechar()


if __name__ == "__main__":
    main()
