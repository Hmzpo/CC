# Système de Gestion de Magasin — CC2
## Document explicatif : Cahier des charges & Solutions

---

## 1. Cahier des charges

### 1.1 Contexte et objectif

L'application permet à un gérant de magasin de :
- **Gérer son inventaire** par catégorie, avec alertes de stock faible.
- **Suivre ses clients** (enregistrement, historique d'achats, ardoise).
- **Enregistrer les ventes** avec numéro automatique, choix paiement/ardoise et confirmation.
- **Réapprovisionner** les produits en rupture ou en stock faible.
- **Produire un rapport mensuel** avec chiffre d'affaires et produit le plus vendu.

Toutes les données sont persistées dans des **fichiers textes** simples, sans base de données.

---

### 1.2 Contraintes fonctionnelles

| Référence | Description |
|-----------|-------------|
| CF-01 | Charger l'inventaire depuis `stock.txt` au démarrage |
| CF-02 | Charger les clients depuis `clients.txt` au démarrage |
| CF-03 | Enregistrer chaque vente dans `ventes.log` avec horodatage et numéro |
| CF-04 | Générer un rapport dans `bilan_mensuel.txt` |
| CF-05 | Décrémenter le stock après chaque vente |
| CF-06 | Menu interactif avec 9 options (a → i) |
| CF-07 | Sauvegarder les données à la fermeture (option i) |
| CF-08 | Afficher les alertes de stock faible et ruptures à chaque tour de menu |
| CF-09 | Permettre le réapprovisionnement d'un produit (option h) |

### 1.3 Contraintes techniques

- Langage : **Python 3.10+**
- Pas de bibliothèque externe — uniquement la bibliothèque standard (`os`, `datetime`).
- Codes couleur **ANSI** pour l'affichage terminal (module `couleurs.py`).
- Interface : mode **texte/terminal** uniquement.

---

### 1.4 Format des fichiers

#### `stock.txt`
```
# FORMAT : CODE|NOM|PRIX|QUANTITE|CATEGORIE
P001|Café moulu|3.50|100|Boissons
P002|Thé vert|2.80|50|Boissons
P004|Biscuits|2.50|4|Snacks
```
Rétrocompatible : un fichier à 4 champs (sans catégorie) est accepté (catégorie = "Divers").

#### `clients.txt`
```
# FORMAT : NOM|ADRESSE|DETTE
Alice Dupont|12 rue des Fleurs Paris|0.00
Bob Martin|5 avenue Victor Hugo Lyon|15.60
```

#### `ventes.log` (ajout en mode append — journal immuable)
```
2026-05-21 10:32:15 | #0001 | Alice Dupont | Café moulu x2 (7.00€); Thé vert x1 (2.80€) | TOTAL: 9.80€ | PAYÉ
2026-05-21 11:15:00 | #0002 | Bob Martin | Sucre en poudre x3 (3.60€) | TOTAL: 3.60€ | ARDOISE
```

#### `compteur_ventes.txt`
Contient uniquement le dernier numéro de vente utilisé (ex : `2`).

#### `bilan_mensuel.txt` (écrasé à chaque génération)
```
=== BILAN MENSUEL - 2026-05 ===
Généré le : 2026-05-21 11:00:00

Nombre de ventes       : 2
  dont payées          : 1
  dont en ardoise      : 1
Chiffre d'affaires     : 13.40 €
Produit le plus vendu  : Café moulu (2 unités)
...
```

---

## 2. Architecture de la solution

### 2.1 Structure des fichiers

```
CC/
├── main.py           ← point d'entrée  (python3 main.py)
├── menu.py           ← classe Menu     (interface utilisateur)
├── magasin_core.py   ← classe Magasin  (logique métier)
├── client.py         ← classe Client
├── produit.py        ← classe Produit
├── couleurs.py       ← codes ANSI pour l'affichage coloré
├── stock.txt         ← données produits
├── clients.txt       ← données clients
├── ventes.log        ← journal des ventes (append-only)
├── compteur_ventes.txt ← numéro de vente courant
└── bilan_mensuel.txt ← rapport généré à la demande
```

### 2.2 Diagramme de classes (simplifié)

```
┌──────────────────┐         ┌──────────────────┐
│     Produit      │         │     Client       │
├──────────────────┤         ├──────────────────┤
│ code             │         │ nom              │
│ nom              │         │ adresse          │
│ prix             │         │ dette            │
│ quantite         │         │ historique       │
│ categorie        │         ├──────────────────┤
├──────────────────┤         │ ajouter_achat()  │
│ vers_ligne()     │         │ vers_ligne()     │
│ depuis_ligne()   │         │ depuis_ligne()   │
└──────────────────┘         └──────────────────┘
        │                            │
        └──────────┐  ┌──────────────┘
                   ▼  ▼
          ┌──────────────────────┐
          │       Magasin        │
          ├──────────────────────┤
          │ produits: dict       │
          │ clients: dict        │
          │ SEUIL_STOCK_FAIBLE=5 │
          ├──────────────────────┤
          │ charger_stock()      │
          │ sauvegarder_*()      │
          │ ajouter_produit()    │
          │ rechercher_produit() │
          │ rechercher_par_nom() │
          │ produits_en_rupture()│
          │ produits_stock_faible() │
          │ categories()         │
          │ produits_par_categorie() │
          │ ajouter_client()     │
          │ prochain_numero_vente() │
          │ enregistrer_vente()  │
          │ produit_plus_vendu() │
          │ generer_rapport()    │
          └──────────┬───────────┘
                     │ composition
                     ▼
          ┌──────────────────────┐
          │        Menu          │
          ├──────────────────────┤
          │ lancer()             │
          │ afficher_alertes()   │
          │ afficher_produit()   │
          │ enregistrer_vente()  │
          │ ajouter_produit()    │
          │ ajouter_client()     │
          │ voir_stock()         │
          │ afficher_clients()   │
          │ produits_rupture()   │
          │ generer_rapport()    │
          │ reapprovisionner()   │
          └──────────────────────┘
```

### 2.3 Description des classes

#### `couleurs.py`
Module utilitaire exposant des fonctions `rouge()`, `vert()`, `jaune()`, `bleu()`, `magenta()`, `cyan()`, `gras()` basées sur les **codes d'échappement ANSI**. Centraliser les couleurs ici évite de dupliquer les codes dans tout le projet.

#### Classe `Produit`
Encapsule les données d'un article, dont le nouveau champ `categorie`. Les méthodes `vers_ligne()` / `depuis_ligne()` gèrent la sérialisation. La lecture accepte 4 ou 5 champs (rétrocompatibilité avec les anciens fichiers sans catégorie).

#### Classe `Client`
Le champ `dette` cumule les montants mis en ardoise. Il n'est incrémenté que si la vente est enregistrée avec `paye=False`. L'`historique` est une liste en mémoire (non persistée séparément).

#### Classe `Magasin`
Cœur du système. Utilise deux **dictionnaires** pour un accès O(1) :
- `produits` : indexé par `code`.
- `clients` : indexé par `nom`.

Méthodes clés :
- `enregistrer_vente()` : vérification en **deux passes** (contrôle d'abord, modification ensuite) pour garantir la cohérence.
- `prochain_numero_vente()` : lit et incrémente `compteur_ventes.txt` à chaque vente.
- `produit_plus_vendu()` : parse `ventes.log` en comptant les quantités par produit.
- `produits_stock_faible()` : retourne les produits avec `0 < quantite <= SEUIL_STOCK_FAIBLE`.

#### Classe `Menu`
Sépare l'interface utilisateur de la logique métier. Chaque option est une méthode distincte, enregistrée dans un dictionnaire `actions`. À chaque tour de boucle, `afficher_alertes()` signale automatiquement les ruptures et stocks faibles.

---

## 3. Options du menu (a → i)

| Option | Titre | Fonctionnalités incluses |
|--------|-------|--------------------------|
| a | Enregistrer une vente | Affichage coloré des produits, constitution du panier, récapitulatif avec total, choix paiement/ardoise, confirmation |
| b | Ajouter un produit | Saisie du code, nom, prix, quantité, catégorie |
| c | Ajouter un client | Saisie du nom et de l'adresse |
| d | Voir le stock | Tous (colorés), par code, par nom, par catégorie, alertes stock faible |
| e | Afficher les clients | Liste colorée : rouge si ardoise, vert si à jour |
| f | Produits en rupture | Liste rouge des produits à quantité ≤ 0 |
| g | Générer un rapport | Rapport mensuel + produit le plus vendu affiché |
| h | Réapprovisionner | Affiche ruptures/stocks faibles, recherche par code ou nom, ajout de quantité |
| i | Quitter | Sauvegarde stock et clients, fermeture propre |

---

## 4. Fonctionnalités détaillées

### 4.1 Affichage coloré (couleurs ANSI)
| Couleur | Signification |
|---------|---------------|
| Rouge   | Rupture de stock (quantite ≤ 0) / erreur / dette client |
| Jaune   | Stock faible (0 < quantite ≤ 5) / ardoise / avertissement |
| Vert    | Stock OK / succès / client à jour |
| Cyan    | Séparateurs de menu |
| Magenta | Informations statistiques (produit le plus vendu) |
| Bleu    | Titres de sous-sections |

### 4.2 Réapprovisionnement (option h)
Flux :
1. Afficher les ruptures (rouge) et stocks faibles (jaune) pour guider le choix.
2. Saisir un **code** ou un **nom** (recherche partielle insensible à la casse).
3. Si plusieurs produits correspondent au nom, afficher la liste et demander le code exact.
4. Afficher le stock actuel du produit sélectionné.
5. Saisir la quantité à ajouter.
6. Demander confirmation avant d'écrire.
7. Sauvegarder `stock.txt`.

### 4.3 Enregistrement d'une vente (option a)
Flux :
1. Choisir le client (ardoise affichée en rouge si > 0).
2. Afficher les produits disponibles avec couleurs.
3. Constituer le panier (code + quantité, en boucle).
4. Afficher le **récapitulatif ligne par ligne + total** avant toute action.
5. Choisir : **paiement immédiat** ou **ardoise**.
6. **Confirmer** (o/n).
7. Enregistrer : décrémenter le stock, mettre à jour la dette si ardoise, écrire dans `ventes.log` avec numéro automatique.

### 4.4 Numéro de vente automatique
`compteur_ventes.txt` contient le dernier numéro utilisé. À chaque vente, `prochain_numero_vente()` lit ce fichier, incrémente et réécrit. Le numéro s'affiche sous la forme `#0001`, `#0002`, etc.

### 4.5 Gestion des catégories (option d)
Les produits ont un champ `categorie` (ex : "Boissons", "Snacks", "Épicerie"). L'option d permet de filtrer par catégorie : la liste des catégories existantes s'affiche numérotée, le gérant choisit par numéro ou par nom.

### 4.6 Produit le plus vendu
`produit_plus_vendu()` parse toutes les lignes de `ventes.log`, extrait les couples `(nom_produit, quantité)` via le pattern `Nom x2 (...)`, cumule par produit et retourne le maximum. Affiché dans l'option g avant la génération du rapport.

---

## 5. Choix de conception et justifications

### 5.1 Dictionnaires plutôt que listes
Accès en O(1) par code/nom. La recherche par nom (`rechercher_par_nom()`) reste O(n) mais n'est utilisée que dans des flux interactifs.

### 5.2 Séparation sérialisation / logique métier
`vers_ligne()` et `depuis_ligne()` sont dans chaque classe modèle. Changer le format de fichier ne touche qu'une classe.

### 5.3 Vérification en deux passes dans `enregistrer_vente()`
Tous les contrôles (client existant, produit existant, stock suffisant) sont effectués **avant** toute modification. Si une erreur est détectée, une `ValueError` est levée sans avoir altéré le stock. Garantit la cohérence des données.

### 5.4 `ventes.log` en mode append
Ouverture avec `"a"` : les entrées existantes ne sont jamais modifiées. Ce journal est la source de vérité pour les rapports et les statistiques.

### 5.5 Compteur de vente persisté
Un fichier `compteur_ventes.txt` contient un entier. Cela évite de recompter les lignes de `ventes.log` à chaque démarrage et résiste aux modifications manuelles du journal.

### 5.6 Rétrocompatibilité du format `stock.txt`
`depuis_ligne()` accepte 4 ou 5 champs. Un fichier sans colonne `CATEGORIE` charge correctement avec la valeur par défaut "Divers".

### 5.7 Recherche par nom flexible
`rechercher_par_nom()` utilise `terme in p.nom.lower()` : une recherche sur "café" trouve "Café moulu" sans distinction majuscules/minuscules.

---

## 6. Scénarios d'utilisation

### Scénario 1 : Premier démarrage
1. Aucun fichier texte n'existe.
2. Le programme démarre sans erreur.
3. Ajout de produits (option b) avec catégories et de clients (option c).
4. Fermeture (option i) : `stock.txt` et `clients.txt` sont créés.

### Scénario 2 : Enregistrement d'une vente avec ardoise
1. Option a → choisir "Bob Martin" (ardoise affichée en rouge).
2. Sélectionner des produits, voir le total.
3. Choisir "2) Mettre en ardoise".
4. Confirmer → vente `#0003` enregistrée, dette de Bob augmentée.

### Scénario 3 : Réapprovisionnement après rupture
1. Le menu affiche `/!\ RUPTURE DE STOCK : 1 produit(s) (Jus d'orange)` en rouge.
2. Option h → les ruptures s'affichent.
3. Saisir "jus" → "Jus d'orange" trouvé automatiquement.
4. Entrer 50 → confirmer → stock mis à jour, alerte disparaît au prochain tour.

### Scénario 4 : Rapport mensuel
1. Option g → affiche le produit le plus vendu.
2. `bilan_mensuel.txt` est généré avec CA, nb ventes payées/ardoise, top produits, top clients, état du stock.

---

## 7. Tests conseillés

| Test | Attendu |
|------|---------|
| Ajouter un produit avec un code existant | Quantité incrémentée, pas de doublon |
| Vendre plus que le stock disponible | Erreur, stock inchangé |
| Vendre à un client inconnu | Erreur, aucune modification |
| Ardoise : vérifier la dette du client | Dette augmentée du montant de la vente |
| Paiement immédiat : vérifier la dette | Dette inchangée |
| Réapprovisionner par nom partiel | Produit trouvé sans saisir le code complet |
| Réapprovisionner avec quantité ≤ 0 | Message d'erreur, stock inchangé |
| Générer un rapport sans ventes ce mois | Rapport vide mais valide |
| Quitter et relancer | Données rechargées correctement |
| Stock faible (quantite=4) | Alerte jaune en tête de menu |

---

## 8. Améliorations possibles (hors périmètre CC2)

- Remboursement d'ardoise : option dédiée pour enregistrer un paiement partiel/total d'un client.
- Modification du prix ou du nom d'un produit existant.
- Historique des réapprovisionnements (fichier `reappros.log`).
- Export CSV du rapport mensuel.
- Interface graphique (Tkinter).
- Utilisation d'une base SQLite pour des performances accrues sur de grands volumes.
