"""Classe Produit : représente un article du magasin."""


class Produit:
    """Représente un article du magasin."""

    def __init__(self, code: str, nom: str, prix: float, quantite: int):
        self.code = code.strip().upper()   # identifiant unique (ex : "P001")
        self.nom = nom.strip()
        self.prix = float(prix)
        self.quantite = int(quantite)

    # Sérialisation vers une ligne du fichier stock.txt
    def vers_ligne(self) -> str:
        return f"{self.code}|{self.nom}|{self.prix:.2f}|{self.quantite}\n"

    # Désérialisation depuis une ligne du fichier
    @classmethod
    def depuis_ligne(cls, ligne: str) -> "Produit":
        parties = ligne.strip().split("|")
        if len(parties) != 4:
            raise ValueError(f"Ligne produit invalide : {ligne}")
        code, nom, prix, quantite = parties
        return cls(code, nom, prix, quantite)

    def __str__(self) -> str:
        return f"[{self.code}] {self.nom:<25} {self.prix:>8.2f} €   stock: {self.quantite}"
