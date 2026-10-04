"""Saída digital que "sopra" a lata reprovada para fora da linha.

O que faz: quando a inspeção encontra uma lata com defeito, liga um pino de
           GPIO (ou um relé ligado a ele) por TEMPO_SOPRO segundos, que aciona o soprador.
           - Na Raspberry Pi: liga o pino de verdade (biblioteca gpiozero).
           - No PC (sem GPIO): só simula e mostra a mensagem no terminal.
Quem usa: 6_inspecionar.py e 6_inspecionar_basico.py.
"""
# Vem do config.py: número do pino e quanto tempo o sopro fica ligado
from config import PINO_GPIO, TEMPO_SOPRO

# gpiozero só existe na Raspberry Pi. Se não estiver instalada (PC, Docker),
# OutputDevice fica None e a saída funciona em modo simulado.
try:
    from gpiozero import OutputDevice
except ImportError:
    OutputDevice = None


class SaidaDigital:
    """Representa o soprador. Tem uma única ação: soprar()."""

    def __init__(self):
        """Tenta abrir o pino do GPIO; se não der, fica em modo simulado."""
        self.pino = None
        if OutputDevice:
            try:
                self.pino = OutputDevice(PINO_GPIO)
            except Exception:  # gpiozero instalado, mas a máquina não tem GPIO
                self.pino = None
        print(f"Saida digital: {'GPIO ' + str(PINO_GPIO) if self.pino else 'simulada (sem GPIO)'}")

    def soprar(self, numero):
        """Dá um pulso no pino (liga e desliga sozinho) e avisa no terminal.

        Recebe: o número da lata (só para a mensagem)
        background=True: o pulso acontece em paralelo, sem travar a inspeção.
        """
        if self.pino:
            self.pino.blink(on_time=TEMPO_SOPRO, off_time=0, n=1, background=True)
        print(f"Lata {numero}: SOPROU via GPIO/Rele")
