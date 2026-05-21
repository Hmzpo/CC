"""Classe Menu : interface utilisateur en mode texte (terminal)."""

from magasin_core import Magasin


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

        # Validation et enregistrement de la vente
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
