import requests
import urllib.parse
import re
from typing import Tuple, Optional, List, Dict

def _extract_true_crc_from_filename(filename_str: Optional[str]) -> Optional[str]:
    """
    Tente d'extraire un CRC hexadécimal à 8 chiffres d'un nom de fichier.
    Gère les formats comme "GAMEID_CRC.pnach", "CRC.pnach", "CRC - Name.pnach".
    """
    if not isinstance(filename_str, str) or not filename_str.strip():
        return None

    s = filename_str.strip().upper()
    if s.endswith(".PNACH"):
        s = s[:-6]

    if '_' in s:
        potential_crc = s.split('_')[-1]
        if len(potential_crc) == 8 and all(c in "0123456789ABCDEF" for c in potential_crc):
            return potential_crc

    if len(s) == 8 and all(c in "0123456789ABCDEF" for c in s):
        return s
    return None

def get_github_directory_listing(repo_owner, repo_name, path="cheats", branch="main"):
    """Récupère la liste des fichiers/dossiers à un chemin donné dans le dépôt."""
    clean_path = path.strip('/')
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{clean_path}?ref={branch}"

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération de la liste depuis {api_url}: {e}")
        return None
    except ValueError as e:
        print(f"Erreur lors du décodage JSON pour {api_url}: {e}")
        return None

def extract_gametitle_from_pnach_content(pnach_content: str) -> Optional[str]:
    """Extrait le gametitle du contenu PNACH."""
    if not pnach_content:
        return None
    for line in pnach_content.splitlines():
        if line.startswith("gametitle="):
            return line[10:].strip()
    return None

def extract_info_from_filename(
    filename: str, 
    file_format_regex_str: Optional[str], 
    default_game_name_pattern: str
) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Extrait le nom du jeu, le CRC et le GameID à partir du nom de fichier PNACH.
    Retourne: (nom_jeu, crc, game_id)
    """
    game_name = ""
    crc = None
    game_id = None

    if file_format_regex_str:
        match = re.match(file_format_regex_str, filename, re.IGNORECASE)
        if match:
            group_dict = match.groupdict()
            crc = group_dict.get('crc')
            game_name = group_dict.get('title', '') or group_dict.get('name', '')
            game_id = group_dict.get('gameid')
            
            if crc:
                crc = crc.upper()
            if game_id:
                game_id = game_id.upper()
            
            if not game_name and crc:
                game_name = default_game_name_pattern.format(crc_8=crc, game_id=game_id if game_id else "N/A")
            elif not game_name and not crc:
                 game_name = filename
            
            return game_name, crc, game_id

    name_part = filename
    if name_part.lower().endswith('.pnach'):
        name_part = name_part[:-6]

    if len(name_part) == 8 and all(c in "0123456789ABCDEFabcdef" for c in name_part):
        crc = name_part.upper()
        game_name = default_game_name_pattern.format(crc_8=crc, game_id="N/A")
        return game_name, crc, None

    if len(name_part) > 8 and name_part[8] in [' ', '-', '_'] and all(c in "0123456789ABCDEFabcdef" for c in name_part[:8]):
        crc = name_part[:8].upper()
        remaining_part = name_part[9:].strip()
        
        game_id_match = re.search(r'[\(\[]([A-Z]{4}[-_]?\d{5}(?:\.\d{2})?)[)\]]', remaining_part, re.IGNORECASE)
        if game_id_match:
            game_id_full = game_id_match.group(1).upper()
            game_id = re.sub(r'[-_.]', '', game_id_full)
            
            game_name = re.sub(r'\s*[\(\[]' + re.escape(game_id_full) + r'[)\]]', '', remaining_part, flags=re.IGNORECASE).strip()
        else:
            game_name = remaining_part
        
        if not game_name and crc:
            game_name = default_game_name_pattern.format(crc_8=crc, game_id=game_id if game_id else "N/A")
        return game_name, crc, game_id

    return name_part, None, None

def list_pnach_files(repo_owner: str, repo_name: str, path_in_repo: str = "cheats", branch: str = "main") -> List[Dict[str, any]]:
    """Liste tous les fichiers PNACH avec leurs infos."""
    games = []
    listing = get_github_directory_listing(repo_owner, repo_name, path=path_in_repo, branch=branch)
    if listing:
        for item in listing:
            if item['type'] == 'file' and item['name'].lower().endswith('.pnach'):

                true_crc = _extract_true_crc_from_filename(item['name'])
                
                initial_name = f"[{true_crc}] Loading..." if true_crc else f"[{item['name'][:-6]}] Loading..."
                if not true_crc:
                    print(f"Avertissement GitHub: CRC non extractible de '{item['name']}'. Utilisation de 'NO_CRC'.")
                
                games.append({
                    'filename': item['name'],
                    'crc': true_crc if true_crc else "NO_CRC",
                    'name': initial_name,
                    'download_url': item['download_url'],
                    'details_loaded': False
                })
    return sorted(games, key=lambda x: x.get('crc') or x['filename'])

def fetch_pnach_content(download_url):
    """Télécharge le contenu d'un fichier PNACH."""
    try:
        response = requests.get(download_url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors du téléchargement du fichier {download_url}: {e}")
        return None

def update_game_names(games):
    """Met à jour les noms des jeux en lisant les fichiers PNACH."""
    for game in games:
        content = fetch_pnach_content(game['download_url'])
        if content:
            game_title = extract_gametitle_from_pnach_content(content)
            if game_title:
                game['name'] = game_title
            else:
                game['name'] = f"Unknown Game [{game['crc']}]"
    return games
