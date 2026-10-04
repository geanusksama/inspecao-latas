"""Configurações centrais do projeto. Todos os scripts importam daqui.

Por que existe: em vez de cada script ter caminhos e números "soltos" no código,
tudo que pode mudar (pastas, classes, parâmetros de treino, posição da linha,
pino do GPIO...) fica aqui. Para ajustar o sistema, normalmente só se mexe neste arquivo.

Quem usa o quê:
    1_capturar.py        PASTA_VIDEOS, PASTA_IMAGENS, PASSO_QUADROS
    2_anotar.py          CLASSES, CORES, PASTA_IMAGENS, PASTA_ROTULOS
    3_separar.py         CLASSES, PASTA_IMAGENS, PASTA_ROTULOS, PASTA_YOLO, ARQUIVO_DATA, FRACAO_VALIDACAO
    4_treinar.py         MODELO_BASE, ARQUIVO_DATA, EPOCAS, TAMANHO_IMAGEM, LOTE_TREINO, PASTA_TREINOS
    5_prerotular.py      MODELO_TREINADO, CONFIANCA, PASTA_IMAGENS, PASTA_ROTULOS
    inspecao.py          CLASSES, CONFIANCA, CORES, PASTA_SAIDA
    6_inspecionar*.py    LINHA_X, MODELO_INSPECAO, VIDEO_PADRAO, CLASSES, CORES
    8_gerar_raspberry.py MODELO_TREINADO, MODELO_NCNN, PASTA_RASPBERRY, TAMANHO_IMAGEM, VIDEO_PADRAO
    saida_gpio.py        PINO_GPIO, TEMPO_SOPRO
    7_ler_lotes.py       PASTA_SAIDA
    menu.py              PASTA_SAIDA, VIDEO_PADRAO, SEM_TELA
"""
# os.environ lê variáveis de ambiente (o Docker define SEM_TELA=1)
import os
# Path (da biblioteca padrão pathlib) representa caminhos de arquivos/pastas.
# Permite montar caminhos com "/" (ex.: RAIZ / "dataset") e funciona igual
# no Windows, no Linux da Raspberry Pi e no Docker.
from pathlib import Path

# __file__ é o caminho deste arquivo (scripts/config.py).
# .parent = pasta scripts/; .parent.parent = pasta do projeto (YOLOENTREGA).
# Todos os outros caminhos partem daqui, então o projeto funciona em qualquer
# pasta ou computador, sem caminhos fixos como "D:\...".
RAIZ = Path(__file__).parent.parent  # pasta do projeto (um nível acima de scripts/)

# ---------------------------------------------------------------- DATASET
# Vídeos usados para montar o dataset (lidos pelo 1_capturar.py)
PASTA_VIDEOS = RAIZ / "vtrieino"

# Imagens extraídas dos vídeos, ainda sem rótulo (criadas pelo 1_capturar.py)
PASTA_IMAGENS = RAIZ / "dataset" / "imagens"

# Rótulos YOLO (.txt), um por imagem, com o mesmo nome da imagem
# (criados pelo 2_anotar.py ou pelo 5_prerotular.py)
PASTA_ROTULOS = RAIZ / "dataset" / "rotulos"

# Salva 1 quadro a cada N quadros do vídeo (30 fps / 10 = 3 imagens por segundo)
PASSO_QUADROS = 10

# Classes que o modelo vai aprender. A ORDEM define o número (id) da classe
# nos rótulos: 0 = lata_ok, 1 = amassada, 2 = sem_rotulo, 3 = sem_cor.
# Não troque a ordem depois de anotar, senão os rótulos ficam errados.
CLASSES = ["lata_ok", "amassada", "sem_rotulo", "sem_cor"]

# Dataset no formato que o YOLO espera (gerado pelo 3_separar.py)
PASTA_YOLO = RAIZ / "dataset" / "yolo"
ARQUIVO_DATA = PASTA_YOLO / "data.yaml"  # diz ao YOLO onde estão as imagens e quais são as classes
FRACAO_VALIDACAO = 0.2  # 20% das imagens rotuladas vão para validação

# ---------------------------------------------------------------- TREINO
MODELO_BASE = str(RAIZ / "yolo26n.pt")  # modelo pré-treinado, versão nano: leve, roda bem na GTX 1650
EPOCAS = 30            # quantas vezes o treino passa por todas as imagens
TAMANHO_IMAGEM = 640   # as imagens são redimensionadas para 640 px no treino
LOTE_TREINO = 8        # imagens por passo; diminua se faltar memória na GPU
PASTA_TREINOS = RAIZ / "treinos"  # onde o Ultralytics grava gráficos e pesos de cada treino
# Melhor modelo do treino: é ele que a inspeção usa
MODELO_TREINADO = PASTA_TREINOS / "latas" / "weights" / "best.pt"

# Mesmo modelo convertido para NCNN (8_gerar_raspberry.py): mais leve e rápido na Raspberry Pi
MODELO_NCNN = PASTA_TREINOS / "latas" / "weights" / "best_ncnn_model"
# A inspeção usa o NCNN se ele existir; senão, o best.pt
MODELO_INSPECAO = MODELO_NCNN if MODELO_NCNN.exists() else MODELO_TREINADO

# Confiança mínima (0 a 1) para aceitar uma detecção do modelo
CONFIANCA = 0.5

# Cores das caixas em BGR (o OpenCV usa Azul, Verde, Vermelho), uma por classe,
# na mesma ordem de CLASSES: verde, vermelho, laranja, rosa
CORES = [(0, 200, 0), (60, 60, 255), (0, 160, 255), (255, 80, 255)]

# ---------------------------------------------------------------- INSPEÇÃO
# Vídeo usado quando nenhum outro é informado (6_inspecionar*.py e menu.py)
VIDEO_PADRAO = RAIZ / "esteirafull.mp4"
LINHA_X = 0.3  # posição da linha vertical: 0 = borda esquerda, 0.5 = meio, 1 = borda direita
PASTA_SAIDA = RAIZ / "saida"  # CSV, resumo e imagens das latas com defeito
# True quando não há monitor (Docker na Raspberry): o menu roda só a inspeção sem janela
SEM_TELA = os.environ.get("SEM_TELA") == "1"

# Pasta com a versão da Raspberry Pi (gerada pelo 8_gerar_raspberry.py; é o repositório Git)
PASTA_RASPBERRY = RAIZ / "raspberry"

# Saída digital que aciona o sopro da lata reprovada (GPIO da Raspberry Pi ou relé)
PINO_GPIO = 17      # numeração BCM
TEMPO_SOPRO = 0.2   # segundos que a saída fica ligada a cada lata reprovada
