"""Menu principal do sistema de inspeção (no terminal). É o que roda na Raspberry Pi.

    1 - Inspecionar   escolhe com janela (6_inspecionar.py) ou sem janela
                      (6_inspecionar_basico.py); para com q/ESC, Ctrl+C ou fim do vídeo
    2 - Relatório     roda o 7_ler_lotes.py por baixo e mostra o resumo:
                      conformes, não conformes, tipos de defeito e lotes afetados

Uso:
    python scripts/menu.py
"""
import csv         # lê o inspecao.csv e o lotes.csv para o relatório
import subprocess  # roda os outros scripts como programas separados
import sys         # sys.executable = o Python que está rodando este menu
from collections import Counter, defaultdict  # contadores do relatório
from pathlib import Path

# Vem do config.py: pasta saida/, se há monitor (SEM_TELA) e o vídeo padrão
from config import PASTA_SAIDA, SEM_TELA, VIDEO_PADRAO

PASTA_SCRIPTS = Path(__file__).parent  # pasta scripts/, onde estão os outros scripts
TRACO = "=" * 44


def rodar(script, *argumentos, silencioso=False):
    """Roda outro script do projeto e espera ele terminar.

    Recebe:  nome do script, argumentos (ex.: o vídeo) e silencioso=True para esconder a saída
    Ctrl+C: chega ao script filho, que para e grava o resumo. O menu ignora o
            Ctrl+C e continua esperando, para voltar ao menu em vez de fechar.
    """
    saida = subprocess.DEVNULL if silencioso else None
    processo = subprocess.Popen([sys.executable, str(PASTA_SCRIPTS / script), *argumentos],
                                stdout=saida, stderr=saida)
    while True:
        try:
            return processo.wait()
        except KeyboardInterrupt:
            continue


def inspecionar():
    """Opção 1: pergunta o modo (com/sem janela) e o vídeo, e roda a inspeção.

    Sem monitor (SEM_TELA, no Docker da Raspberry) não pergunta o modo: vai direto sem janela.
    """
    scripts = {"1": "6_inspecionar.py", "2": "6_inspecionar_basico.py"}
    if SEM_TELA:
        modo = "2"
    else:
        print("\n1 - Com janela (mostra a esteira)\n2 - Sem janela (só o terminal)\n0 - Voltar")
        modo = input("Modo: ").strip()
    if modo not in scripts:
        return
    video = input(f"Vídeo ou número da câmera (Enter = {VIDEO_PADRAO.name}): ").strip()
    rodar(scripts[modo], video or str(VIDEO_PADRAO))
    print("\nInspeção finalizada. Use a opção 2 para ver o relatório.\n")


def ler_csv(nome):
    """Lê um CSV da pasta saida/ e devolve as linhas (lista vazia se ainda não existir)."""
    caminho = PASTA_SAIDA / nome
    if not caminho.exists():
        return []
    with open(caminho, encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo, delimiter=";"))


def mostrar_lotes(defeitos):
    """Mostra os lotes que tiveram defeito e quantos de cada tipo.

    Recebe: as linhas do lotes.csv
    """
    por_lote = defaultdict(Counter)  # lote -> contagem por classe
    for lata in defeitos:
        por_lote[lata["lote"]][lata["classe"]] += 1
    print(f"\nLotes com defeito: {len(por_lote)}")
    for lote, contagem in sorted(por_lote.items(), key=lambda item: (len(item[0]), item[0])):
        detalhes = ", ".join(f"{classe}={n}" for classe, n in sorted(contagem.items()))
        print(f"  lote {lote:<4} {sum(contagem.values()):>4} defeitos  ({detalhes})")


def relatorio():
    """Opção 2: lê os lotes (7_ler_lotes.py, sem mostrar nada) e imprime o relatório."""
    latas = ler_csv("inspecao.csv")
    if not latas:
        print("\nNenhuma inspeção encontrada. Rode a inspeção primeiro.\n")
        return

    print("\nLendo os lotes das latas com defeito...")
    rodar("7_ler_lotes.py", silencioso=True)  # gera o lotes.csv

    total = len(latas)
    nao_conformes = sum(lata["situacao"] == "nao_conforme" for lata in latas)
    conformes = total - nao_conformes
    print(f"\n{TRACO}\n            RELATÓRIO DE INSPEÇÃO\n{TRACO}")
    print(f"Total de latas:  {total}")
    print(f"Conformes:       {conformes} ({conformes / total:.1%})")
    print(f"Não conformes:   {nao_conformes} ({nao_conformes / total:.1%})")
    print("\nPor tipo:")
    for classe, n in Counter(lata["classe"] for lata in latas).most_common():
        print(f"  {classe:<12} {n}")
    mostrar_lotes(ler_csv("lotes.csv"))
    print(f"{TRACO}\n")


# Opção digitada -> (texto no menu, função que roda)
OPCOES = {
    "1": ("Inspecionar", inspecionar),
    "2": ("Relatório", relatorio),
}


def main():
    """Mostra o menu e repete até escolher 0 (Sair)."""
    while True:
        print(f"{TRACO}\n         INSPEÇÃO DE LATAS - MENU\n{TRACO}")
        for chave, (nome, _) in OPCOES.items():
            print(f"{chave} - {nome}")
        print(f"0 - Sair\n{TRACO}")

        escolha = input("Escolha uma opção: ").strip()
        if escolha == "0":
            break
        if escolha in OPCOES:
            OPCOES[escolha][1]()  # chama a função da opção
        else:
            print("\nOpção inválida!\n")


if __name__ == "__main__":
    main()
