"""Classe Menu : interface utilisateur en mode texte avec affichage coloré."""

import couleurs as c
from magasin_core import Magasin
from produit import Produit


class Menu:
    """Interface utilisateur en mode texte (terminal)."""

    def __init__(self):
        self.magasin = Magasin()

    # ----------------------------------------------------------
    #  Utilitaires d'affichage / saisie
    # ----------------------------------------------------------

    @staticmethod
    def titre(texte: str) -> None:
        print(f"\n{c.cyan('='*52)}")
        print(f"  {c.gras(texte)}")
        print(c.cyan("="*52))

    @staticmethod
    def saisir_float(invite: str) -> float:
        """Boucle jusqu'à obtenir un nombre flottant valide."""
        while True:
            valeur = input(invite).strip()
            try:
                return float(valeur)
            except ValueError:
                print(c.rouge("  Veuillez entrer un nombre valide."))

    @staticmethod
    def saisir_int(invite: str) -> int:
        """Boucle jusqu'à obtenir un entier valide."""
        while True:
            valeur = input(invite).strip()
            try:
                return int(valeur)
            except ValueError:
                print(c.rouge("  Veuillez entrer un entier valide."))

    @staticmethod
    def confirmer(invite: str) -> bool:
        """Demande une confirmation o/n. Retourne True si 'o'."""
        rep = input(invite + " (o/n) : ").strip().lower()
        return rep == "o"

    # ----------------------------------------------------------
    #  Affichage coloré d'un produit selon l'état du stock
    # ----------------------------------------------------------

    def afficher_produit(self, p: Produit) -> None:
        """
        Rouge  = rupture (quantite <= 0)
        Jaune  = stock faible (0 < quantite <= SEUIL)
        Vert   = stock OK
        """
        if p.quantite <= 0:
            print(c.rouge(f"  {p}  [RUPTURE]"))
        elif p.quantite <= Magasin.SEUIL_STOCK_FAIBLE:
            print(c.jaune(f"  {p}  [STOCK FAIBLE]"))
        else:
            print(c.vert(f"  {p}"))

    def afficher_liste_produits(self, produits: list[Produit]) -> None:
        if not produits:
            print(c.jaune("  Aucun produit à afficher."))
            return
        for p in sorted(produits, key=lambda x: x.code):
            self.afficher_produit(p)

    # ----------------------------------------------------------
    #  Alertes automatiques (affichées en tête de menu)
    # ----------------------------------------------------------

    def afficher_alertes(self) -> None:
        """Affiche les alertes de rupture et de stock faible."""
        ruptures = self.magasin.produits_en_rupture()
        faibles  = self.magasin.produits_stock_faible()
        if ruptures:
            print(c.rouge(f"\n  /!\\ RUPTURE DE STOCK : {len(ruptures)} produit(s)"), end="")
            noms = ", ".join(p.nom for p in ruptures)
            print(c.rouge(f"  ({noms})"))
        if faibles:
            print(c.jaune(f"  /!\\ STOCK FAIBLE     : {len(faibles)} produit(s)"), end="")
            noms = ", ".join(p.nom for p in faibles)
            print(c.jaune(f"  ({noms})"))

    # ----------------------------------------------------------
    #  Option a : Enregistrer une vente
    # ----------------------------------------------------------

    def enregistrer_vente(self) -> None:
        self.titre("ENREGISTRER UNE VENTE")

        # --- Choix du client ---
        if not self.magasin.clients:
            print(c.rouge("  Aucun client enregistré. Ajoutez d'abord un client."))
            return

        print(c.bleu("  Clients disponibles :"))
        for nom, client in self.magasin.clients.items():
            dette_str = (
                c.rouge(f"  ardoise: {client.dette:.2f} €")
                if client.dette > 0 else ""
            )
            print(f"    - {nom}{dette_str}")

        nom_client = input("  Nom du client : ").strip()
        if nom_client not in self.magasin.clients:
            print(c.rouge("  Client inconnu."))
            return

        # --- Affichage des produits disponibles (colorés) ---
        produits_dispos = [p for p in self.magasin.produits.values() if p.quantite > 0]
        if not produits_dispos:
            print(c.rouge("  Aucun produit en stock."))
            return

        print(c.bleu("\n  Produits disponibles :"))
        self.afficher_liste_produits(produits_dispos)

        # --- Constitution du panier ---
        panier: list[tuple[str, int]] = []
        print(c.cyan("\n  (Entrée vide pour terminer)"))
        while True:
            code = input("  Code produit : ").strip().upper()
            if not code:
                break
            if code not in self.magasin.produits:
                print(c.rouge("  Code inconnu, réessayez."))
                continue
            if self.magasin.produits[code].quantite <= 0:
                print(c.rouge("  Ce produit est en rupture de stock."))
                continue
            qte = self.saisir_int("  Quantité    : ")
            if qte <= 0:
                print(c.rouge("  Quantité invalide."))
                continue
            panier.append((code, qte))

        if not panier:
            print(c.jaune("  Panier vide, vente annulée."))
            return

        # --- Récapitulatif du panier avec total (avant validation) ---
        print(c.bleu("\n  ─── Récapitulatif du panier ───"))
        total_preview = 0.0
        for code, qte in panier:
            p = self.magasin.produits[code]
            sous_total = p.prix * qte
            total_preview += sous_total
            print(f"    {p.nom:<28} x{qte}   {sous_total:>8.2f} €")
        print(c.gras(f"  {'TOTAL':<35} {total_preview:>8.2f} €"))

        # --- Paiement immédiat ou ardoise ---
        print(c.bleu("\n  Mode de règlement :"))
        print("    1) Paiement immédiat")
        print("    2) Mettre en ardoise")
        choix_paiement = input("  Choix : ").strip()
        paye = choix_paiement != "2"
        if paye:
            print(c.vert("  → Paiement immédiat sélectionné."))
        else:
            print(c.jaune("  → Ardoise sélectionnée (dette ajoutée au compte client)."))

        # --- Confirmation finale ---
        if not self.confirmer(c.gras("  Confirmer la vente ?")):
            print(c.jaune("  Vente annulée."))
            return

        # --- Enregistrement ---
        try:
            total, numero = self.magasin.enregistrer_vente(nom_client, panier, paye)
            print(c.vert(
                f"\n  ✔ Vente #{numero:04d} enregistrée — Total : {total:.2f} €"
            ))
            if not paye:
                dette = self.magasin.clients[nom_client].dette
                print(c.jaune(f"  Ardoise totale de {nom_client} : {dette:.2f} €"))
            self.magasin.sauvegarder_tout()
        except ValueError as e:
            print(c.rouge(f"  Erreur : {e}"))

    # ----------------------------------------------------------
    #  Option b : Ajouter un produit
    # ----------------------------------------------------------

    def ajouter_produit(self) -> None:
        self.titre("AJOUTER UN PRODUIT")

        # Afficher les catégories existantes pour guider la saisie
        cats = self.magasin.categories()
        if cats:
            print(c.bleu("  Catégories existantes : ") + ", ".join(cats))

        code      = input("  Code       : ").strip()
        nom       = input("  Nom        : ").strip()
        prix      = self.saisir_float("  Prix (€)   : ")
        quantite  = self.saisir_int("  Quantité   : ")
        categorie = input("  Catégorie  : ").strip() or "Divers"

        if not code or not nom:
            print(c.rouge("  Code et nom obligatoires."))
            return

        cree = self.magasin.ajouter_produit(code, nom, prix, quantite, categorie)
        if cree:
            print(c.vert(f"  Produit '{nom}' ajouté dans la catégorie '{categorie}'."))
        else:
            print(c.jaune(f"  Code existant : quantité mise à jour."))
        self.magasin.sauvegarder_stock()

    # ----------------------------------------------------------
    #  Option c : Ajouter un client
    # ----------------------------------------------------------

    def ajouter_client(self) -> None:
        self.titre("AJOUTER UN CLIENT")
        nom     = input("  Nom     : ").strip()
        adresse = input("  Adresse : ").strip()

        if not nom:
            print(c.rouge("  Le nom est obligatoire."))
            return

        cree = self.magasin.ajouter_client(nom, adresse)
        if cree:
            print(c.vert(f"  Client '{nom}' ajouté."))
        else:
            print(c.rouge(f"  Un client avec ce nom existe déjà."))
        self.magasin.sauvegarder_clients()

    # ----------------------------------------------------------
    #  Option d : Voir le stock
    # ----------------------------------------------------------

    def voir_stock(self) -> None:
        self.titre("STOCK")
        print("  1) Tous les produits (colorés)")
        print("  2) Recherche par code")
        print("  3) Recherche par nom")
        print("  4) Filtrer par catégorie")
        print("  5) Alertes stock faible / ruptures")
        choix = input("  Choix : ").strip()

        if choix == "2":
            code = input("  Code produit : ").strip()
            p = self.magasin.rechercher_produit(code)
            if p:
                self.afficher_produit(p)
            else:
                print(c.rouge(f"  Produit '{code.upper()}' introuvable."))

        elif choix == "3":
            terme = input("  Nom (ou partie du nom) : ").strip()
            resultats = self.magasin.rechercher_par_nom(terme)
            if resultats:
                print(c.bleu(f"  {len(resultats)} résultat(s) :"))
                self.afficher_liste_produits(resultats)
            else:
                print(c.rouge(f"  Aucun produit ne correspond à '{terme}'."))

        elif choix == "4":
            cats = self.magasin.categories()
            if not cats:
                print(c.rouge("  Aucune catégorie disponible."))
                return
            print(c.bleu("  Catégories disponibles :"))
            for i, cat in enumerate(cats, 1):
                print(f"    {i}) {cat}")
            choix_cat = input("  Numéro ou nom de catégorie : ").strip()
            # Accepter numéro ou nom
            if choix_cat.isdigit():
                idx = int(choix_cat) - 1
                categorie = cats[idx] if 0 <= idx < len(cats) else None
            else:
                categorie = choix_cat if choix_cat in cats else None
            if not categorie:
                print(c.rouge("  Catégorie invalide."))
                return
            produits_cat = self.magasin.produits_par_categorie(categorie)
            print(c.bleu(f"\n  Catégorie : {categorie}"))
            self.afficher_liste_produits(produits_cat)

        elif choix == "5":
            ruptures = self.magasin.produits_en_rupture()
            faibles  = self.magasin.produits_stock_faible()
            print(c.rouge(f"\n  Ruptures ({len(ruptures)}) :"))
            for p in ruptures:
                print(c.rouge(f"    {p}"))
            print(c.jaune(f"\n  Stock faible (seuil ≤ {Magasin.SEUIL_STOCK_FAIBLE}) — {len(faibles)} produit(s) :"))
            for p in faibles:
                print(c.jaune(f"    {p}"))

        else:
            if not self.magasin.produits:
                print(c.rouge("  Aucun produit en stock."))
                return
            self.afficher_liste_produits(list(self.magasin.produits.values()))

    # ----------------------------------------------------------
    #  Option e : Afficher les clients
    # ----------------------------------------------------------

    def afficher_clients(self) -> None:
        self.titre("LISTE DES CLIENTS")
        if not self.magasin.clients:
            print(c.rouge("  Aucun client enregistré."))
            return
        for client in sorted(self.magasin.clients.values(), key=lambda x: x.nom):
            if client.dette > 0:
                print(c.rouge(f"  {client}"))   # rouge si ardoise non réglée
            else:
                print(c.vert(f"  {client}"))    # vert si client à jour

    # ----------------------------------------------------------
    #  Option f : Produits en rupture
    # ----------------------------------------------------------

    def produits_rupture(self) -> None:
        self.titre("PRODUITS EN RUPTURE DE STOCK")
        ruptures = self.magasin.produits_en_rupture()
        if not ruptures:
            print(c.vert("  Aucun produit en rupture. Tout est en stock !"))
        else:
            for p in ruptures:
                print(c.rouge(f"  {p}"))

    # ----------------------------------------------------------
    #  Option g : Générer un rapport
    # ----------------------------------------------------------

    def generer_rapport(self) -> None:
        self.titre("GÉNÉRATION DU RAPPORT MENSUEL")

        # Afficher le produit le plus vendu avant d'écrire le rapport
        plus_vendu = self.magasin.produit_plus_vendu()
        if plus_vendu:
            print(c.magenta(
                f"  🏆 Produit le plus vendu : {plus_vendu[0]} ({plus_vendu[1]} unités)"
            ))

        chemin = self.magasin.generer_rapport()
        print(c.vert(f"  Rapport généré : {chemin}"))

    # ----------------------------------------------------------
    #  Option h : Réapprovisionner un produit
    # ----------------------------------------------------------

    def reapprovisionner(self) -> None:
        self.titre("RÉAPPROVISIONNEMENT")

        # Afficher d'abord les ruptures et stocks faibles pour guider le choix
        ruptures = self.magasin.produits_en_rupture()
        faibles  = self.magasin.produits_stock_faible()

        if ruptures:
            print(c.rouge(f"  Ruptures ({len(ruptures)}) :"))
            for p in ruptures:
                print(c.rouge(f"    {p}"))

        if faibles:
            print(c.jaune(f"\n  Stock faible ({len(faibles)}) :"))
            for p in faibles:
                print(c.jaune(f"    {p}"))

        if not ruptures and not faibles:
            print(c.vert("  Tous les produits ont un stock suffisant."))

        print()

        # Saisie du produit à réapprovisionner (code ou nom)
        saisie = input(
            "  Code ou nom du produit à réapprovisionner (Entrée pour annuler) : "
        ).strip()
        if not saisie:
            print(c.jaune("  Réapprovisionnement annulé."))
            return

        # Recherche par code d'abord, puis par nom
        produit = self.magasin.rechercher_produit(saisie)
        if produit is None:
            resultats = self.magasin.rechercher_par_nom(saisie)
            if len(resultats) == 1:
                produit = resultats[0]
            elif len(resultats) > 1:
                print(c.bleu(f"  {len(resultats)} produits correspondent :"))
                for p in resultats:
                    print(f"    {p}")
                code = input("  Entrez le code exact : ").strip()
                produit = self.magasin.rechercher_produit(code)

        if produit is None:
            print(c.rouge("  Produit introuvable."))
            return

        # Afficher l'état actuel
        print(c.bleu(f"\n  Produit sélectionné :"))
        self.afficher_produit(produit)
        print(f"  Stock actuel : {produit.quantite} unité(s)")

        # Saisie de la quantité à ajouter
        qte = self.saisir_int("  Quantité à ajouter : ")
        if qte <= 0:
            print(c.rouge("  Quantité invalide."))
            return

        # Confirmation
        if not self.confirmer(
            c.gras(f"  Ajouter {qte} unité(s) à '{produit.nom}' ?")
        ):
            print(c.jaune("  Réapprovisionnement annulé."))
            return

        # Mise à jour du stock
        produit.quantite += qte
        self.magasin.sauvegarder_stock()
        print(c.vert(
            f"  ✔ '{produit.nom}' réapprovisionné — nouveau stock : {produit.quantite} unité(s)"
        ))

    # ----------------------------------------------------------
    #  Boucle principale
    # ----------------------------------------------------------

    def afficher_menu(self) -> None:
        print("\n" + c.cyan("-"*52))
        print(c.gras("  MENU PRINCIPAL"))
        print(f"  {c.cyan('a)')} Enregistrer une vente")
        print(f"  {c.cyan('b)')} Ajouter un produit")
        print(f"  {c.cyan('c)')} Ajouter un client")
        print(f"  {c.cyan('d)')} Voir le stock")
        print(f"  {c.cyan('e)')} Afficher les clients")
        print(f"  {c.cyan('f)')} Produits en rupture de stock")
        print(f"  {c.cyan('g)')} Générer un rapport mensuel")
        print(f"  {c.cyan('h)')} Réapprovisionner un produit")
        print(f"  {c.cyan('i)')} Quitter")
        print(c.cyan("-"*52))

    def lancer(self) -> None:
        """Boucle principale de l'application."""
        print(c.gras(c.cyan("\n  === Bienvenue dans le système de gestion de magasin ===")))

        actions = {
            "a": self.enregistrer_vente,
            "b": self.ajouter_produit,
            "c": self.ajouter_client,
            "d": self.voir_stock,
            "e": self.afficher_clients,
            "f": self.produits_rupture,
            "g": self.generer_rapport,
            "h": self.reapprovisionner,
        }

        while True:
            self.afficher_alertes()   # affiche les alertes stock en temps réel
            self.afficher_menu()
            choix = input("  Votre choix : ").strip().lower()

            if choix == "i":
                self.magasin.sauvegarder_tout()
                print(c.vert("  Au revoir !"))
                break
            elif choix in actions:
                actions[choix]()
            else:
                print(c.rouge("  Choix invalide, veuillez réessayer."))
