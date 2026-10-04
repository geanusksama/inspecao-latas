"""Etapa 8 - Converte o modelo treinado para NCNN (para a Raspberry Pi e o Docker).

O que faz: transforma o best.pt (formato do PyTorch) em best_ncnn_model/, o formato NCNN.
           NCNN é um motor de inferência feito para processadores ARM, como o da Raspberry:
           mais leve e mais rápido que o PyTorch na CPU (recomendado pelo guia Raspberry Pi
           da Ultralytics). A pasta gerada tem:
               model.ncnn.param   estrutura da rede
               model.ncnn.bin     pesos (o que o modelo aprendeu)
               metadata.yaml      nomes das classes e tamanho da imagem
Depois:    a inspeção e a API passam a usar o NCNN sozinhas (MODELO_INSPECAO no config.py),
           e o Dockerfile copia essa pasta para a imagem.
           Rode de novo sempre que treinar um modelo novo (4_treinar.py).
"""
# YOLO (Ultralytics): carrega o best.pt e faz a conversão
from ultralytics import YOLO

# Vem do config.py: o modelo treinado, onde fica o NCNN e o tamanho de imagem do treino
from config import MODELO_NCNN, MODELO_TREINADO, TAMANHO_IMAGEM


def main():
    """Converte o best.pt para NCNN, só se o NCNN não existe ou é mais antigo que o best.pt."""
    if not MODELO_TREINADO.exists():
        print("Rode antes o 4_treinar.py")
        return
    pesos_ncnn = MODELO_NCNN / "model.ncnn.bin"
    if pesos_ncnn.exists() and pesos_ncnn.stat().st_mtime > MODELO_TREINADO.stat().st_mtime:
        print(f"Modelo NCNN já está atualizado: {MODELO_NCNN}")
        return
    # Na primeira vez, o Ultralytics instala sozinho os pacotes ncnn e pnnx (o conversor)
    YOLO(str(MODELO_TREINADO)).export(format="ncnn", imgsz=TAMANHO_IMAGEM)
    print(f"Modelo NCNN: {MODELO_NCNN}")


if __name__ == "__main__":
    main()
