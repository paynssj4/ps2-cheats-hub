# ps2_database_frame_qt.py

"""
Interface moderne pour la gestion de la base de donnÃ©es PS2 (PySide6).
"""
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableView, QHeaderView, QMessageBox, QAbstractItemView, QGroupBox, QScrollArea
)
from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QThread, Signal, QMetaObject, Q_ARG, QSortFilterProxyModel, QTimer, Slot
from PySide6.QtGui import QPalette, QColor, QClipboard
from ps2_database_manager import PS2DatabaseManager, PS2GameInfo
from ps2_github_handler import list_pnach_files, fetch_pnach_content, extract_gametitle_from_pnach_content
from PySide6.QtWidgets import QFileDialog
import sys
import threading
from PySide6.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QHBoxLayout, QPushButton, QDialogButtonBox


class PnachViewerDialog(QDialog):
    def __init__(self, game_name, game_crc, pnach_content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"PNACH - {game_name} [{game_crc}]")
        self.setMinimumSize(600, 400)

        self.game_crc = game_crc
        self.pnach_content = pnach_content

        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setText(pnach_content)
        layout.addWidget(self.text_edit)

        button_layout = QHBoxLayout()
        
        copy_button = QPushButton("Copier tout")
        copy_button.clicked.connect(self.copy_content)
        button_layout.addWidget(copy_button)

        extract_button = QPushButton("Extraire en .pnach")
        extract_button.clicked.connect(self.extract_pnach)
        button_layout.addWidget(extract_button)

        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)

    def copy_content(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())
        QMessageBox.information(self, "Copié", "Contenu du PNACH copié dans le presse-papiers.")

    def extract_pnach(self):
        default_filename = f"{self.game_crc}.pnach"
        filepath, _ = QFileDialog.getSaveFileName(
            self, 
            "Sauvegarder le fichier PNACH", 
            default_filename, 
            "Fichiers PNACH (*.pnach);;Tous les fichiers (*.*)"
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(self.pnach_content)
                QMessageBox.information(self, "Succès", f"Fichier PNACH sauvegardé:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur de Sauvegarde", f"Impossible de sauvegarder le fichier PNACH:\n{e}")

class GameTableModel(QAbstractTableModel):
    model_updated_and_ready_for_fetch = Signal()
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.games = self.db_manager.get_all_games()
        self.headers = ["Nom du jeu", "CRC"]

    def rowCount(self, parent=QModelIndex()):
        return len(self.games)

    def columnCount(self, parent=QModelIndex()):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        game = self.games[index.row()]
        if role == Qt.DisplayRole:
            if index.column() == 0:
                return game.name
            elif index.column() == 1:
                return game.crc
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid() or index.column() != 0:
            return False
        if role == Qt.EditRole:
            game = self.games[index.row()]
            if game.name != value:
                game.name = value
                self.dataChanged.emit(index, index, [Qt.DisplayRole])
                return True
        return False

    def flags(self, index):
        base_flags = super().flags(index)
        return base_flags


    @Slot()

    def update_all(self):
        print("[TableModel] update_all called.")

        self.games = self.db_manager.get_all_games()
        self.beginResetModel()
        self.endResetModel()
        print(f"[TableModel] Model reset. Number of games in model: {len(self.games)}")
        self.model_updated_and_ready_for_fetch.emit()


class GameFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_text = ""

    def setFilterText(self, text):
        self.filter_text = text.lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        game = model.games[source_row]
        return self.filter_text in game.name.lower() or self.filter_text in game.crc.lower()

class PS2DatabaseWindow(QMainWindow):
    def __init__(self, db_manager: PS2DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.setWindowTitle("Gestion Base de Données PS2 (moderne)")
        self.setMinimumSize(700, 500)
        self._apply_dark_theme()
        self._init_ui()
        self._initial_load_pending_fetch = False
        self._names_updated_by_thread = False
        self.is_fetching_names = False


    def _apply_dark_theme(self):
        app = QApplication.instance()
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(40, 40, 40))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(45, 45, 45))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Highlight, QColor(60, 120, 200))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        app.setPalette(palette)

    def _init_ui(self):
        central = QWidget()
        layout = QVBoxLayout(central)
        db_group = QGroupBox("Configuration Base de Données")
        db_layout = QVBoxLayout(db_group)
        url_layout = QHBoxLayout()
        url_label = QLabel("URL GitHub:")
        self.url_edit = QLineEdit("https://github.com/paynssj4/pcsx2_cheats_collection/tree/main/cheats")
        self.url_edit.setMinimumWidth(400)
        reset_btn = QPushButton("Réinitialiser")
        reset_btn.clicked.connect(lambda: self.url_edit.setText("https://github.com/paynssj4/pcsx2_cheats_collection"))
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_edit)
        url_layout.addWidget(reset_btn)
        db_layout.addLayout(url_layout)
        btn_layout = QHBoxLayout()
        self.load_btn = QPushButton("Charger Base de Données")
        self.load_btn.clicked.connect(self.load_database)
        btn_layout.addWidget(self.load_btn)
        self.show_names_btn = QPushButton("Afficher les noms")
        self.show_names_btn.setEnabled(False)
        self.show_names_btn.clicked.connect(self._start_background_name_fetching)
        

        btn_layout.addWidget(self.show_names_btn)
        self.status_label = QLabel("")
        btn_layout.addWidget(self.status_label)
        db_layout.addLayout(btn_layout)
        layout.addWidget(db_group)
        search_group = QGroupBox("Recherche de Jeux")
        search_layout = QHBoxLayout(search_group)
        search_label = QLabel("Rechercher:")
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.filter_games)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit)
        layout.addWidget(search_group)
        self.table_model = GameTableModel(self.db_manager)
        self.proxy_model = GameFilterProxy()
        self.proxy_model.setSourceModel(self.table_model)
        self.table_view = QTableView()
        self.table_view.setModel(self.proxy_model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.doubleClicked.connect(self.on_game_double_click)
        layout.addWidget(self.table_view)
        self.setCentralWidget(central)
        self.table_model.model_updated_and_ready_for_fetch.connect(self._on_model_updated_for_fetching)

    def filter_games(self):
        text = self.search_edit.text()
        self.proxy_model.setFilterText(text)

    def on_game_double_click(self, proxy_clicked_index):
        if not proxy_clicked_index.isValid():
            return
        source_index = self.proxy_model.mapToSource(proxy_clicked_index)
        if not source_index.isValid():

            return

        game_info = self.table_model.games[source_index.row()]

        self.status_label.setText(f"Chargement PNACH pour {game_info.name}...")
        QApplication.processEvents()



        try:
            content = fetch_pnach_content(game_info.download_url)
            if content:
                dialog = PnachViewerDialog(game_info.name, game_info.crc, content, self)
                dialog.exec()
            else:
                QMessageBox.warning(self, "Erreur PNACH", f"Impossible de charger le contenu PNACH pour {game_info.name}.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur PNACH", f"Erreur lors du chargement du PNACH:\n{e}")
        finally:
            self.status_label.setText("")


    def set_and_refresh_game_name(self, crc, new_name):
        print(f"[UI] Mise à jour du nom pour {crc} : {new_name}")
        game_to_update = self.db_manager.get_game_by_crc(crc)
        if game_to_update:
            source_row = -1
            for row, game in enumerate(self.table_model.games):
                if game.crc == crc:
                    source_row = row
                    break
            if source_row != -1:

                model_index = self.table_model.index(source_row, 0)


                self.table_model.setData(model_index, new_name, Qt.EditRole)
                self._names_updated_by_thread = True
            else:
                print(f"[UI] Avertissement: Jeu avec CRC {crc} non trouvé dans le modèle pour mise à jour visuelle.")
        self.status_label.setText(f"Nom mis à jour pour {crc} : {new_name}")
    @Slot(str, str)

    def update_game_name_in_main_thread(self, crc, game_title):
        self.set_and_refresh_game_name(crc, game_title)
        self.status_label.setText(f"Nom mis à jour pour {crc} : {game_title}")
    @Slot(str)
    def show_success_message(self, msg):
        QMessageBox.information(self, "Succès", msg)
    @Slot(str)
    def show_error_message(self, msg):
        QMessageBox.critical(self, "Erreur", msg)

    def load_database(self):
        self.status_label.setText("Chargement en cours...")
        self.load_btn.setEnabled(False)
        self.show_names_btn.setEnabled(False)
        QApplication.processEvents()
        url = self.url_edit.text().strip()
        if not url.startswith("https://github.com/"):
            QMessageBox.critical(self, "Erreur", "L'URL doit être un lien GitHub valide")
            self.status_label.setText("Erreur URL")
            self.load_btn.setEnabled(True)
            return
        parts = url.replace("https://github.com/", "").split("/")
        if len(parts) < 2:
            QMessageBox.critical(self, "Erreur", "URL GitHub invalide. Format attendu: https://github.com/owner/repo[/tree/branch/path]")
            self.status_label.setText("Erreur URL")
            self.load_btn.setEnabled(True)
            return
        
        repo_owner, repo_name = parts[0], parts[1]
        branch = "main"
        path_in_repo = ""

        if '/tree/' in url:
            branch = parts[3]
            if len(parts) > 4:
                path_in_repo = "/".join(parts[4:])
        else:
            pass
        
        self.status_label.setText(f"Connexion à {repo_owner}/{repo_name}...")
        QApplication.processEvents()
        self.db_manager.clear_games()
        def fetch():
            initial_save_needed = False
            try:
                games = list_pnach_files(repo_owner, repo_name, path_in_repo=path_in_repo, branch=branch)
                if not games:
                    QMetaObject.invokeMethod(self, "show_error_message", Qt.QueuedConnection,
                                             Q_ARG(str, "Aucun fichier PNACH trouvé ou erreur d'accès."))
                    QMetaObject.invokeMethod(self.status_label, "setText", Qt.QueuedConnection,
                                             Q_ARG(str, "Aucun jeu trouvé."))
                    QMetaObject.invokeMethod(self.show_names_btn, "setEnabled", Qt.QueuedConnection, Q_ARG(bool, False))
                else:
                    for game_info_dict in games:
                        if self.db_manager.add_game(PS2GameInfo(
                            name=game_info_dict['name'],
                            crc=game_info_dict['crc'],
                            download_url=game_info_dict['download_url']
                        )):
                            initial_save_needed = True
                    
                    self._initial_load_pending_fetch = True
                    QMetaObject.invokeMethod(self.table_model, "update_all", Qt.QueuedConnection)

                    QMetaObject.invokeMethod(self.status_label, "setText", Qt.QueuedConnection,
                                             Q_ARG(str, f"{len(games)} jeux chargés depuis GitHub."))

                    if initial_save_needed:
                        self.db_manager.save_config()

                    QMetaObject.invokeMethod(self, "show_success_message", Qt.QueuedConnection,
                                             Q_ARG(str, f"{len(games)} jeux ont été chargés depuis GitHub."))
                    QMetaObject.invokeMethod(self.show_names_btn, "setEnabled", Qt.QueuedConnection, Q_ARG(bool, True))
                    


            except Exception as e:
                QMetaObject.invokeMethod(self, "show_error_message", Qt.QueuedConnection,
                                         Q_ARG(str, f"Erreur lors du chargement de la base de données:\n{str(e)}"))
                QMetaObject.invokeMethod(self.status_label, "setText", Qt.QueuedConnection,
                                         Q_ARG(str, "Erreur lors du chargement"))
                QMetaObject.invokeMethod(self.show_names_btn, "setEnabled", Qt.QueuedConnection, Q_ARG(bool, False))

            finally:
                QMetaObject.invokeMethod(self.load_btn, "setEnabled", Qt.QueuedConnection, Q_ARG(bool, True))
        threading.Thread(target=fetch, daemon=True).start()

    @Slot()
    def _on_model_updated_for_fetching(self):
        print("[UI] _on_model_updated_for_fetching called.")
        if self._initial_load_pending_fetch:
            print("[UI] Initial load was pending, now starting background name fetching.")
            self._initial_load_pending_fetch = False
            if self.db_manager.games and not self.is_fetching_names:
                self._start_background_name_fetching()
            elif self.is_fetching_names:
                print("[UI] Background name fetching already in progress, not starting again.")
            elif not self.db_manager.games:
                print("[UI] No games in db_manager, not starting background name fetching.")
        else:
            print("[UI] Model updated, but no initial load was pending for name fetching.")


    def _start_background_name_fetching(self):
        print("[UI] _start_background_name_fetching called.")

        if self.is_fetching_names:
            self.status_label.setText("Récupération des noms déjà en cours.")
            print("[UI] Fetching already in progress.")

            return
        if not self.db_manager.get_all_games():
            self.status_label.setText("Aucun jeu chargé pour récupérer les noms.")
            print("[UI] No games loaded to fetch names for.")

            return

        self.is_fetching_names = True
        self.show_names_btn.setEnabled(False)
        self.load_btn.setEnabled(False)
        self.status_label.setText("Récupération des noms en arrière-plan...")
        QApplication.processEvents()
        self._names_updated_by_thread = False
        
        threading.Thread(target=self._background_name_fetch_worker, daemon=True).start()

    def _background_name_fetch_worker(self):

        all_games = self.db_manager.get_all_games()
        for game_info in list(all_games):
            if not game_info.crc or game_info.crc == "INVALID_CRC":
                print(f"[BG Fetch] CRC invalide ou manquant pour le jeu '{game_info.name}', ignoré.")
                continue
            is_placeholder = (
                game_info.name.endswith("Loading...") or
                "Cliquez pour charger les détails" in game_info.name
            )
            if not is_placeholder:
                continue
            
            print(f"[BG Fetch] Extraction du nom pour {game_info.crc} ({game_info.name})...")
            content = fetch_pnach_content(game_info.download_url)
            if content:
                game_title = extract_gametitle_from_pnach_content(content)
                if game_title and game_title != game_info.name:
                    print(f"[BG Fetch] Nom trouvé pour {game_info.crc} : {game_title}")
                    QMetaObject.invokeMethod(self, "update_game_name_in_main_thread", Qt.QueuedConnection,
                                             Q_ARG(str, game_info.crc), Q_ARG(str, game_title))

        QMetaObject.invokeMethod(self, "_execute_final_cleanup_for_name_fetching", Qt.QueuedConnection)

    @Slot()
    def _execute_final_cleanup_for_name_fetching(self):
        """Exécute le nettoyage final après la récupération des noms, dans le thread principal."""
        print("[UI Thread] Running final cleanup for name fetching.")
        if self._names_updated_by_thread:
            print("[UI Thread] Saving configuration as names were updated by thread.")
            self.db_manager.save_config()
            self._names_updated_by_thread = False
        
        self.status_label.setText("Récupération des noms terminée.")
        
        has_games = bool(self.db_manager.games)
        self.show_names_btn.setEnabled(has_games)
        self.load_btn.setEnabled(True)
        self.is_fetching_names = False







if __name__ == "__main__":
    app = QApplication(sys.argv)
    db_manager = PS2DatabaseManager()
    win = PS2DatabaseWindow(db_manager)
    win.show()
    sys.exit(app.exec())