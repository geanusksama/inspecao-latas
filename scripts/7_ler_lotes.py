"""Etapa 7 - Leitura do lote das latas com defeito.

O que faz: depois da inspeção, abre o recorte de cada lata reprovada
           (saida/recortes/, salvo pelo inspecao.py) e lê o texto "LOTE N" com OCR.
           Roda fora da linha de produção, então não atrasa a inspeção.
Gera em saida/:
    lotes.csv          uma linha por lata com defeito: número, hora, classe, lote, imagens
    resumo_lotes.txt   quantos defeitos cada lote teve, por tipo
Quem chama: o menu.py (opção Relatório), ou rodando direto.
"""
import csv      # lê o inspecao.csv e grava o lotes.csv
import logging  # usado só para esconder as mensagens internas do OCR
import re       # expressão regular: acha "LOTE 7" no texto lido
from collections import Counter, defaultdict  # contadores por lote e por classe

import cv2                    # OpenCV: abre a imagem do recorte
from rapidocr import RapidOCR  # OCR: transforma a imagem do texto em texto

# Vem do config.py: pasta saida/
from config import PASTA_SAIDA

# Procura "LOTE" seguido de número. [O0] aceita a letra O lida como zero (L0TE 7).
REGEX_LOTE = re.compile(r"L[O0]TE\s*(\d+)")
LOTE_DESCONHECIDO = "ND"  # "não detectado": quando o OCR não consegue ler

logging.getLogger("RapidOCR").setLevel(logging.WARNING)  # esconde as mensagens internas do OCR


def ler_lote(ocr, caminho):
    """Lê o número do lote na imagem de uma lata.

    Recebe:  o OCR e o caminho do recorte da lata
    Devolve: o número do lote como texto (ex.: "7"), ou "ND" se não conseguir ler
    Usa só a metade de baixo da lata, que é onde o lote é impresso (mais rápido e preciso).
    """
    imagem = cv2.imread(str(caminho))
    metade_de_baixo = imagem[imagem.shape[0] // 2:]
    for texto in ocr(metade_de_baixo).txts or ():  # .txts = textos encontrados
        achou = REGEX_LOTE.search(texto.upper())
        if achou:
            return achou.group(1)  # só o número
    return LOTE_DESCONHECIDO


def ler_defeitos():
    """Devolve as linhas do inspecao.csv que são latas não conformes."""
    with open(PASTA_SAIDA / "inspecao.csv", encoding="utf-8") as arquivo:
        return [lata for lata in csv.DictReader(arquivo, delimiter=";")
                if lata["situacao"] == "nao_conforme"]


def escrever_resumo(por_lote):
    """Grava o resumo_lotes.txt e mostra no terminal quantos defeitos cada lote teve.

    Recebe: dicionário lote -> contagem por classe
    Os lotes saem em ordem numérica (7, 8, 10): ordena pelo tamanho do texto e depois pelo texto.
    """
    linhas = ["Defeitos por lote:"]
    for lote, contagem in sorted(por_lote.items(), key=lambda item: (len(item[0]), item[0])):
        detalhes = ", ".join(f"{classe}={n}" for classe, n in sorted(contagem.items()))
        linhas.append(f"  lote {lote}: {sum(contagem.values())} ({detalhes})")
    (PASTA_SAIDA / "resumo_lotes.txt").write_text("\n".join(linhas), encoding="utf-8")
    print("\n".join(linhas))


def main():
    """Lê o lote de cada lata com defeito e grava o lotes.csv e o resumo_lotes.txt."""
    if not (PASTA_SAIDA / "inspecao.csv").exists():
        print("Rode antes a inspeção (6_inspecionar.py ou 6_inspecionar_basico.py)")
        return

    ocr = RapidOCR()
    por_lote = defaultdict(Counter)  # lote -> contagem por classe

    with open(PASTA_SAIDA / "lotes.csv", "w", newline="", encoding="utf-8") as arquivo:
        saida = csv.writer(arquivo, delimiter=";")
        saida.writerow(["numero", "data_hora", "classe", "lote", "imagem", "recorte"])
        for lata in ler_defeitos():
            lote = ler_lote(ocr, PASTA_SAIDA / lata["recorte"])
            por_lote[lote][lata["classe"]] += 1
            saida.writerow([lata["numero"], lata["data_hora"], lata["classe"], lote,
                            lata["imagem"], lata["recorte"]])
            print(f"Lata {lata['numero']}: {lata['classe']} | lote {lote}")

    escrever_resumo(por_lote)


if __name__ == "__main__":
    main()
