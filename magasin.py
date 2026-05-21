"""
Système de gestion de magasin - CC2 Programmation Python
Auteur : étudiant
Description : gestion du stock, des ventes et des clients réguliers
              avec persistance des données en fichiers textes.
"""

import os
from datetime import datetime


# ==============================================================
#  CLASSE PRODUIT
# ==============================================================

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


# ==============================================================
#  CLASSE CLIENT
# ==============================================================

class Client:
    """Représente un client du magasin."""

    def __init__(self, nom: str, adresse: str, dette: float = 0.0):
        self.nom = nom.strip()
        self.adresse = adresse.strip()
        # dette : montant total des achats non encore réglés (optionnel)
        self.dette = float(dette)
        # historique : liste de chaînes décrivant chaque achat
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


# ==============================================================
#  CLASSE MAGASIN
# ==============================================================

class Magasin:
    """
    Gère l'inventaire des produits, la liste des clients
    et l'enregistrement des ventes.
    """

    FICHIER_STOCK   = "stock.txt"
    FICHIER_CLIENTS = "clients.txt"
    FICHIER_VENTES  = "ventes.log"
    FICHIER_RAPPORT = "bilan_mensuel.txt"

    def __init__(self):
        # Dictionnaire code -> Produit pour un accès O(1) par code
        self.produits: dict[str, Produit] = {}
        # Dictionnaire nom -> Client (le nom est utilisé comme clé simple)
        self.clients: dict[str, Client] = {}

        self.charger_stock()
        self.charger_clients()

    # ----------------------------------------------------------
    #  Chargement / sauvegarde du stock
    # ----------------------------------------------------------

    def charger_stock(self) -> None:
        """Lit stock.txt et remplit le dictionnaire de produits."""
        if not os.path.exists(self.FICHIER_STOCK):
            return  # premier lancement : fichier inexistant, rien à charger
        with open(self.FICHIER_STOCK, "r", encoding="utf-8") as f:
            for ligne in f:
                ligne = ligne.strip()
                if not ligne or ligne.startswith("#"):
                    continue  # ignorer les lignes vides et les commentaires
                try:
                    p = Produit.depuis_ligne(ligne)
                    self.produits[p.code] = p
                except ValueError as e:
                    print(f"  [AVERTISSEMENT] {e}")

    def sauvegarder_stock(self) -> None:
        """Écrase stock.txt avec l'état actuel de l'inventaire."""
        with open(self.FICHIER_STOCK, "w", encoding="utf-8") as f:
            f.write("# FORMAT : CODE|NOM|PRIX|QUANTITE\n")
            for p in self.produits.values():
                f.write(p.vers_ligne())

    # ----------------------------------------------------------
    #  Chargement / sauvegarde des clients
    # ----------------------------------------------------------

    def charger_clients(self) -> None:
        """Lit clients.txt et remplit le dictionnaire de clients."""
        if not os.path.exists(self.FICHIER_CLIENTS):
            return
        with open(self.FICHIER_CLIENTS, "r", encoding="utf-8") as f:
            for ligne in f:
                ligne = ligne.strip()
                if not ligne or ligne.startswith("#"):
                    continue
                try:
                    c = Client.depuis_ligne(ligne)
                    self.clients[c.nom] = c
                except ValueError as e:
                    print(f"  [AVERTISSEMENT] {e}")

    def sauvegarder_clients(self) -> None:
        """Écrase clients.txt avec l'état actuel des clients."""
        with open(self.FICHIER_CLIENTS, "w", encoding="utf-8") as f:
            f.write("# FORMAT : NOM|ADRESSE|DETTE\n")
            for c in self.clients.values():
                f.write(c.vers_ligne())

    def sauvegarder_tout(self) -> None:
        """Point de sauvegarde global appelé à la fermeture."""
        self.sauvegarder_stock()
        self.sauvegarder_clients()
        print("  Données sauvegardées.")

    # ----------------------------------------------------------
    #  Gestion des produits
    # ----------------------------------------------------------

    def ajouter_produit(self, code: str, nom: str, prix: float, quantite: int) -> bool:
        """
        Ajoute un nouveau produit ou met à jour la quantité si le code existe.
        Retourne True si création, False si mise à jour.
        """
        code = code.strip().upper()
        if code in self.produits:
            # Code déjà existant : on met à jour la quantité
            self.produits[code].quantite += quantite
            return False
        self.produits[code] = Produit(code, nom, prix, quantite)
        return True

    def rechercher_produit(self, code: str) -> Produit | None:
        return self.produits.get(code.strip().upper())

    def produits_en_rupture(self) -> list[Produit]:
        """Retourne la liste des produits dont la quantité est <= 0."""
        return [p for p in self.produits.values() if p.quantite <= 0]

    # ----------------------------------------------------------
    #  Gestion des clients
    # ----------------------------------------------------------

    def ajouter_client(self, nom: str, adresse: str) -> bool:
        """Crée un client. Retourne False si le nom existe déjà."""
        if nom in self.clients:
            return False
        self.clients[nom] = Client(nom, adresse)
        return True

    # ----------------------------------------------------------
    #  Enregistrement d'une vente
    # ----------------------------------------------------------

    def enregistrer_vente(self, nom_client: str, panier: list[tuple[str, int]]) -> float:
        """
        Effectue une vente.

        panier : liste de tuples (code_produit, quantite_voulue)

        - Vérifie la disponibilité de chaque article.
        - Décrémente les stocks.
        - Calcule le montant total.
        - Écrit une ligne horodatée dans ventes.log.
        - Met à jour la dette du client.

        Retourne le montant total ou lève ValueError si problème.
        """
        if nom_client not in self.clients:
            raise ValueError(f"Client inconnu : {nom_client}")

        # Première passe : vérification des stocks (pas de modification encore)
        lignes_detail = []
        total = 0.0
        for code, qte in panier:
            produit = self.rechercher_produit(code)
            if produit is None:
                raise ValueError(f"Produit inconnu : {code}")
            if produit.quantite < qte:
                raise ValueError(
                    f"Stock insuffisant pour '{produit.nom}' "
                    f"(demandé: {qte}, disponible: {produit.quantite})"
                )
            sous_total = produit.prix * qte
            total += sous_total
            lignes_detail.append((produit, qte, sous_total))

        # Deuxième passe : mise à jour des stocks
        for produit, qte, _ in lignes_detail:
            produit.quantite -= qte

        # Mise à jour de la dette du client
        self.clients[nom_client].dette += total

        # Journalisation dans ventes.log
        horodatage = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        detail_str = "; ".join(
            f"{p.nom} x{q} ({st:.2f}€)" for p, q, st in lignes_detail
        )
        ligne_log = f"{horodatage} | {nom_client} | {detail_str} | TOTAL: {total:.2f}€\n"

        with open(self.FICHIER_VENTES, "a", encoding="utf-8") as f:
            f.write(ligne_log)

        # Mémorisation locale dans l'historique du client
        self.clients[nom_client].ajouter_achat(ligne_log.strip())

        return total

    # ----------------------------------------------------------
    #  Génération du rapport mensuel
    # ----------------------------------------------------------

    def generer_rapport(self) -> str:
        """
        Analyse ventes.log pour le mois courant et écrit bilan_mensuel.txt.
        Retourne le chemin du fichier créé.
        """
        mois_courant = datetime.now().strftime("%Y-%m")
        total_mois = 0.0
        nb_ventes = 0
        compteur_produits: dict[str, float] = {}  # nom_produit -> chiffre d'affaires
        compteur_clients: dict[str, float] = {}   # nom_client -> montant dépensé

        if os.path.exists(self.FICHIER_VENTES):
            with open(self.FICHIER_VENTES, "r", encoding="utf-8") as f:
                for ligne in f:
                    if not ligne.strip() or not ligne.startswith(mois_courant):
                        continue  # ignorer les ventes des autres mois
                    nb_ventes += 1
                    parties = ligne.split("|")
                    if len(parties) < 4:
                        continue
                    nom_client = parties[1].strip()
                    montant_str = parties[-1].replace("TOTAL:", "").replace("€", "").strip()
                    try:
                        montant = float(montant_str)
                    except ValueError:
                        continue
                    total_mois += montant
                    compteur_clients[nom_client] = compteur_clients.get(nom_client, 0) + montant

                    # Extraction des détails produit depuis la partie centrale
                    detail_partie = "|".join(parties[2:-1])
                    for item in detail_partie.split(";"):
                        item = item.strip()
                        if " x" in item and "(" in item:
                            nom_prod = item.split(" x")[0].strip()
                            montant_prod_str = item.split("(")[-1].replace("€)", "").strip()
                            try:
                                compteur_produits[nom_prod] = (
                                    compteur_produits.get(nom_prod, 0) + float(montant_prod_str)
                                )
                            except ValueError:
                                pass

        # Construction du rapport
        lignes = [
            f"=== BILAN MENSUEL - {mois_courant} ===\n",
            f"Généré le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n",
            f"Nombre de ventes       : {nb_ventes}\n",
            f"Chiffre d'affaires     : {total_mois:.2f} €\n\n",
            "--- Top produits (CA) ---\n",
        ]
        for nom, ca in sorted(compteur_produits.items(), key=lambda x: -x[1]):
            lignes.append(f"  {nom:<30} {ca:>10.2f} €\n")

        lignes.append("\n--- Top clients (montant dépensé ce mois) ---\n")
        for nom, montant in sorted(compteur_clients.items(), key=lambda x: -x[1]):
            lignes.append(f"  {nom:<30} {montant:>10.2f} €\n")

        lignes.append("\n--- État du stock ---\n")
        for p in sorted(self.produits.values(), key=lambda x: x.nom):
            statut = " [RUPTURE]" if p.quantite <= 0 else ""
            lignes.append(f"  {p}{statut}\n")

        with open(self.FICHIER_RAPPORT, "w", encoding="utf-8") as f:
            f.writelines(lignes)

        return self.FICHIER_RAPPORT


