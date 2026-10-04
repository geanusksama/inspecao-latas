# Guia de Teste — Inspeção de Latas com Edge AI

Este guia leva você, passo a passo, a testar o sistema **no seu computador** (parte A) e **na Raspberry Pi 5**
(parte B), baixando tudo do GitHub. Não é preciso saber programar: basta copiar e colar os comandos.

**Repositório:** https://github.com/geanusksama/inspecao-latas

| O que o sistema faz | Como você vai ver |
| --- | --- |
| Recebe uma foto da esteira e diz quais latas estão boas ou com defeito | Numa página do navegador (Swagger) |
| Devolve a mesma foto com as latas marcadas | Imagem com caixas coloridas |
| Inspeciona um vídeo inteiro da esteira e conta as latas | Num menu no terminal |
| Mostra o relatório: conformes, não conformes e lotes com defeito | No mesmo menu |

---

## Parte A — Testar no computador (Windows)

### A1. Instalar o Docker Desktop (uma vez)
1. Baixe em https://docs.docker.com/desktop/setup/install/windows-install/ e instale com as opções padrão.
2. Se pedir para reiniciar o computador, reinicie.
3. Abra o **Docker Desktop** e espere aparecer **Engine running** no canto de baixo. Deixe-o aberto.

### A2. Baixar o projeto
Escolha **um** dos jeitos:

**Sem instalar nada:** abra https://github.com/geanusksama/inspecao-latas, clique no botão verde **Code** →
**Download ZIP** e extraia o arquivo (por exemplo em `C:\inspecao-latas`).

**Com o Git** (se já tiver instalado), no PowerShell:
```powershell
git clone https://github.com/geanusksama/inspecao-latas.git C:\inspecao-latas
```

### A3. Abrir o terminal na pasta do projeto
Abra a pasta extraída no Explorador de Arquivos (a que tem o arquivo `Dockerfile`), clique com o botão direito
num espaço vazio e escolha **Abrir no Terminal**. Ou abra o **PowerShell** e digite:
```powershell
cd C:\inspecao-latas
```

### A4. Ligar o sistema
```powershell
docker compose up -d --build
```
- **Na primeira vez** ele baixa e monta tudo: de 5 a 20 minutos, dependendo da internet (cerca de 1 GB).
- Nas próximas vezes, leva segundos.
- Quando terminar, aparece `Container ... Started`.

### A5. Testar pelo navegador
1. Abra **http://localhost:8000/docs**
2. Clique em **POST /detectar** → **Try it out** → **Escolher arquivo** → escolha uma imagem da pasta
   `dataset\imagens` do projeto → **Execute**.
3. Desça até **Response body**: aparece a lista de latas, cada uma com `classe`, `confianca` e `conforme`,
   e o `resumo` com o total de conformes e não conformes.
4. Faça o mesmo em **POST /detectar/imagem**: a resposta é a foto com as latas marcadas.

Cores: verde = lata boa · vermelho = amassada · laranja = sem rótulo · rosa = sem cor.

### A6. Inspecionar o vídeo da esteira
```powershell
docker compose exec inspecao python scripts/menu.py
```
1. Digite **1** e aperte **Enter** duas vezes: inspeciona o vídeo de demonstração (84 segundos de esteira).
   No computador leva cerca de 6 minutos; cada lata aparece numa linha, e as reprovadas mostram `SOPROU`.
2. No fim, o resumo deve mostrar **Total de latas: 160 · Conformes: 96 · Nao conformes: 64**.
3. Digite **2**: relatório com os lotes com defeito (**lote 7: 24** e **lote 8: 40**).
4. Digite **0** para sair.

