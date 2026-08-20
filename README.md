# Agricola2P

Moteur de regles + bots pour **Agricola: Terre d'Elevage** (*All Creatures Big
and Small*, Uwe Rosenberg), le jeu de placement d'ouvriers a 2 joueurs centre
sur l'elevage.

## Contenu

- `agricola2p/engine/` — le moteur de jeu, entierement data-driven (voir
  `rules_data.py`).
- `agricola2p/bots/` — trois bots: `RandomBot`, `HeuristicBot` (glouton 1 coup
  a l'avance) et `MCTSBot` (Monte Carlo Tree Search, UCB1).
- `agricola2p/cli.py` — fait jouer deux bots l'un contre l'autre en terminal.
- `tests/` — tests pytest (regles de la ferme, boucle de partie complete,
  bots).

## Installation rapide

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
```

## Jouer une partie bot vs bot

```bash
python3 -m agricola2p.cli --p1 heuristic --p2 mcts --iterations 200 --seed 1
```

Bots disponibles: `random`, `heuristic`, `mcts`.

## Utilisation programmatique

```python
from agricola2p.engine.game import AgricolaGame
from agricola2p.bots.mcts_bot import MCTSBot
from agricola2p.bots.heuristic_bot import HeuristicBot

game = AgricolaGame.new_game(seed=42)
bots = [HeuristicBot(seed=1), MCTSBot(iterations=300, seed=1)]

while not game.is_terminal():
    idx = game.current_player_idx
    action = bots[idx].choose_action(game, idx)
    game.apply(action)

print(game.scores())
```

## Fidelite aux regles officielles

Le ruleset implemente suit la synthese fournie par l'utilisateur (basee sur
une presentation d'Agricola: Terre d'Elevage), precisee ensuite en detail sur
le mecanisme central des clotures/enclos/batiments:

- **Partie en 8 tours**, chaque joueur disposant de **3 ouvriers** (6
  placements d'ouvrier au total par tour, en alternance stricte: joueur 1,
  joueur 2, joueur 1, ...). **1 seul ouvrier par case d'action**: une case
  occupee devient indisponible a l'autre joueur pour le reste du tour
  (`state.is_space_free`).
- **Jeton 1er joueur "collant"**: le 1er joueur d'une manche reste le meme
  d'une manche a l'autre par defaut. Prendre la case "Petit Bois"
  (`rules_data.FIRST_PLAYER_SPACE` — la synthese utilisateur dit juste
  "l'action bois" sans preciser laquelle, choix par analogie avec la case
  "1er joueur + 1 cereale" de l'Agricola classique) octroie le jeton 1er
  joueur pour la manche SUIVANTE a celui qui l'a prise, et il le garde tant
  que personne ne reprend cette case.
- **Plateau d'action precis** (17 cases, toutes disponibles des le tour 1,
  cf `rules_data.ACTION_SPACE_KIND`):
  - Ressources: Petit Bois (+1 bois/tour), Grand Bois (+2), Petite Pierre
    (+1 pierre/tour), Grande Pierre (+2), Roseau & Bois (+1 roseau +1 bois
    /tour) — chacune sa propre case, accumulant si non prise.
  - 1 case d'accumulation par espece animale (mouton/cochon/vache/cheval,
    +1/tour chacune).
  - **Clotures**: 2 cases distinctes — standard (1 bois/segment, illimite)
    et alternative (2 pierres pour les 2 premiers segments puis 1 pierre/
    segment supplementaire). Si la standard est prise, l'autre joueur peut
    toujours cloturer via l'alternative (plus chere). **Deux enclos voisins
    mutualisent** la barriere qui les separe (payee une seule fois — le
    moteur retient chaque arete deja cloturee). Les bords de la **maison**
    et des **batiments** (stalle/etable) font office de **murs naturels
    gratuits**. Une fois posee, une barriere/auge/batiment n'est plus
    jamais deplacee.
  - **Auges**: 2 cases distinctes — standard (la 1re auge de la visite est
    gratuite, puis 3 bois/auge supplementaire) et alternative (3 pierres/
    auge, jamais de gratuite). Une auge se pose sur **n'importe quelle case
    de terrain**, libre OU faisant partie d'un enclos, au maximum **1 auge
    par case** (pas de plafond arbitraire par enclos: la limite naturelle
    est le nombre de cases de l'enclos). Une case libre sans auge ne loge
    aucun animal (0), avec auge elle en loge 1. Une seule visite peut poser
    plusieurs auges a des emplacements differents (le moteur propose soit 1
    auge a un emplacement precis, soit toutes les auges possibles en une
    fois, plutot que d'enumerer tous les sous-ensembles).
  - **Agrandissement de ferme** (case dediee, 3 pierres + 1 roseau): achete
    directement 1 tuile d'extension de 3 cases (max 2 tuiles au total).
  - **Agrandissement ou amelioration** (5 bois OU 5 pierres au choix): au
    choix, achete 1 tuile d'extension, OU ameliore une Stalle en Etable/
    Etable ouverte, OU renove la maison en Maison a colombage.
  - **Batiment special**: 2 cases independantes, jusqu'a 2 batiments
    speciaux achetes par manche (un par case, cf pool ci-dessous).
  - **Construction d'une Stalle** (1 case): non listee dans la description
    fournie par l'utilisateur pour les cases d'action — conservee telle
    quelle car il faut bien un moyen de batir une premiere Stalle avant de
    pouvoir la remplacer par une Etable via "agrandissement ou
    amelioration" (voir limitations plus bas).
- **4 especes animales** (mouton, cochon, vache, cheval).
- **Plateau de depart**: grille 3x2 (2 cases maison + 4 cases ouvertes), avec
  jusqu'a **2 tuiles d'extension** de 3 cases chacune.
- **Capacite des enclos**: un enclos de N cases loge `N x 2` animaux de base,
  et ce nombre **double par auge** ajoutee (jusqu'a 3 auges -> `N x 16`). Une
  case non cloturee ne loge un animal que si elle est equipee d'une auge (1
  animal). Une **Stalle** (1 case, 3 bois + 1 pierre, 1 PV) loge 4 animaux
  sans cloture, et peut etre amelioree en **Etable** (2 PV, 5 animaux) ou
  **Etable ouverte** (2 PV, 4 animaux). Une auge sur un batiment ajoute +1
  animal.
- **Maison a colombage**: renovation de la maison de depart (+2 PV en fin de
  partie, aucune capacite animale).
- **Reproduction**: a la fin de **chaque** tour, tout groupe d'au moins 2
  animaux de la meme espece avec de la place produit 1 bebe supplementaire.
- **Batiments speciaux**: pool partage distinct (Bergerie, Porcherie, Puits,
  Carriere privee, Entrepot...), achetes contre ressources sans occuper de
  case de ferme, rapportent des PV directs et parfois un bonus. L'Entrepot
  rapporte +0.5 PV par ressource restante en reserve en fin de partie.
- **Score final**: `+1 PV` par animal, plus un **bareme par paliers propre a
  chaque espece** (malus fixe de -3 PV si moins de 4 animaux d'une espece,
  paliers croissants ensuite), plus les PV des batiments (stalle/etable,
  maison a colombage, batiments speciaux), plus **+4 PV par tuile
  d'extension entierement amenagee** (batiment, auge ou pature cloturee sur
  ses 3 cases) en fin de partie.
- **Egalite**: en cas de score final egal, le joueur qui n'a **pas** commence
  la toute premiere manche l'emporte.
- **Redeplacement des animaux**: les barrieres, auges et batiments sont fixes
  une fois poses (jamais deplaces), mais les **animaux** peuvent etre
  redispatches librement entre 2 emplacements deja construits (enclos,
  batiment ou case a auge) de sa propre ferme, en respectant toujours la
  regle d'**une seule espece par emplacement**. C'est une action gratuite
  (`kind="reorganize"`): elle n'occupe pas de case du plateau central et ne
  consomme pas le tour de l'ouvrier — le meme joueur peut donc reorganiser
  puis jouer normalement dans la foulee. Limitee a 1 redeplacement par tour
  d'ouvrier (donc jusqu'a 3 par manche et par joueur) pour rester bornee: le
  texte source dit "librement" sans preciser de frequence, et une limite
  explicite evite un espace de recherche illimite pour les bots tout en
  restant tres permissive en pratique (`agricola2p/engine/farmyard.py:
  move_animals`, `agricola2p/engine/actions.py: _reorganize_actions`).

**Ce qui reste une approximation** (la synthese fournie ne donne pas ces
details, donc des valeurs raisonnables ont ete choisies et sont centralisees
dans `rules_data.py` pour rester faciles a corriger):

- L'incrementation de la case "Roseau & Bois" (+1 roseau ET +1 bois par
  tour) suit la note "selon la variante" du texte source sans plus de
  precision.
- Les enclos sont des **rectangles** (pas de formes libres).
- Les tuiles d'extension ont une forme/un emplacement fixes choisis
  arbitrairement (2 tuiles de 3 cases), plutot que le systeme exact du jeu.
- Le pool de "batiments speciaux" (au-dela de l'Entrepot, donne en exemple)
  utilise des noms/couts/PV generiques plutot que la liste exacte du jeu
  physique.
- La construction d'une premiere Stalle (case dediee, 3 bois + 1 pierre)
  n'apparait pas dans la liste d'actions fournie par l'utilisateur: elle est
  conservee car le jeu a besoin d'un moyen d'en batir une avant de pouvoir la
  remplacer par une Etable.
- Le bot MCTS clone l'etat de jeu (y compris l'accumulation a venir, fixee au
  moment du clone): depuis un etat donne, la partie redevient donc a
  information parfaite, ce qui simplifie l'algorithme (MCTS classique plutot
  qu'un MCTS a information imparfaite/ISMCTS).

**Tout est centralise dans `agricola2p/engine/rules_data.py`** precisement
pour que ce soit facile a corriger: si une source plus precise est
disponible, il suffit d'ajuster les constantes/tables de ce fichier — aucun
autre module ne contient de valeur numerique "en dur". Le reste du moteur
(`farmyard.py`, `actions.py`, `game.py`) reste correct quelles que soient ces
valeurs.

## Prochaines etapes possibles

- Modeliser le redeplacement libre des animaux entre emplacements.
- Remplacer le pool generique de batiments speciaux et les tuiles
  d'extension par les vraies listes du jeu (texte + effet exact + formes).
- Autoriser des formes d'enclos non rectangulaires (clotures libres).
- Ajouter un bot par apprentissage par renforcement (self-play, type
  AlphaZero simplifie) une fois le moteur valide/ajuste par rapport au jeu
  physique — le `MCTSBot` actuel peut deja servir de generateur de parties
  d'entrainement.
- Interface graphique / web pour jouer contre un bot.
