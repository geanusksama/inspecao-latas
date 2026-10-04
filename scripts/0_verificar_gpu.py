"""Etapa 0 - Verifica se o PyTorch enxerga a GPU (deve mostrar True e o nome da placa).

Rode antes de treinar: o 4_treinar.py usa a GPU (device=0). Se aparecer False,
o PyTorch instalado é a versão só para CPU e o treino não vai funcionar.
Não depende de nenhum outro arquivo do projeto.
"""
# torch = PyTorch, a biblioteca de redes neurais que o YOLO (Ultralytics) usa por baixo
import torch

print(torch.__version__)               # versão; deve terminar com +cuXXX (ex.: 2.14.1+cu130) para ter GPU
print(torch.cuda.is_available())       # True = a placa de vídeo NVIDIA está acessível
print(torch.cuda.get_device_name())    # nome da placa (ex.: NVIDIA GeForce GTX 1650)
