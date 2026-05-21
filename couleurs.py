"""Codes ANSI pour l'affichage coloré en terminal."""

ROUGE   = "\033[91m"
VERT    = "\033[92m"
JAUNE   = "\033[93m"
BLEU    = "\033[94m"
MAGENTA = "\033[95m"
CYAN    = "\033[96m"
GRAS    = "\033[1m"
RESET   = "\033[0m"


def rouge(texte: str) -> str:   return f"{ROUGE}{texte}{RESET}"
def vert(texte: str) -> str:    return f"{VERT}{texte}{RESET}"
def jaune(texte: str) -> str:   return f"{JAUNE}{texte}{RESET}"
def bleu(texte: str) -> str:    return f"{BLEU}{texte}{RESET}"
def magenta(texte: str) -> str: return f"{MAGENTA}{texte}{RESET}"
def cyan(texte: str) -> str:    return f"{CYAN}{texte}{RESET}"
def gras(texte: str) -> str:    return f"{GRAS}{texte}{RESET}"
