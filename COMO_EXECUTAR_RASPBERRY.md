# Como executar — passo a passo

Do GitHub até o sistema rodando, no PC ou na Raspberry Pi 5.
Repositório: https://github.com/geanusksama/inspecao-latas

---

## A) No PC, notebook, VM ou nuvem (demonstração)

Precisa do Docker (Docker Desktop no Windows).
```sh
git clone https://github.com/geanusksama/inspecao-latas.git
cd inspecao-latas
docker compose up -d --build
```
1. Abra **http://localhost:8000/docs** (Swagger).
2. Em **POST /detectar**: *Try it out* → escolha uma imagem de `dataset/imagens/` → *Execute* → veja o JSON.
3. Em **POST /detectar/imagem**: a mesma coisa → veja a imagem anotada.
4. Inspeção do vídeo da esteira pelo menu:
   ```sh
   docker compose exec inspecao python scripts/menu.py
   ```
   Opção 1 + Enter (vídeo de demonstração) e depois opção 2 (relatório).

Para parar: `docker compose down`.

---

## B) Na Raspberry Pi 5

1. Grave o **Raspberry Pi OS (64-bit)** no SSD com o *Raspberry Pi Imager* (ative SSH, usuário e Wi-Fi nas opções).
2. Entre na placa: `ssh usuario@nome-da-raspberry.local`.
3. Rode:
   ```sh
   sudo apt update && sudo apt install -y git
   git clone https://github.com/geanusksama/inspecao-latas.git
   cd inspecao-latas
   sh raspberry/iniciar.sh
   ```
4. No PC, abra `http://IP-da-raspberry:8000/docs`.
5. Menu de inspeção de vídeo: `cd raspberry && sudo docker compose exec inspecao python scripts/menu.py`

Detalhes, ligação do relé (GPIO 17) e problemas comuns: [`raspberry/LEIAME.md`](raspberry/LEIAME.md).

---

## C) Gerar a imagem para as duas arquiteturas (amd64 + arm64)

```sh
docker buildx build --platform linux/amd64,linux/arm64 -t inspecao-latas:1.0 --load .
```
