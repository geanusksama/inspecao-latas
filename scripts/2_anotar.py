"""Etapa 2 - Anotação (rotulagem) das imagens.

O que faz: mostra cada imagem de dataset/imagens/ numa janela para você
           desenhar uma caixa em cada lata e dizer a classe dela.
Salva:     um .txt por imagem em dataset/rotulos/ (formato YOLO).
Também serve para corrigir os rótulos criados pelo 5_prerotular.py.
Próximo passo: 3_separar.py.

Controles:
    mouse         clique e arraste para desenhar uma caixa
    1 a 4         escolhe a classe da próxima caixa
    z             desfaz a última caixa
    d ou ESPAÇO   salva e vai para a próxima imagem
    a             salva e volta para a imagem anterior
    q ou ESC      salva e sai

Ao abrir de novo, continua da primeira imagem ainda sem rótulo.
"""
# cv2 = OpenCV. Aqui é usado para abrir a janela, ler mouse/teclado e desenhar
import cv2

# Vem do config.py:
#   CLASSES       -> nomes das 4 classes (lata_ok, amassada, sem_rotulo, sem_cor)
#   CORES         -> uma cor de caixa para cada classe
#   PASTA_IMAGENS -> imagens a anotar (criadas pelo 1_capturar.py)
#   PASTA_ROTULOS -> onde salvar os .txt (lidos depois pelo 3_separar.py)
from config import CLASSES, CORES, PASTA_IMAGENS, PASTA_ROTULOS

JANELA = "Anotar"
FONTE = cv2.FONT_HERSHEY_SIMPLEX
BRANCO = (255, 255, 255)

# Texto de ajuda mostrado na tela (sem acentos: o OpenCV não desenha acentos)
AJUDA = "arraste o mouse: nova caixa  |  z: desfaz  |  d ou ESPACO: proxima  |  a: anterior  |  q ou ESC: salva e sai"

# Tecla -> para onde ir: +1 próxima imagem, -1 anterior, None sair (27 = tecla ESC)
NAVEGACAO = {ord("d"): 1, ord(" "): 1, ord("a"): -1, ord("q"): None, 27: None}

# Dados da imagem atual, compartilhados com a função mouse():
#   caixas -> caixas desenhadas: (classe, x1, y1, x2, y2) em pixels
#   classe -> classe escolhida com as teclas 1 a 4 (guardada como 0 a 3)
#   inicio -> ponto onde o mouse foi apertado
#   atual  -> ponto atual do mouse enquanto arrasta
estado = {"caixas": [], "classe": 0, "inicio": None, "atual": None}


def mouse(evento, x, y, _flags, _param):
    """Desenha caixas com o mouse. O OpenCV chama esta função sozinho a cada movimento/clique.

    Apertou o botão -> guarda o ponto inicial
    Arrastou        -> guarda o ponto atual (para mostrar a caixa provisória)
    Soltou          -> cria a caixa com a classe escolhida
    """
    if evento == cv2.EVENT_LBUTTONDOWN:
        estado["inicio"] = (x, y)
    elif evento == cv2.EVENT_MOUSEMOVE and estado["inicio"]:
        estado["atual"] = (x, y)
    elif evento == cv2.EVENT_LBUTTONUP and estado["inicio"]:
        x1, y1 = estado["inicio"]
        if abs(x - x1) > 5 and abs(y - y1) > 5:  # ignora clique sem arrastar
            # min/max: funciona arrastando para qualquer direção
            estado["caixas"].append((estado["classe"], min(x1, x), min(y1, y), max(x1, x), max(y1, y)))
        estado["inicio"] = estado["atual"] = None


def carregar(arquivo, larg, alt):
    """Lê um .txt de rótulo e devolve as caixas em pixels.

    Recebe:  arquivo .txt, largura e altura da imagem
    Devolve: lista de (classe, x1, y1, x2, y2); vazia se o arquivo não existe
    Por quê: o .txt guarda centro/tamanho de 0 a 1 (formato YOLO); para desenhar
             na tela precisamos dos cantos da caixa em pixels.
    """
    if not arquivo.exists():
        return []
    caixas = []
    for linha in arquivo.read_text().splitlines():
        c, xc, yc, w, h = map(float, linha.split())
        # round() e não int(): int() corta 199.9998 para 199 e a caixa encolheria
        # 1 pixel cada vez que a imagem fosse aberta e salva de novo
        caixas.append((int(c),
                       round((xc - w / 2) * larg), round((yc - h / 2) * alt),
                       round((xc + w / 2) * larg), round((yc + h / 2) * alt)))
    return caixas


def salvar(arquivo, caixas, larg, alt):
    """Grava as caixas no .txt no formato YOLO (o caminho inverso de carregar).

    Recebe:  arquivo .txt, lista de caixas em pixels, largura e altura da imagem
    Se não houver caixas, apaga o .txt (a imagem fica fora do treino).
    """
    if not caixas:
        arquivo.unlink(missing_ok=True)
        return
    linhas = [f"{c} {(x1 + x2) / 2 / larg:.6f} {(y1 + y2) / 2 / alt:.6f} "
              f"{(x2 - x1) / larg:.6f} {(y2 - y1) / alt:.6f}"
              for c, x1, y1, x2, y2 in caixas]
    arquivo.write_text("\n".join(linhas))


