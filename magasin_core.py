"""Classe Magasin : gère l'inventaire, les clients et les ventes."""

import os
from datetime import datetime

from produit import Produit
from client import Client


class Magasin:
    """
    Gère l'inventaire des produits, la liste des clients
    et l'enregistrement des ventes.
    """

    FICHIER_STOCK    = "stock.txt"
    FICHIER_CLIENTS  = "clients.txt"
    FICHIER_VENTES   = "ventes.log"
    FICHIER_RAPPORT  = "bilan_mensuel.txt"
    FICHIER_COMPTEUR = "compteur_ventes.txt"

    # Seuil en-dessous duquel une alerte "stock faible" est émise
    SEUIL_STOCK_FAIBLE = 5

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
            f.write("# FORMAT : CODE|NOM|PRIX|QUANTITE|CATEGORIE\n")
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

    def ajouter_produit(
        self, code: str, nom: str, prix: float, quantite: int, categorie: str = "Divers"
    ) -> bool:
        """
        Ajoute un nouveau produit ou incrémente la quantité si le code existe.
        Retourne True si création, False si mise à jour.
        """
        code = code.strip().upper()
        if code in self.produits:
            self.produits[code].quantite += quantite
            return False
        self.produits[code] = Produit(code, nom, prix, quantite, categorie)
        return True

    def rechercher_produit(self, code: str) -> Produit | None:
        return self.produits.get(code.strip().upper())

    def rechercher_par_nom(self, terme: str) -> list[Produit]:
        """Retourne les produits dont le nom contient le terme (insensible à la casse)."""
        terme = terme.strip().lower()
        return [p for p in self.produits.values() if terme in p.nom.lower()]

    def produits_en_rupture(self) -> list[Produit]:
        """Retourne les produits dont la quantité est <= 0."""
        return [p for p in self.produits.values() if p.quantite <= 0]

    def produits_stock_faible(self) -> list[Produit]:
        """Retourne les produits avec 0 < quantite <= SEUIL_STOCK_FAIBLE."""
        return [
            p for p in self.produits.values()
            if 0 < p.quantite <= self.SEUIL_STOCK_FAIBLE
        ]

    def categories(self) -> list[str]:
        """Retourne la liste triée des catégories disponibles."""
        return sorted(set(p.categorie for p in self.produits.values()))

    def produits_par_categorie(self, categorie: str) -> list[Produit]:
        """Retourne les produits appartenant à une catégorie donnée."""
        return [p for p in self.produits.values() if p.categorie == categorie]

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
    #  Numéro de vente automatique
    # ----------------------------------------------------------

    def prochain_numero_vente(self) -> int:
        """Lit le compteur persisté, l'incrémente et le sauvegarde."""
        numero = 1
        if os.path.exists(self.FICHIER_COMPTEUR):
            with open(self.FICHIER_COMPTEUR, "r", encoding="utf-8") as f:
                try:
                    numero = int(f.read().strip()) + 1
                except ValueError:
                    numero = 1
        with open(self.FICHIER_COMPTEUR, "w", encoding="utf-8") as f:
            f.write(str(numero))
        return numero

    # ----------------------------------------------------------
    #  Enregistrement d'une vente
    # ----------------------------------------------------------

    def enregistrer_vente(
        self,
        nom_client: str,
        panier: list[tuple[str, int]],
        paye: bool = True,
    ) -> tuple[float, int]:
        """
        Effectue une vente.

        panier : liste de tuples (code_produit, quantite_voulue)
        paye   : True  → paiement immédiat (dette inchangée)
                 False → mise en ardoise (dette augmentée du total)

        Retourne (montant_total, numero_vente).
        Lève ValueError si client/produit inconnu ou stock insuffisant.
        """
        if nom_client not in self.clients:
            raise ValueError(f"Client inconnu : {nom_client}")

        # Première passe : vérification des stocks sans modification
        lignes_detail: list[tuple[Produit, int, float]] = []
        total = 0.0
        for code, qte in panier:
            produit = self.rechercher_produit(code)
            if produit is None:
                raise ValueError(f"Produit inconnu : {code}")
            if produit.quantite < qte:
                raise ValueError(
                    f"Stock insuffisant pour '{produit.nom}' "
                    f"(demandé : {qte}, disponible : {produit.quantite})"
                )
            sous_total = produit.prix * qte
            total += sous_total
            lignes_detail.append((produit, qte, sous_total))

        # Deuxième passe : mise à jour des stocks
        for produit, qte, _ in lignes_detail:
            produit.quantite -= qte

        # Ardoise : seulement si le client ne paie pas immédiatement
        if not paye:
            self.clients[nom_client].dette += total

        # Numéro de vente automatique
        numero = self.prochain_numero_vente()

        # Journalisation horodatée dans ventes.log (mode append)
        horodatage = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        detail_str = "; ".join(
            f"{p.nom} x{q} ({st:.2f}€)" for p, q, st in lignes_detail
        )
        statut = "PAYÉ" if paye else "ARDOISE"
        ligne_log = (
            f"{horodatage} | #{numero:04d} | {nom_client} | "
            f"{detail_str} | TOTAL: {total:.2f}€ | {statut}\n"
        )
        with open(self.FICHIER_VENTES, "a", encoding="utf-8") as f:
            f.write(ligne_log)

        self.clients[nom_client].ajouter_achat(ligne_log.strip())
        return total, numero

    # ----------------------------------------------------------
    #  Statistiques
    # ----------------------------------------------------------

    def produit_plus_vendu(self) -> tuple[str, int] | None:
        """
        Parcourt ventes.log et retourne (nom_produit, quantite_totale)
        du produit le plus vendu toutes périodes confondues.
        """
        compteur: dict[str, int] = {}
        if not os.path.exists(self.FICHIER_VENTES):
            return None
        with open(self.FICHIER_VENTES, "r", encoding="utf-8") as f:
            for ligne in f:
                if not ligne.strip():
                    continue
                # Chaque article est séparé par ";" dans la ligne
                for item in ligne.split(";"):
                    item = item.strip()
                    if " x" not in item or "(" not in item:
                        continue
                    try:
                        parties = item.split(" x")
                        nom = parties[0].strip()
                        # Retirer le préfixe horodatage/client collé (format multi-colonnes)
                        if "|" in nom:
                            nom = nom.split("|")[-1].strip()
                        qte = int(parties[1].split(" ")[0].strip())
                        compteur[nom] = compteur.get(nom, 0) + qte
                    except (ValueError, IndexError):
                        pass
        if not compteur:
            return None
        return max(compteur.items(), key=lambda x: x[1])

    # ----------------------------------------------------------
    #  Génération du rapport mensuel
    # ----------------------------------------------------------

    def generer_rapport(self) -> str:
        """
        Analyse ventes.log pour le mois courant et écrit bilan_mensuel.txt.
        Compatible avec l'ancien format (4 champs) et le nouveau (6 champs).
        Retourne le chemin du fichier créé.
        """
        mois_courant = datetime.now().strftime("%Y-%m")
        total_mois = 0.0
        nb_ventes = 0
        nb_payes = 0
        nb_ardoises = 0
        compteur_produits: dict[str, float] = {}  # nom_produit -> chiffre d'affaires
        compteur_clients: dict[str, float] = {}   # nom_client  -> montant dépensé

        if os.path.exists(self.FICHIER_VENTES):
            with open(self.FICHIER_VENTES, "r", encoding="utf-8") as f:
                for ligne in f:
                    if not ligne.strip() or not ligne.startswith(mois_courant):
                        continue
                    nb_ventes += 1
                    parties = ligne.split("|")
                    if len(parties) < 4:
                        continue

                    # Détecter le format : nouveau (parties[1] = #num) ou ancien
                    if parties[1].strip().startswith("#"):
                        nom_client   = parties[2].strip()
                        detail_part  = "|".join(parties[3:-2])
                        montant_str  = parties[-2].replace("TOTAL:", "").replace("€", "").strip()
                        statut       = parties[-1].strip()
                    else:
                        nom_client   = parties[1].strip()
                        detail_part  = "|".join(parties[2:-1])
                        montant_str  = parties[-1].replace("TOTAL:", "").replace("€", "").strip()
                        statut       = "PAYÉ"

                    if statut == "PAYÉ":
                        nb_payes += 1
                    else:
                        nb_ardoises += 1

                    try:
                        montant = float(montant_str)
                    except ValueError:
                        continue
                    total_mois += montant
                    compteur_clients[nom_client] = compteur_clients.get(nom_client, 0) + montant

                    for item in detail_part.split(";"):
                        item = item.strip()
                        if " x" in item and "(" in item:
                            try:
                                nom_prod = item.split(" x")[0].strip()
                                montant_prod_str = item.split("(")[-1].replace("€)", "").strip()
                                compteur_produits[nom_prod] = (
                                    compteur_produits.get(nom_prod, 0) + float(montant_prod_str)
                                )
                            except ValueError:
                                pass

        plus_vendu = self.produit_plus_vendu()

        lignes = [
            f"=== BILAN MENSUEL - {mois_courant} ===\n",
            f"Généré le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n",
            f"Nombre de ventes       : {nb_ventes}\n",
            f"  dont payées          : {nb_payes}\n",
            f"  dont en ardoise      : {nb_ardoises}\n",
            f"Chiffre d'affaires     : {total_mois:.2f} €\n",
        ]
        if plus_vendu:
            lignes.append(
                f"Produit le plus vendu  : {plus_vendu[0]} ({plus_vendu[1]} unités)\n"
            )

        lignes.append("\n--- Top produits (CA ce mois) ---\n")
        for nom, ca in sorted(compteur_produits.items(), key=lambda x: -x[1]):
            lignes.append(f"  {nom:<30} {ca:>10.2f} €\n")

        lignes.append("\n--- Top clients (montant ce mois) ---\n")
        for nom, montant in sorted(compteur_clients.items(), key=lambda x: -x[1]):
            lignes.append(f"  {nom:<30} {montant:>10.2f} €\n")

        lignes.append("\n--- État du stock ---\n")
        for p in sorted(self.produits.values(), key=lambda x: x.nom):
            if p.quantite <= 0:
                statut_stock = " [RUPTURE]"
            elif p.quantite <= self.SEUIL_STOCK_FAIBLE:
                statut_stock = " [STOCK FAIBLE]"
            else:
                statut_stock = ""
            lignes.append(f"  {p}{statut_stock}\n")

        with open(self.FICHIER_RAPPORT, "w", encoding="utf-8") as f:
            f.writelines(lignes)

        return self.FICHIER_RAPPORT
