"""Classe Client : représente un client du magasin."""


class Client:
    """Représente un client du magasin."""

    def __init__(self, nom: str, adresse: str, dette: float = 0.0):
        self.nom = nom.strip()
        self.adresse = adresse.strip()
        # dette : montant total des achats non encore réglés
        self.dette = float(dette)
        # historique : liste de chaînes décrivant chaque achat (en mémoire)
        self.historique: list[str] = []

    def ajouter_achat(self, description: str) -> None:
        """Ajoute une entrée à l'historique local (non persisté séparément)."""
        self.historique.append(description)

    # Sérialisation vers une ligne de clients.txt
    def vers_ligne(self) -> str:
        return f"{self.nom}|{self.adresse}|{self.dette:.2f}\n"

    # Désérialisation depuis une ligne de clients.txt
    @classmethod
    def depuis_ligne(cls, ligne: str) -> "Client":
        parties = ligne.strip().split("|")
        if len(parties) < 2:
            raise ValueError(f"Ligne client invalide : {ligne}")
        nom = parties[0]
        adresse = parties[1]
        dette = float(parties[2]) if len(parties) >= 3 else 0.0
        return cls(nom, adresse, dette)

    def __str__(self) -> str:
        return f"{self.nom:<30} {self.adresse:<40} dette: {self.dette:.2f} €"