def desenhar_painel(tela, titulo):
    """Desenha a faixa de ajuda no topo da tela.

    Linha 1: número da imagem + as 4 classes na cor delas (a escolhida fica entre [ ])
    Linha 2: os comandos de teclado e mouse
    """
    # Fundo escuro semitransparente: pinta uma cópia e mistura com a original
    fundo = tela.copy()
    cv2.rectangle(fundo, (0, 0), (tela.shape[1], 58), (30, 30, 30), -1)
    cv2.addWeighted(fundo, 0.75, tela, 0.25, 0, tela)

    # Linha 1: título e classes, um texto ao lado do outro
    textos = [titulo] + [f"[{i + 1}: {nome}]" if i == estado["classe"] else f"{i + 1}: {nome}"
                         for i, nome in enumerate(CLASSES)]
    cores = [BRANCO] + CORES
    x = 10
    for texto, cor in zip(textos, cores):
        cv2.putText(tela, texto, (x, 22), FONTE, 0.55, cor, 1, cv2.LINE_AA)
        x += cv2.getTextSize(texto, FONTE, 0.55, 1)[0][0] + 25  # avança para depois do texto

    # Linha 2: comandos
    cv2.putText(tela, AJUDA, (10, 48), FONTE, 0.5, BRANCO, 1, cv2.LINE_AA)


def desenhar(imagem, titulo):
    """Monta o que aparece na janela: imagem + caixas + painel de ajuda.

    Devolve uma cópia desenhada; a imagem original continua limpa.
    """
    tela = imagem.copy()
    for c, x1, y1, x2, y2 in estado["caixas"]:  # caixas já feitas
        cv2.rectangle(tela, (x1, y1), (x2, y2), CORES[c], 2)
        cv2.putText(tela, CLASSES[c], (x1, y1 - 5), FONTE, 0.5, CORES[c], 2)
    if estado["inicio"] and estado["atual"]:     # caixa sendo arrastada agora
        cv2.rectangle(tela, estado["inicio"], estado["atual"], CORES[estado["classe"]], 1)
    desenhar_painel(tela, titulo)
    return tela


def anotar_imagem(caminho, titulo):
    """Mostra UMA imagem e trata o teclado até você mudar de imagem.

    Recebe:  caminho da imagem e o título (ex.: "3/60")
    Devolve: +1 (próxima), -1 (anterior) ou None (sair)
    Ao sair desta imagem, salva os rótulos dela.
    """
    imagem = cv2.imread(str(caminho))
    alt, larg = imagem.shape[:2]
    rotulo = PASTA_ROTULOS / f"{caminho.stem}.txt"  # mesmo nome da imagem, com .txt
    estado["caixas"] = carregar(rotulo, larg, alt)  # mostra o que já foi marcado antes

    while True:
        cv2.imshow(JANELA, desenhar(imagem, f"Imagem {titulo}  caixas: {len(estado['caixas'])}"))
        tecla = cv2.waitKey(20) & 0xFF  # espera até 20 ms por uma tecla

        if cv2.getWindowProperty(JANELA, cv2.WND_PROP_VISIBLE) < 1:  # fechou a janela no X
            tecla = ord("q")
        if ord("1") <= tecla < ord("1") + len(CLASSES):  # 1 a 4: troca a classe
            estado["classe"] = tecla - ord("1")
        elif tecla == ord("z") and estado["caixas"]:      # z: desfaz
            estado["caixas"].pop()
        elif tecla in NAVEGACAO:                           # d, espaço, a, q, ESC
            salvar(rotulo, estado["caixas"], larg, alt)
            return NAVEGACAO[tecla]


def main():
    """Abre a janela e passa pelas imagens, uma por vez, começando pela primeira sem rótulo."""
    PASTA_ROTULOS.mkdir(parents=True, exist_ok=True)
    imagens = sorted(PASTA_IMAGENS.glob("*.jpg"))
    if not imagens:
        print(f"Nenhuma imagem em {PASTA_IMAGENS}. Rode antes o 1_capturar.py")
        return

    # Primeira imagem que ainda não tem .txt (para continuar de onde parou)
    pos = next((i for i, img in enumerate(imagens)
                if not (PASTA_ROTULOS / f"{img.stem}.txt").exists()), 0)

    cv2.namedWindow(JANELA)
    cv2.setMouseCallback(JANELA, mouse)  # avisa o OpenCV para chamar mouse() nesta janela

    while pos < len(imagens):
        passo = anotar_imagem(imagens[pos], f"{pos + 1}/{len(imagens)}")
        if passo is None:
            break
        pos = max(pos + passo, 0)  # não volta para antes da primeira imagem

    cv2.destroyAllWindows()
    feitas = len(list(PASTA_ROTULOS.glob("*.txt")))
    print(f"{feitas}/{len(imagens)} imagens rotuladas em {PASTA_ROTULOS}")


if __name__ == "__main__":
    main()
