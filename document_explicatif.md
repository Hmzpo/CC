# Système de Gestion de Magasin — CC2
## Document explicatif : Cahier des charges & Solutions

---

## 1. Cahier des charges

### 1.1 Contexte et objectif

L'application doit permettre à un gérant de magasin de :
- **Gérer son inventaire** (ajout, consultation, mise à jour du stock après vente).
- **Suivre ses clients** (enregistrement, historique d'achats, dettes).
- **Enregistrer les ventes** et conserver une trace horodatée.
- **Produire un rapport mensuel** synthétisant le chiffre d'affaires.

Toutes les données sont persistées dans des **fichiers textes** simples, sans base de données.

---

### 1.2 Contraintes fonctionnelles

| Référence | Description |
|-----------|-------------|
| CF-01 | Le système doit charger l'inventaire depuis `stock.txt` au démarrage. |
| CF-02 | Le système doit charger la liste des clients depuis `clients.txt` au démarrage. |
| CF-03 | Chaque vente doit être enregistrée dans `ventes.log` avec horodatage. |
| CF-04 | Le rapport mensuel doit être généré dans `bilan_mensuel.txt`. |
| CF-05 | Le stock doit être décrémenté après chaque vente. |
| CF-06 | Le menu doit proposer 8 fonctions (a à h). |
| CF-07 | Les données doivent être sauvegardées à la fermeture (option h). |

### 1.3 Contraintes techniques

- Langage : **Python 3.10+** (utilisation des unions de types `X | Y`).
- Pas de bibliothèque externe, uniquement la bibliothèque standard (`os`, `datetime`).
- Interface : mode **texte/terminal** uniquement.

---

### 1.4 Format des fichiers

#### `stock.txt`
```
# FORMAT : CODE|NOM|PRIX|QUANTITE
P001|Café moulu|3.50|100
P002|Thé vert|2.80|50
```

#### `clients.txt`
```
# FORMAT : NOM|ADRESSE|DETTE
Alice Dupont|12 rue des Fleurs Paris|0.00
Bob Martin|5 avenue Victor Hugo Lyon|15.60
```

#### `ventes.log` (ajout en mode append)
```
2026-05-21 10:32:15 | Alice Dupont | Café moulu x2 (7.00€); Thé vert x1 (2.80€) | TOTAL: 9.80€
```

#### `bilan_mensuel.txt` (écrasé à chaque génération)
```
=== BILAN MENSUEL - 2026-05 ===
Généré le : 2026-05-21 11:00:00

Nombre de ventes       : 12
Chiffre d'affaires     : 148.70 €
...
```

---

## 2. Architecture de la solution

### 2.1 Diagramme de classes (simplifié)

```
┌──────────────┐         ┌──────────────┐
│   Produit    │         │   Client     │
├──────────────┤         ├──────────────┤
│ code         │         │ nom          │
│ nom          │         │ adresse      │
│ prix         │         │ dette        │
│ quantite     │         │ historique   │
├──────────────┤         ├──────────────┤
│ vers_ligne() │         │ vers_ligne() │
│ depuis_ligne()│        │ depuis_ligne()│
└──────────────┘         └──────────────┘
        │                        │
        └────────┐  ┌────────────┘
                 ▼  ▼
          ┌─────────────────┐
          │    Magasin      │
          ├─────────────────┤
          │ produits: dict  │
          │ clients: dict   │
          ├─────────────────┤
          │ charger_stock() │
          │ sauvegarder_*() │
          │ ajouter_produit()│
          │ ajouter_client()│
          │ enregistrer_vente()│
          │ generer_rapport()│
          └────────┬────────┘
                   │ composition
                   ▼
          ┌─────────────────┐
          │      Menu       │
          ├─────────────────┤
          │ lancer()        │
          │ enregistrer_vente()│
          │ ajouter_produit()│
          │ ...             │
          └─────────────────┘
```

### 2.2 Description des classes

#### Classe `Produit`
Encapsule les données d'un article. Les méthodes `vers_ligne()` et `depuis_ligne()` assurent la **sérialisation/désérialisation** vers le format `CODE|NOM|PRIX|QUANTITE`, isolant la logique de persistance dans la classe concernée.

#### Classe `Client`
Structure similaire à `Produit`. Le champ `dette` cumule le total des achats non réglés. L'`historique` est une liste en mémoire (reconstituable depuis `ventes.log` si besoin).

#### Classe `Magasin`
Cœur du système. Utilise deux **dictionnaires** (accès en O(1)) :
- `produits` : indexé par `code`.
- `clients` : indexé par `nom`.

La méthode `enregistrer_vente()` effectue une **vérification en deux passes** :
1. Vérification de la disponibilité de tous les articles (sans modification).
2. Décrémentation des stocks seulement si tout est valide.

Cela évite un état incohérent (stocks partiellement modifiés) en cas d'erreur.

#### Classe `Menu`
Sépare l'interface utilisateur de la logique métier (**séparation des responsabilités**). Chaque option du menu est une méthode distincte, rendues accessibles via un dictionnaire `actions` dans la boucle principale.

---

## 3. Choix de conception et justifications

### 3.1 Dictionnaires plutôt que listes

Les produits et clients sont stockés dans des dictionnaires Python plutôt que des listes. Cela permet :
- Un accès direct par clé (`produits["P001"]`) sans parcours linéaire.
- Une vérification d'existence en O(1) au lieu de O(n).

### 3.2 Séparation sérialisation / logique métier

Les méthodes `vers_ligne()` et `depuis_ligne()` sont placées dans chaque classe (Produit, Client). Ainsi, si le format de fichier change, seule la classe concernée est à modifier, sans toucher à `Magasin` ni à `Menu`.

### 3.3 Vérification en deux passes dans `enregistrer_vente()`

Avant de modifier quoi que ce soit, la méthode vérifie l'ensemble du panier. Si un article manque en stock, une `ValueError` est levée **avant** toute modification. Cela garantit la cohérence des données (pas de vente partielle enregistrée).

### 3.4 Journalisation en mode `append`

Le fichier `ventes.log` est ouvert en mode `"a"` (append). Les entrées ne sont jamais écrasées, ce qui constitue un **journal immuable** des transactions.

### 3.5 Rapport mensuel filtré par mois courant

La méthode `generer_rapport()` filtre `ventes.log` en comparant le préfixe `YYYY-MM` de chaque ligne à la date courante. Cela évite de charger toutes les ventes historiques en mémoire.

---

## 4. Scénarios d'utilisation

### Scénario 1 : Premier démarrage
1. Les fichiers `stock.txt` et `clients.txt` n'existent pas.
2. Le programme démarre sans erreur (les fonctions de chargement vérifient l'existence des fichiers).
3. L'utilisateur ajoute des produits (option b) et des clients (option c).
4. À la fermeture (option h), les fichiers sont créés.

### Scénario 2 : Enregistrement d'une vente
1. L'utilisateur choisit l'option **a**.
2. Il saisit le nom d'un client existant.
3. La liste des produits en stock s'affiche.
4. Il entre les codes et quantités désirés.
5. Le système vérifie les stocks, décrémente les quantités, écrit dans `ventes.log`.

### Scénario 3 : Rupture de stock
- Un produit dont la quantité atteint 0 apparaît dans l'option **f**.
- Il ne peut plus être ajouté à un panier (vérification dans `enregistrer_vente()`).

---

## 5. Tests conseillés

| Test | Attendu |
|------|---------|
| Ajouter un produit avec un code existant | Quantité incrémentée, pas de doublon |
| Vendre plus que le stock disponible | Message d'erreur, stock inchangé |
| Ajouter un client avec un nom déjà pris | Message d'erreur |
| Générer un rapport sans ventes ce mois | Rapport vide mais valide |
| Quitter et relancer | Données rechargées correctement |

---

## 6. Améliorations possibles (hors périmètre CC2)

- Gestion des mots de passe (authentification gérant).
- Remboursement de dettes (réinitialisation du champ `dette`).
- Export CSV du rapport.
- Interface graphique (Tkinter).
- Utilisation d'une base SQLite pour des performances accrues.
