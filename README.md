# PS2 Cheats Hub

PS2 Cheats Hub est une application de bureau conçue pour aider à la gestion et à la conversion de codes de triche pour les jeux PlayStation 2.
L'application fournit une interface graphique pour décrypter les codes Action Replay MAX (ARMAX) et Action Replay 2 / Gameshark 2 (AR2/GS2), les afficher au format brut et les convertir au format PNACH.

## Fonctionnalités Principales

*   Décryptage des codes de triche ARMAX.
*   Décryptage des codes de triche AR2/GS2.
*   Affichage des codes décryptés au format RAW (adresse/valeur).
*   Génération de fichiers PNACH à partir des codes décryptés, incluant la possibilité d'ajouter des descriptions et le titre/CRC du jeu.
*   Intégration d'une base de données de jeux PS2 pour faciliter la recherche d'informations
*   Possibilité de récupérer des informations PNACH depuis GitHub

## Fichiers et Dépendances du Projet

Ce projet est composé des principaux fichiers Python suivants :

*   `ps2_cheats_hub_qt.py`: Le script principal de l'application avec l'interface utilisateur.
*   `ps2_database_manager.py`: Gère la logique de la base de données des jeux.
*   `ps2_database_frame_qt.py`: Fournit l'interface utilisateur pour la section base de données.
*   `armax_ps2_logic.py`: Contient la logique de décryptage pour les codes ARMAX.
*   `ar2_ps2_logic.py`: Contient la logique de décryptage pour les codes AR2/GS2.
*   `ps2_github_handler.py`: Gère la récupération de données PNACH depuis GitHub.

Dépendances externes notables :
*   **PySide6**: Utilisé pour l'interface graphique.

## Compilation avec Nuitka

Pour compiler `ps2_cheats_hub_qt.py` et ses dépendances en un exécutable unique sous Windows, vous pouvez utiliser Nuitka. Assurez-vous que Nuitka, PySide6 et un compilateur C compatible (comme MinGW ou celui fourni avec Visual Studio) sont installés dans votre environnement Python.

Placez tous les fichiers `.py` listés ci-dessus dans le même répertoire. La commande de base pour la compilation est la suivante :

```bash
python -m nuitka --onefile --windows-disable-console --enable-plugin=pyside6 ps2_cheats_hub_qt.py
```

Nuitka tentera de suivre les imports pour inclure les autres fichiers `.py` nécessaires. L'option `--onefile` crée un seul exécutable autonome. L'option `--windows-disable-console` masque la fenêtre de terminal lors de l'exécution.

## Licence

Ce projet est basé sur le travail original de **parasyte (ou pyriell)** et est distribué sous les termes de la **Licence Publique Générale GNU (GNU GPL)**. Il est recommandé de consulter le fichier de licence spécifique (par exemple, `LICENSE` ou `COPYING`) inclus avec les sources originales.

## Remerciements

*   ce programme est inspiré du travail de **parasyte (pyriell)** pour le travail original sur la logique de décryptage des codes PS2.
