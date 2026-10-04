"""Etapa 1 - Captura do dataset.

O que faz: lê os vídeos da pasta vtrieino/ e salva algumas imagens de cada um
           em dataset/imagens/. Essas imagens são o material do treino.
Próximo passo: 2_anotar.py (marcar as latas nessas imagens).
"""
# cv2 = OpenCV. Aqui é usado para abrir o vídeo, ler quadro a quadro e salvar .jpg
import cv2

# Vem do config.py:
#   PASTA_VIDEOS  -> de onde ler os vídeos (vtrieino/)
#   PASTA_IMAGENS -> onde salvar as imagens (dataset/imagens/)
#   PASSO_QUADROS -> salvar 1 a cada quantos quadros (10)
from config import PASTA_IMAGENS, PASTA_VIDEOS, PASSO_QUADROS

# Só arquivos com estas extensões são tratados como vídeo
EXTENSOES_VIDEO = {".mp4", ".avi", ".mov", ".mkv"}


def extrair_quadros(video, destino, passo):
    """Salva 1 de cada `passo` quadros do vídeo como imagem .jpg.

    Recebe:  video   -> arquivo de vídeo
             destino -> pasta onde salvar as imagens
             passo   -> ex.: 10 = salva os quadros 0, 10, 20, 30...
    Devolve: quantas imagens foram salvas
    Exemplo de nome salvo: curto_000010.jpg (vídeo "curto", quadro 10)
    """
    captura = cv2.VideoCapture(str(video))
    numero_quadro = salvos = 0

    while True:
        ok, quadro = captura.read()     # pega o próximo quadro
        if not ok:                      # acabou o vídeo
            break
        if numero_quadro % passo == 0:  # é um quadro múltiplo do passo? salva
            nome = destino / f"{video.stem}_{numero_quadro:06d}.jpg"
            cv2.imwrite(str(nome), quadro)
            salvos += 1
        numero_quadro += 1

    captura.release()
    return salvos


def main():
    """Roda a captura em todos os vídeos da pasta e mostra quantas imagens saíram de cada um."""
    PASTA_IMAGENS.mkdir(parents=True, exist_ok=True)  # cria a pasta se ainda não existir
    videos = [v for v in PASTA_VIDEOS.iterdir() if v.suffix.lower() in EXTENSOES_VIDEO]

    if not videos:
        print(f"Nenhum vídeo encontrado em {PASTA_VIDEOS}")
        return

    for video in videos:
        total = extrair_quadros(video, PASTA_IMAGENS, PASSO_QUADROS)
        print(f"{video.name}: {total} imagens salvas")

    print(f"Imagens em: {PASTA_IMAGENS}")


# Roda o main() só quando o arquivo é executado direto (python scripts/1_capturar.py)
if __name__ == "__main__":
    main()
