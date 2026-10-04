"""Etapa 3 - Separação em treino e validação.

O que faz: pega as imagens que já têm rótulo (2_anotar.py), sorteia 20% para
           validação e copia tudo para dataset/yolo/ na estrutura que o YOLO exige:
               images/train  labels/train   -> o modelo aprende com estas
               images/val    labels/val     -> servem para testar se ele aprendeu
           Também cria o data.yaml, que diz ao YOLO onde estão as imagens e quais são as classes.
Próximo passo: 4_treinar.py (lê o data.yaml).
"""
import random  # sorteia a ordem das imagens
import shutil  # copia arquivos e apaga pastas

# Vem do config.py:
#   PASTA_IMAGENS, PASTA_ROTULOS -> origem (imagens e .txt)
#   PASTA_YOLO, ARQUIVO_DATA     -> destino (dataset/yolo e data.yaml)
#   CLASSES                      -> nomes escritos no data.yaml
#   FRACAO_VALIDACAO             -> quanto vai para validação (0.2 = 20%)
from config import (ARQUIVO_DATA, CLASSES, FRACAO_VALIDACAO, PASTA_IMAGENS,
                    PASTA_ROTULOS, PASTA_YOLO)


def copiar(rotulos, parte):
    """Copia as imagens e os .txt para a pasta de treino ou de validação.

    Recebe: lista de .txt e a parte ("train" ou "val")
    Exemplo: rotulos/x.txt -> yolo/labels/train/x.txt e imagens/x.jpg -> yolo/images/train/x.jpg
    """
    for pasta in ("images", "labels"):
        (PASTA_YOLO / pasta / parte).mkdir(parents=True, exist_ok=True)
    for rotulo in rotulos:
        shutil.copy(PASTA_IMAGENS / f"{rotulo.stem}.jpg", PASTA_YOLO / "images" / parte)
        shutil.copy(rotulo, PASTA_YOLO / "labels" / parte)


def main():
    """Monta o dataset/yolo do zero e escreve o data.yaml."""
    rotulos = sorted(PASTA_ROTULOS.glob("*.txt"))  # só imagens com rótulo entram
    if len(rotulos) < 2:
        print("Rotule pelo menos 2 imagens com o 2_anotar.py antes de separar.")
        return

    shutil.rmtree(PASTA_YOLO, ignore_errors=True)  # apaga a separação anterior
    random.seed(42)            # sorteio sempre igual para os mesmos rótulos
    random.shuffle(rotulos)

    n_val = max(1, round(len(rotulos) * FRACAO_VALIDACAO))  # pelo menos 1 de validação
    copiar(rotulos[n_val:], "train")
    copiar(rotulos[:n_val], "val")

    nomes = "\n".join(f"  {i}: {nome}" for i, nome in enumerate(CLASSES))
    ARQUIVO_DATA.write_text(
        f"path: {PASTA_YOLO.as_posix()}\ntrain: images/train\nval: images/val\nnames:\n{nomes}\n"
    )
    print(f"Treino: {len(rotulos) - n_val} imagens | Validação: {n_val} imagens")
    print(f"Configuração: {ARQUIVO_DATA}")


if __name__ == "__main__":
    main()
