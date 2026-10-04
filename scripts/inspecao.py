"""Peças da inspeção usadas pelos dois scripts: 6_inspecionar.py (com tela)
e 6_inspecionar_basico.py (sem tela). Ficam aqui para não repetir código.

    detectar()  acha as latas num quadro do vídeo, cada uma com um número (id)
    Rastreio    segue cada lata e avisa quando ela cruza a linha vertical
    Registro    conta as latas e grava CSV, resumo e imagens dos defeitos

Arquivos gerados em saida/ (pelo Registro):
    inspecao.csv        uma linha por lata: hora, número, classe, situação, imagens
    resumo.txt          quantidade por classe
    defeitos/           quadro inteiro com a lata defeituosa marcada (rastreabilidade)
    recortes/<classe>/  só a lata defeituosa, sem desenho (o 7_ler_lotes.py lê o lote daqui)
"""
import csv                                # grava o inspecao.csv
from collections import Counter, defaultdict  # Counter = contador; defaultdict = dicionário com valor inicial
from datetime import datetime             # data e hora de cada lata no CSV

import cv2  # OpenCV: salva as imagens e desenha a marcação do defeito

# Vem do config.py:
#   CLASSES     -> nomes das classes (o modelo devolve o número; aqui viramos nome)
#   CONFIANCA   -> confiança mínima para aceitar uma detecção
#   CORES       -> cor da marcação de cada classe
#   PASTA_SAIDA -> pasta saida/
from config import CLASSES, CONFIANCA, CORES, PASTA_SAIDA

CLASSE_OK = 0  # número da classe lata_ok; qualquer outra classe é defeito
FONTE = cv2.FONT_HERSHEY_SIMPLEX


def detectar(modelo, quadro):
    """Acha as latas de um quadro do vídeo.

    Recebe:  o modelo YOLO e o quadro (imagem)
    Devolve: lista de (id, classe, caixa), onde caixa = (x1, y1, x2, y2) em pixels.
             O id é o "número" da lata: continua o mesmo nos quadros seguintes.
    Detalhes:
        track()           detecta E segue as latas entre quadros (dá o id)
        bytetrack.yaml    rastreador leve (o padrão gasta ~20 ms a mais por quadro)
        agnostic_nms=True se a mesma lata vier com 2 caixas de classes diferentes,
                          fica só a mais forte (senão ela seria contada 2 vezes)
    """
    caixas = modelo.track(quadro, persist=True, conf=CONFIANCA, agnostic_nms=True,
                          verbose=False, tracker="bytetrack.yaml")[0].boxes
    if caixas.id is None:  # nenhuma lata no quadro
        return []
    return list(zip(caixas.id.int().tolist(), caixas.cls.int().tolist(), caixas.xyxy.int().tolist()))


def cruzou(x_antes, x_agora, linha):
    """Diz se a lata passou pela linha entre o quadro anterior e o atual.

    Recebe:  x do centro da lata antes e agora, e o x da linha
    Devolve: True se um está de um lado da linha e o outro do outro lado
    """
    return x_antes < linha <= x_agora or x_agora <= linha < x_antes


class Rastreio:
    """Segue cada lata até ela cruzar a linha e decide a classe final dela.

    Por que votar: em um quadro o modelo pode errar (ex.: ver amassada como ok).
    Então cada quadro é um "voto" e, ao cruzar a linha, vence a classe mais vista.
    """

    def __init__(self):
        """Cria as anotações vazias. Tudo é guardado pelo id da lata."""
        self.ultimo_x = {}                 # id -> posição x do centro no quadro anterior
        self.votos = defaultdict(Counter)  # id -> quantas vezes cada classe foi vista
        self.avaliadas = {}                # id -> classe final (latas que já cruzaram)

    def atualizar(self, deteccoes, linha):
        """Processa as latas de um quadro.

        Recebe:  as detecções do quadro (saída de detectar()) e o x da linha
        Devolve: as latas que cruzaram a linha neste quadro: lista de (caixa, classe final)
        Cada lata é devolvida uma única vez (quem já foi avaliada é pulada).
        """
        cruzaram = []
        for id_lata, classe, caixa in deteccoes:
            if id_lata in self.avaliadas:  # já foi contada
                continue
            centro = (caixa[0] + caixa[2]) // 2
            self.votos[id_lata][classe] += 1  # mais um voto para a classe vista agora
            if id_lata in self.ultimo_x and cruzou(self.ultimo_x[id_lata], centro, linha):
                self.avaliadas[id_lata] = self.votos[id_lata].most_common(1)[0][0]  # classe mais votada
                cruzaram.append((caixa, self.avaliadas[id_lata]))
            self.ultimo_x[id_lata] = centro

        self.esquecer_saidas({d[0] for d in deteccoes})
        return cruzaram

    def esquecer_saidas(self, ids_na_tela):
        """Apaga as anotações das latas já avaliadas que saíram da imagem.

        Sem isso, numa linha rodando o dia todo, a memória cresceria sem parar.
        """
        for id_lata in [i for i in self.avaliadas if i not in ids_na_tela]:
            for dados in (self.ultimo_x, self.votos, self.avaliadas):
                dados.pop(id_lata, None)


