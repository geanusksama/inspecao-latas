"""Etapa 4 - Treino do modelo YOLO26 na GPU.

O que faz: pega o modelo pronto yolo26n.pt (que já sabe reconhecer objetos em geral)
           e ensina as nossas 4 classes de lata, usando o data.yaml do 3_separar.py.
Resultado: treinos/latas/weights/best.pt -> o "cérebro" usado pelo
           5_prerotular.py e pela inspeção (6_inspecionar*.py).
"""
# YOLO (biblioteca Ultralytics): carrega o modelo e faz o treino
from ultralytics import YOLO

# Vem do config.py: o data.yaml, os parâmetros de treino e onde salvar
from config import (ARQUIVO_DATA, EPOCAS, LOTE_TREINO, MODELO_BASE, MODELO_TREINADO,
                    PASTA_TREINOS, TAMANHO_IMAGEM)


def main():
    """Treina o modelo e mostra onde ficou o melhor resultado."""
    if not ARQUIVO_DATA.exists():
        print("Rode antes o 3_separar.py")
        return

    modelo = YOLO(MODELO_BASE)  # se o yolo26n.pt não existir, é baixado sozinho
    modelo.train(
        data=str(ARQUIVO_DATA),      # onde estão as imagens e as classes
        epochs=EPOCAS,               # quantas passadas por todas as imagens
        imgsz=TAMANHO_IMAGEM,        # tamanho das imagens no treino (640 px)
        batch=LOTE_TREINO,           # imagens processadas por vez
        device=0,                    # 0 = primeira GPU
        project=str(PASTA_TREINOS),  # pasta dos resultados (treinos/)
        name="latas",                # subpasta: treinos/latas/
        exist_ok=True,               # sobrescreve o treino anterior
    )
    print(f"Modelo treinado: {MODELO_TREINADO}")


if __name__ == "__main__":
    main()
