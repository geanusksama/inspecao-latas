# Inspeção de Latas — Raspberry Pi 5

Esta pasta tem só o que é específico da placa. A imagem Docker é a mesma do PC (`Dockerfile` na raiz),
montada para `arm64`. O sistema sobe sozinho quando a Raspberry liga (`restart: always`).

**Requisitos:** Raspberry Pi 5 (2 GB de RAM ou mais), SSD ou cartão de 32 GB,
**Raspberry Pi OS 64-bit** (Lite serve) e internet na primeira instalação.

---

## Instalação (uma vez)

1. Grave o **Raspberry Pi OS (64-bit)** com o *Raspberry Pi Imager*. Nas opções, ative o **SSH**,
   defina usuário e senha e configure o Wi-Fi.
2. Entre na Raspberry (monitor e teclado, ou `ssh usuario@nome-da-raspberry.local`).
3. Baixe o projeto e inicie:
```sh
sudo apt update && sudo apt install -y git
git clone https://github.com/geanusksama/inspecao-latas.git
cd inspecao-latas
sh raspberry/iniciar.sh
```
Na primeira vez ele instala o Docker e monta a imagem (alguns minutos, cerca de 1 GB de download).
No fim, mostra o endereço da API.

---

## Uso

| O quê | Como |
| --- | --- |
| **API (Swagger)** | No navegador do PC: `http://IP-da-raspberry:8000/docs` |
| **Detectar numa imagem** | `curl -F "arquivo=@lata.jpg" http://IP-da-raspberry:8000/detectar` |
| **Inspeção de vídeo / câmera (menu)** | `cd raspberry && sudo docker compose exec inspecao python scripts/menu.py` |
| **Ver os logs** | `cd raspberry && sudo docker compose logs -f` |
| **Parar** | `cd raspberry && sudo docker compose down` |

No menu: **1** inspeciona (Enter = vídeo de demonstração; `videos/arquivo.mp4` = vídeo seu; `0` = câmera USB;
**Ctrl+C** para parar) e **2** mostra o relatório de conformidade e os lotes afetados.
Vídeos seus vão na pasta `videos/` e os resultados ficam em `saida/` (na raiz do projeto).

---

## Ligação do soprador (GPIO)

| Raspberry Pi | Módulo relé |
| --- | --- |
| GPIO 17 (pino físico 11) | IN (sinal) |
| GND (pino físico 6) | GND |
| 5V (pino físico 2) | VCC |

Cada lata reprovada liga a saída por 0,2 s (`TEMPO_SOPRO` em `scripts/config.py`).

---

## Validar na placa

1. `curl http://localhost:8000/saude` deve responder `"formato": "ncnn"`.
2. `cd raspberry && sudo docker compose exec inspecao python scripts/9_benchmark.py`: a mediana do NCNN deve ficar perto de 67 ms (referência oficial da Ultralytics para a Pi 5).
3. Menu → opção 1 com o vídeo de demonstração: resumo com **160 latas (96 conformes / 64 não conformes)**.
4. LED ou relé no GPIO 17: um pulso por lata reprovada.
5. Temperatura em uso contínuo: `vcgencmd measure_temp` (use cooler ativo).

---

## Atualizar
```sh
cd inspecao-latas && git pull && sh raspberry/iniciar.sh
```

## Problemas comuns

| Sintoma | O que fazer |
| --- | --- |
| `exec format error` | O sistema é de 32 bits: grave o Raspberry Pi OS **64-bit**. |
| Montagem para por falta de memória | Aumente a swap (no Raspberry Pi OS Bookworm: `CONF_SWAPSIZE=1024` em `/etc/dphys-swapfile` e `sudo systemctl restart dphys-swapfile`). |
| Porta 8000 ocupada | Troque `"8000:8000"` por `"8080:8000"` em `raspberry/docker-compose.yml`. |
| Câmera não abre (`0`) | Confira com `ls /dev/video*`. |
| Disco cheio | Apague resultados antigos em `saida/` e rode `sudo docker system prune`. |
