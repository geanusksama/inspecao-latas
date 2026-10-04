"""Etapa 5 - Pré-rotulagem automática (opcional).

O que faz: usa o modelo já treinado (4_treinar.py) para marcar sozinho as latas
           nas imagens que ainda não têm rótulo. Você só confere e corrige no
           2_anotar.py, em vez de desenhar tudo à mão.
           Imagens que já têm rótulo não são alteradas.
Ciclo: anota algumas -> treina -> pré-rotula o resto -> corrige -> treina de novo.
"""
# YOLO (Ultralytics): carrega o modelo treinado e detecta as latas
from ultralytics import YOLO

# Vem do config.py: confiança mínima, modelo treinado, pasta das imagens e dos rótulos
from config import CONFIANCA, MODELO_TREINADO, PASTA_IMAGENS, PASTA_ROTULOS


def main():
    """Cria o .txt de rótulo de cada imagem que ainda não tem um."""
    if not MODELO_TREINADO.exists():
        print("Rode antes o 4_treinar.py")
        return

    modelo = YOLO(str(MODELO_TREINADO))
    # Lista só as imagens sem .txt
    pendentes = [img for img in sorted(PASTA_IMAGENS.glob("*.jpg"))
                 if not (PASTA_ROTULOS / f"{img.stem}.txt").exists()]

    for imagem in pendentes:
        caixas = modelo.predict(str(imagem), conf=CONFIANCA, verbose=False)[0].boxes
        # Cada caixa vira uma linha "classe x_centro y_centro largura altura" (0 a 1).
        # O YOLO já entrega nesse formato em xywhn (n = normalizado).
        linhas = [f"{int(c)} {x:.6f} {y:.6f} {w:.6f} {h:.6f}"
                  for c, (x, y, w, h) in zip(caixas.cls.tolist(), caixas.xywhn.tolist())]
        if linhas:  # só salva se achou alguma lata
            (PASTA_ROTULOS / f"{imagem.stem}.txt").write_text("\n".join(linhas))

    print(f"{len(pendentes)} imagens pré-rotuladas. Confira tudo com o 2_anotar.py")


if __name__ == "__main__":
    main()
