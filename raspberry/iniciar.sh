#!/bin/sh
# Inicia o sistema de inspeção na Raspberry Pi 5.
# 1ª vez: instala o Docker e monta a imagem (alguns minutos). Depois: sobe em segundos.
# A API fica rodando em segundo plano e volta sozinha quando a Raspberry reinicia.
set -e                                # para no primeiro erro
cd "$(dirname "$0")"                  # roda a partir da pasta raspberry/

# 1. Instala o Docker, se ainda não tiver
if ! command -v docker >/dev/null 2>&1; then
    echo "Instalando o Docker (só na primeira vez)..."
    curl -fsSL https://get.docker.com | sudo sh
fi

# 2. Pastas que ficam fora do container
mkdir -p ../saida ../videos

# 3. Monta a imagem (só refaz o que mudou) e sobe a API em segundo plano
sudo docker compose up -d --build

IP=$(hostname -I | awk '{print $1}')
echo ""
echo "API no ar:  http://$IP:8000/docs"
echo "Menu de inspeção de vídeo:  cd raspberry && sudo docker compose exec inspecao python scripts/menu.py"