class Registro:
    """Conta as latas e grava os arquivos da pasta saida/ (ver lista no topo)."""

    def __init__(self):
        """Cria as pastas de saída e abre o inspecao.csv com o cabeçalho."""
        (PASTA_SAIDA / "defeitos").mkdir(parents=True, exist_ok=True)
        for nome in CLASSES[1:]:  # uma pasta de recortes por tipo de defeito (lata_ok não é salva)
            (PASTA_SAIDA / "recortes" / nome).mkdir(parents=True, exist_ok=True)
        self.por_classe = Counter()  # classe -> quantidade de latas
        self.arquivo = open(PASTA_SAIDA / "inspecao.csv", "w", newline="", encoding="utf-8")
        self.csv = csv.writer(self.arquivo, delimiter=";")
        self.csv.writerow(["data_hora", "numero", "classe", "situacao", "imagem", "recorte"])

    def adicionar(self, quadro, caixa, classe):
        """Registra uma lata que cruzou a linha.

        Recebe:  o quadro, a caixa da lata e a classe final
        Faz:     conta a lata; se tiver defeito, salva o quadro marcado em defeitos/
                 e o recorte da lata em recortes/<classe>/; escreve a linha no CSV
        Devolve: o número da lata (1, 2, 3...), usado na mensagem do sopro
        """
        self.por_classe[classe] += 1
        numero = sum(self.por_classe.values())
        defeito = classe != CLASSE_OK
        imagem = recorte = ""
        if defeito:
            imagem = f"defeitos/{numero:05d}_{CLASSES[classe]}.jpg"
            recorte = f"recortes/{CLASSES[classe]}/{numero:05d}.jpg"
            x1, y1, x2, y2 = caixa
            cv2.imwrite(str(PASTA_SAIDA / imagem), anotar_defeito(quadro, caixa, classe))
            cv2.imwrite(str(PASTA_SAIDA / recorte), quadro[max(y1, 0):y2, max(x1, 0):x2])
        self.csv.writerow([datetime.now().isoformat(timespec="seconds"), numero, CLASSES[classe],
                           "nao_conforme" if defeito else "conforme", imagem, recorte])
        self.arquivo.flush()  # grava na hora, para não perder nada se o programa parar
        print(f"Lata {numero}: {CLASSES[classe]}")
        return numero

    def fechar(self):
        """Fecha o CSV, grava o resumo.txt e mostra o resumo no terminal."""
        self.arquivo.close()
        total = sum(self.por_classe.values())
        linhas = [f"Total de latas: {total}",
                  f"Conformes: {self.por_classe[CLASSE_OK]}",
                  f"Nao conformes: {total - self.por_classe[CLASSE_OK]}", "", "Por classe:"]
        linhas += [f"  {nome}: {self.por_classe[i]}" for i, nome in enumerate(CLASSES)]
        (PASTA_SAIDA / "resumo.txt").write_text("\n".join(linhas), encoding="utf-8")
        print("\n".join(linhas))


def anotar_defeito(quadro, caixa, classe):
    """Devolve uma cópia do quadro com a lata defeituosa marcada (caixa + nome do defeito).

    É a imagem de rastreabilidade salva em saida/defeitos/.
    """
    imagem = quadro.copy()
    x1, y1, x2, y2 = caixa
    cv2.rectangle(imagem, (x1, y1), (x2, y2), CORES[classe], 3)
    cv2.putText(imagem, CLASSES[classe], (x1, y1 - 10), FONTE, 0.7, CORES[classe], 2)
    return imagem