Os resultados ficam na pasta **`saida`** do projeto: `inspecao.csv` (abre no Excel), `lotes.csv`,
`defeitos\` (fotos das latas reprovadas) e `recortes\`.

### A7. Desligar
```powershell
docker compose down
```

### Problemas comuns no computador
| Mensagem ou sintoma | O que fazer |
| --- | --- |
| `docker` não é reconhecido | O Docker Desktop não está instalado ou não está aberto (passo A1). |
| `Cannot connect to the Docker daemon` | Abra o Docker Desktop e espere **Engine running**. |
| `port is already allocated` | Outro programa usa a porta 8000. No `docker-compose.yml`, troque `"8000:8000"` por `"8080:8000"` e use http://localhost:8080/docs. |
| A página não abre logo após o `up` | Espere 1 minuto: o sistema ainda está carregando o modelo. |
| `no configuration file provided` | O terminal não está na pasta do projeto (passo A3). |

---

## Parte B — Testar na Raspberry Pi 5

**Você vai precisar de:** Raspberry Pi 5 (2 GB ou mais), SSD ou cartão de 32 GB, fonte oficial, internet
e o computador para preparar a placa.

### B1. Gravar o sistema (no computador)
1. Instale o **Raspberry Pi Imager**: https://www.raspberrypi.com/software/
2. **Dispositivo:** Raspberry Pi 5 · **Sistema:** **Raspberry Pi OS (64-bit)** (a versão *Lite* basta) ·
   **Armazenamento:** o SSD ou cartão. O sistema **precisa ser 64 bits**.
3. Quando perguntar se quer personalizar, clique em **Editar configurações**:
    - Nome do computador: `inspecao`
    - Usuário e senha: por exemplo `pi` e uma senha sua
    - Wi-Fi: nome e senha da rede (pule se usar cabo)
    - Aba **Serviços**: marque **Ativar SSH** com senha
4. Grave, coloque o SSD na Raspberry e ligue. Espere uns 2 minutos.

### B2. Entrar na Raspberry pelo computador
No PowerShell do computador:
```powershell
ssh pi@inspecao.local
```
Responda `yes` e digite a senha. (Se `inspecao.local` não for encontrado, use o IP da placa, que aparece no
roteador: `ssh pi@192.168.x.x`.) Também dá para usar monitor e teclado direto na Raspberry.

### B3. Baixar e ligar o sistema (na Raspberry)
```sh
sudo apt update && sudo apt install -y git
git clone https://github.com/geanusksama/inspecao-latas.git
cd inspecao-latas
sh raspberry/iniciar.sh
```
Na primeira vez ele instala o Docker e monta o sistema (vários minutos). No fim mostra:
`API no ar: http://192.168.x.x:8000/docs`. Daí em diante, o sistema **liga sozinho** sempre que a Raspberry ligar.

### B4. Testar
**Pela API:** no navegador do **computador**, abra o endereço mostrado (`http://IP-da-raspberry:8000/docs`) e
repita o teste do passo A5.

**Menu de inspeção do vídeo**, na Raspberry (depois: opção 1 + Enter e opção 2, como no passo A6):
```sh
cd ~/inspecao-latas/raspberry
sudo docker compose exec inspecao python scripts/menu.py
```

**Copiar os resultados para o computador**, no PowerShell do computador:
```powershell
scp -r pi@inspecao.local:~/inspecao-latas/saida .
```

### B5. Soprador (opcional)
Ligue um módulo relé (ou um LED com resistor) no **GPIO 17 (pino físico 11)** e no **GND (pino 6)**.
Cada lata reprovada dá um pulso de 0,2 s. Sem nada ligado, o sistema funciona igual.

### B6. Conferir o primeiro teste na placa
O sistema foi testado no computador e numa emulação do processador da Raspberry, mas **ainda não numa
Raspberry Pi 5 de verdade**. No primeiro uso, confira:
- [ ] `http://IP:8000/saude` responde com `"formato": "ncnn"`
- [ ] A opção 1 do menu termina com **160 latas (96 conformes / 64 não conformes)**
- [ ] A opção 2 mostra **lote 7: 24** e **lote 8: 40**
- [ ] Benchmark na placa, `sudo docker compose exec inspecao python scripts/9_benchmark.py`: referência de ~67 ms por imagem no NCNN

Se algo falhar, copie a mensagem de erro inteira que aparecer na tela.

### Problemas comuns na Raspberry
| Sintoma | O que fazer |
| --- | --- |
| `exec format error` | O sistema gravado é de 32 bits: grave o **Raspberry Pi OS (64-bit)**. |
| A montagem para por falta de memória | Aumente a memória virtual (swap). No Raspberry Pi OS Bookworm: `CONF_SWAPSIZE=1024` em `/etc/dphys-swapfile` e `sudo systemctl restart dphys-swapfile`. |
| `inspecao.local` não encontrado | Use o IP da Raspberry (veja no roteador). |
| Atualizar para a versão mais nova | `cd ~/inspecao-latas && git pull && sh raspberry/iniciar.sh` |