# ==============================================================
#  CLASSE MENU
# ==============================================================

class Menu:
    """Interface utilisateur en mode texte (terminal)."""

    def __init__(self):
        self.magasin = Magasin()

    # ----------------------------------------------------------
    #  Utilitaires d'affichage / saisie
    # ----------------------------------------------------------

    @staticmethod
    def titre(texte: str) -> None:
        print(f"\n{'='*50}")
        print(f"  {texte}")
        print(f"{'='*50}")

    @staticmethod
    def saisir_float(invite: str) -> float:
        """Boucle jusqu'à obtenir un nombre flottant valide."""
        while True:
            valeur = input(invite).strip()
            try:
                return float(valeur)
            except ValueError:
                print("  Veuillez entrer un nombre valide.")

    @staticmethod
    def saisir_int(invite: str) -> int:
        """Boucle jusqu'à obtenir un entier valide."""
        while True:
            valeur = input(invite).strip()
            try:
                return int(valeur)
            except ValueError:
                print("  Veuillez entrer un entier valide.")

    # ----------------------------------------------------------
    #  Option a : Enregistrer une vente
    # ----------------------------------------------------------

    def enregistrer_vente(self) -> None:
        self.titre("ENREGISTRER UNE VENTE")

        # Choix du client
        if not self.magasin.clients:
            print("  Aucun client enregistré. Ajoutez d'abord un client.")
            return

        print("  Clients disponibles :")
        for nom in self.magasin.clients:
            print(f"    - {nom}")
        nom_client = input("  Nom du client : ").strip()
        if nom_client not in self.magasin.clients:
            print("  Client inconnu.")
            return

        # Affichage des produits disponibles
        print("\n  Produits disponibles :")
        produits_dispos = [p for p in self.magasin.produits.values() if p.quantite > 0]
        if not produits_dispos:
            print("  Aucun produit en stock.")
            return
        for p in produits_dispos:
            print(f"    {p}")

        # Constitution du panier
        panier: list[tuple[str, int]] = []
        print("\n  (Appuyez sur Entrée sans saisir de code pour terminer)")
        while True:
            code = input("  Code produit : ").strip().upper()
            if not code:
                break
            if code not in self.magasin.produits:
                print("  Code inconnu, réessayez.")
                continue
            qte = self.saisir_int("  Quantité : ")
            if qte <= 0:
                print("  Quantité invalide.")
                continue
            panier.append((code, qte))

        if not panier:
            print("  Panier vide, vente annulée.")
            return

        # Validation de la vente
        try:
            total = self.magasin.enregistrer_vente(nom_client, panier)
            print(f"\n  Vente enregistrée. Total : {total:.2f} €")
            self.magasin.sauvegarder_tout()
        except ValueError as e:
            print(f"  Erreur : {e}")

    # ----------------------------------------------------------
    #  Option b : Ajouter un produit
    # ----------------------------------------------------------

    def ajouter_produit(self) -> None:
        self.titre("AJOUTER UN PRODUIT")
        code     = input("  Code      : ").strip()
        nom      = input("  Nom       : ").strip()
        prix     = self.saisir_float("  Prix (€)  : ")
        quantite = self.saisir_int("  Quantité  : ")

        if not code or not nom:
            print("  Code et nom obligatoires.")
            return

        cree = self.magasin.ajouter_produit(code, nom, prix, quantite)
        if cree:
            print(f"  Produit '{nom}' ajouté.")
        else:
            print(f"  Code existant : quantité mise à jour.")
        self.magasin.sauvegarder_stock()

    # ----------------------------------------------------------
    #  Option c : Ajouter un client
    # ----------------------------------------------------------

    def ajouter_client(self) -> None:
        self.titre("AJOUTER UN CLIENT")
        nom     = input("  Nom     : ").strip()
        adresse = input("  Adresse : ").strip()

        if not nom:
            print("  Le nom est obligatoire.")
            return

        cree = self.magasin.ajouter_client(nom, adresse)
        if cree:
            print(f"  Client '{nom}' ajouté.")
        else:
            print(f"  Un client avec ce nom existe déjà.")
        self.magasin.sauvegarder_clients()

    # ----------------------------------------------------------
    #  Option d : Voir le stock
    # ----------------------------------------------------------

    def voir_stock(self) -> None:
        self.titre("STOCK")
        choix = input("  (1) Tous les produits  (2) Recherche par code : ").strip()

        if choix == "2":
            code = input("  Code produit : ").strip()
            p = self.magasin.rechercher_produit(code)
            if p:
                print(f"  {p}")
            else:
                print(f"  Produit '{code}' introuvable.")
        else:
            if not self.magasin.produits:
                print("  Aucun produit en stock.")
                return
            for p in sorted(self.magasin.produits.values(), key=lambda x: x.code):
                print(f"  {p}")

    # ----------------------------------------------------------
    #  Option e : Afficher les clients
    # ----------------------------------------------------------

    def afficher_clients(self) -> None:
        self.titre("LISTE DES CLIENTS")
        if not self.magasin.clients:
            print("  Aucun client enregistré.")
            return
        for c in sorted(self.magasin.clients.values(), key=lambda x: x.nom):
            print(f"  {c}")

    # ----------------------------------------------------------
    #  Option f : Produits en rupture
    # ----------------------------------------------------------

    def produits_rupture(self) -> None:
        self.titre("PRODUITS EN RUPTURE DE STOCK")
        ruptures = self.magasin.produits_en_rupture()
        if not ruptures:
            print("  Aucun produit en rupture.")
        else:
            for p in ruptures:
                print(f"  {p}")

    # ----------------------------------------------------------
    #  Option g : Générer un rapport
    # ----------------------------------------------------------

    def generer_rapport(self) -> None:
        self.titre("GÉNÉRATION DU RAPPORT MENSUEL")
        chemin = self.magasin.generer_rapport()
        print(f"  Rapport généré : {chemin}")

    # ----------------------------------------------------------
    #  Boucle principale
    # ----------------------------------------------------------

    def afficher_menu(self) -> None:
        print("\n" + "-"*50)
        print("  MENU PRINCIPAL")
        print("  a) Enregistrer une vente")
        print("  b) Ajouter un produit")
        print("  c) Ajouter un client")
        print("  d) Voir le stock")
        print("  e) Afficher les clients")
        print("  f) Produits en rupture de stock")
        print("  g) Générer un rapport mensuel")
        print("  h) Quitter")
        print("-"*50)

    def lancer(self) -> None:
        """Boucle principale de l'application."""
        print("\n  === Bienvenue dans le système de gestion de magasin ===")

        actions = {
            "a": self.enregistrer_vente,
            "b": self.ajouter_produit,
            "c": self.ajouter_client,
            "d": self.voir_stock,
            "e": self.afficher_clients,
            "f": self.produits_rupture,
            "g": self.generer_rapport,
        }

        while True:
            self.afficher_menu()
            choix = input("  Votre choix : ").strip().lower()

            if choix == "h":
                self.magasin.sauvegarder_tout()
                print("  Au revoir !")
                break
            elif choix in actions:
                actions[choix]()
            else:
                print("  Choix invalide, veuillez réessayer.")


# ==============================================================
#  POINT D'ENTRÉE
# ==============================================================

if __name__ == "__main__":
    menu = Menu()
    menu.lancer()
