"""Gestionnaire de base de données pour les fichiers PNACH PS2."""
import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class PS2GameInfo:
    name: str
    crc: str
    download_url: str
    description: str = ""

class PS2DatabaseManager:
    def __init__(self, config_file: str = "ps2_databases.json"):
        self.config_file = config_file
        self.games: List[PS2GameInfo] = [] 
        self.load_config()

    def load_config(self) -> None:
        """Charge la configuration de la base de données PS2."""
        if not os.path.exists(self.config_file):
            self.games = [] 
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.games = [] 
                for game_data in data.get('games', []):
                    crc_value = game_data.get('crc')
                    if isinstance(crc_value, str) and crc_value.strip(): 
                        game_data['crc'] = crc_value.strip().upper()
                    else:
                        original_name_for_log = game_data.get('name', 'NOM_MANQUANT')
                        print(f"Avertissement: CRC invalide ou manquant ('{crc_value}') pour le jeu '{original_name_for_log}'. Remplacé par 'INVALID_CRC'.")
                        game_data['crc'] = 'INVALID_CRC'
                    
                    # Assurer que 'name' est aussi une chaîne
                    name_value = game_data.get('name')
                    if not isinstance(name_value, str) or not name_value.strip():
                         game_data['name'] = f"[{game_data['crc']}] NO_NAME_SPECIFIED" # Utiliser le CRC (même si INVALID_CRC)
                    else:
                        game_data['name'] = name_value.strip()

                    self.games.append(PS2GameInfo(**game_data))
                        
            print(f"{len(self.games)} jeux chargés depuis la configuration JSON '{self.config_file}'.")

        except Exception as e:
            print(f"Erreur lors du chargement de la configuration : {e}")
            self.games = []

    def save_config(self) -> None:
        """Sauvegarde la configuration de la base de données PS2."""
        data = {
            'games': [
                {
                    'name': game.name,
                    'crc': game.crc,
                    'download_url': game.download_url,
                    'description': game.description,
                    # 'details_loaded': getattr(game, 'details_loaded', False) # Si vous ajoutez cet attribut
                }
                for game in self.games
            ]
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f: # Ligne 56 (environ)
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"Configuration sauvegardée dans '{self.config_file}'.")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration : {e}")

    def add_game(self, game: PS2GameInfo) -> bool:
        """Ajoute un nouveau jeu à la base de données."""
        if any(g.crc == game.crc for g in self.games):
            return False
        self.games.append(game)
        # self.save_config() # La sauvegarde sera gérée par l'appelant après un lot d'ajouts
        return True

    def clear_games(self):
        """Efface tous les jeux de la liste en mémoire et sauvegarde."""
        self.games = []
        self.save_config() # Sauvegarde la liste vide
        print("Liste des jeux effacée.")



    def get_game_by_crc(self, crc: str) -> Optional[PS2GameInfo]:
        """Récupère les informations d'un jeu par son CRC."""
        return next((game for game in self.games if game.crc == crc), None)

    def update_game(self, crc: str, game: PS2GameInfo) -> bool:
        """Met à jour les informations d'un jeu en modifiant l'objet en place."""
        for existing_game in self.games:
            if existing_game.crc == crc:
                existing_game.name = game.name
                existing_game.download_url = game.download_url
                existing_game.description = game.description
                self.save_config() # Sauvegarde les changements si un jeu est mis à jour
                return True
        return False

    def get_all_games(self) -> List[PS2GameInfo]:
        """Récupère la liste de tous les jeux."""
        # Le tri doit être géré par la vue (ex: QSortFilterProxyModel)
        return self.games 




