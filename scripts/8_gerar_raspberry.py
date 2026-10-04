"""Etapa 8 - Gera a versão da Raspberry Pi na pasta raspberry/.

O que faz:
    1. Converte o best.pt para NCNN, se ainda não foi convertido ou se o treino é mais novo.
       NCNN é um motor de inferência feito para processadores ARM, como o da Raspberry:
       mais leve e rápido que o PyTorch lá (formato recomendado pelo guia Raspberry Pi da Ultralytics).
    2. Copia para raspberry/ só o que a inspeção usa: scripts, modelo NCNN e o vídeo de demonstração.

Os arquivos do Docker (Dockerfile, docker-compose.yml, iniciar.sh, LEIAME.md) já ficam em
raspberry/ e não são tocados. A pasta raspberry/ é o repositório Git baixado na Raspberry.
Rode de novo sempre que mudar um script de inspeção ou treinar um modelo novo.
"""
import shutil  # copia arquivos mantendo a data de modificação

from ultralytics import YOLO  # faz a conversão para NCNN

# Vem do config.py: modelo treinado, onde fica o NCNN, pasta da Raspberry, raiz, tamanho e vídeo
from config import (MODELO_NCNN, MODELO_TREINADO, PASTA_RASPBERRY, RAIZ, TAMANHO_IMAGEM,
                    VIDEO_PADRAO)

# Só os scripts da inspeção; treino, anotação e captura ficam no PC
SCRIPTS = ["config.py", "inspecao.py", "saida_gpio.py", "menu.py",
           "6_inspecionar.py", "6_inspecionar_basico.py", "7_ler_lotes.py"]
# Arquivos do modelo NCNN: estrutura da rede (.param), pesos (.bin) e nomes das classes (.yaml)
ARQUIVOS_NCNN = ["metadata.yaml", "model.ncnn.param", "model.ncnn.bin"]


def converter_ncnn():
    """Converte o best.pt para NCNN, só se o NCNN não existe ou é mais antigo que o best.pt."""
    pesos_ncnn = MODELO_NCNN / "model.ncnn.bin"
    if pesos_ncnn.exists() and pesos_ncnn.stat().st_mtime > MODELO_TREINADO.stat().st_mtime:
        print("Modelo NCNN já está atualizado.")
        return
    # Na primeira vez, o Ultralytics instala sozinho os pacotes ncnn e pnnx (o conversor)
    YOLO(str(MODELO_TREINADO)).export(format="ncnn", imgsz=TAMANHO_IMAGEM)


def copiar(origem, destino):
    """Copia um arquivo, criando as pastas do destino se faltarem."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origem, destino)


def main():
    """Atualiza o modelo NCNN e copia para raspberry/ tudo o que a inspeção precisa."""
    if not MODELO_TREINADO.exists():
        print("Rode antes o 4_treinar.py")
        return

    converter_ncnn()
    for nome in SCRIPTS:
        copiar(RAIZ / "scripts" / nome, PASTA_RASPBERRY / "scripts" / nome)
    # O modelo vai no mesmo caminho relativo do PC, então o config.py serve para os dois
    for nome in ARQUIVOS_NCNN:
        copiar(MODELO_NCNN / nome, PASTA_RASPBERRY / MODELO_NCNN.relative_to(RAIZ) / nome)
    copiar(VIDEO_PADRAO, PASTA_RASPBERRY / VIDEO_PADRAO.name)

    print(f"Versão da Raspberry atualizada em {PASTA_RASPBERRY}")
    print("Envie para o Git: cd raspberry && git add -A && git commit -m \"atualiza\" && git push")


if __name__ == "__main__":
    main()
