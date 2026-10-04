# Imagem da inspeção de latas: API HTTP + inspeção de vídeo, modelo NCNN, só CPU.
# Multi-arquitetura: a mesma receita gera linux/amd64 (PC) e linux/arm64 (Raspberry Pi 5):
#   docker buildx build --platform linux/amd64,linux/arm64 -t inspecao-latas .
# Só a INFERÊNCIA vai aqui: treino, dataset e anotação ficam no PC (ver .dockerignore).

# Python 3.12 numa base Debian enxuta (existe para amd64 e arm64)
FROM python:3.12-slim-bookworm

# PYTHONUNBUFFERED: logs aparecem na hora | PIP_NO_CACHE_DIR: imagem menor
# SEM_TELA: não há monitor no container (o menu vai direto para a inspeção sem janela)
# YOLO_CONFIG_DIR: pasta gravável para as configurações do Ultralytics
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SEM_TELA=1 \
    YOLO_CONFIG_DIR=/tmp/ultralytics

# Bibliotecas do sistema que o OpenCV precisa
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# PyTorch só para CPU: a Raspberry não tem GPU NVIDIA, e essa versão é bem menor
RUN pip install torch==2.14.1 torchvision==0.29.1 --index-url https://download.pytorch.org/whl/cpu

# Resto das bibliotecas + download dos modelos do OCR já na montagem (a placa pode estar sem internet)
COPY requirements-docker.txt .
RUN pip install -r requirements-docker.txt \
    && python -c "from rapidocr import RapidOCR; RapidOCR()"

# Código, modelo NCNN e vídeo de demonstração por último: mudar o código não reinstala nada
COPY scripts/ scripts/
COPY treinos/latas/weights/best_ncnn_model/ treinos/latas/weights/best_ncnn_model/
COPY esteirafull.mp4 .

EXPOSE 8000

# O Docker considera o container saudável quando a API responde
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/saude')"

# Sobe a API. Para a inspeção de vídeo pelo menu: docker compose exec inspecao python scripts/menu.py
CMD ["uvicorn", "api:app", "--app-dir", "scripts", "--host", "0.0.0.0", "--port", "8000"]
