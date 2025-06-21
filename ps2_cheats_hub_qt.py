"""
Fenêtre principale moderne et 100% sombre pour PS2 Cheats Hub (PySide6).
"""
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableView, QHeaderView, QComboBox, QTextEdit, QSplitter, QMessageBox, QFileDialog, QInputDialog, QGroupBox
)
from PySide6.QtCore import Qt
from ps2_database_manager import PS2DatabaseManager, PS2GameInfo
from ps2_database_frame_qt import PS2DatabaseWindow, GameTableModel
from armax_ps2_logic import armax_batch_decrypt_full_python, FILTER_CHARS
from ar2_ps2_logic import ar2_set_seed, ar2_batch_decrypt_arr, AR1_SEED
from ps2_github_handler import fetch_pnach_content
import sys
import os

class PS2CheatsHubQt(QMainWindow):
    def __init__(self, db_manager: PS2DatabaseManager):
        super().__init__()
        self.setWindowTitle("PS2 Cheats Hub - Moderne (Qt)")
        self.setMinimumSize(900, 600)
        self.db_manager = db_manager
        self._apply_dark_theme()
        self._init_ui()
        self.current_decrypted_items = []

    def _apply_dark_theme(self):
        app = QApplication.instance()
        app.setStyle("Fusion")
        from PySide6.QtGui import QPalette, QColor
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
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        db_panel = QWidget()
        db_layout = QVBoxLayout(db_panel)
        self.db_widget = PS2DatabaseWindow(self.db_manager)
        db_layout.addWidget(self.db_widget.centralWidget())
        splitter.addWidget(db_panel)
        decrypt_panel = QWidget()
        decrypt_layout = QVBoxLayout(decrypt_panel)
        code_type_group = QGroupBox("Type de Code")
        code_type_layout = QHBoxLayout(code_type_group)
        self.code_type_combo = QComboBox()
        self.code_type_combo.addItems(["ARMAX", "AR2/GS2"])
        code_type_layout.addWidget(QLabel("Type:"))
        code_type_layout.addWidget(self.code_type_combo)
        decrypt_layout.addWidget(code_type_group)
        input_group = QGroupBox("Codes Cryptés")
        input_layout = QVBoxLayout(input_group)
        self.txt_encrypted = QTextEdit()
        input_layout.addWidget(self.txt_encrypted)
        decrypt_layout.addWidget(input_group)
        raw_group = QGroupBox("Codes RAW Décryptés")
        raw_layout = QVBoxLayout(raw_group)
        self.txt_decrypted_raw = QTextEdit()
        self.txt_decrypted_raw.setReadOnly(True)
        raw_layout.addWidget(self.txt_decrypted_raw)
        decrypt_layout.addWidget(raw_group)
        pnach_group = QGroupBox("Format PNACH")
        pnach_layout = QVBoxLayout(pnach_group)
        self.txt_pnach = QTextEdit()
        self.txt_pnach.setReadOnly(True)
        pnach_layout.addWidget(self.txt_pnach)
        decrypt_layout.addWidget(pnach_group)
        btn_layout = QHBoxLayout()
        self.btn_decrypt = QPushButton("Décrypter")
        self.btn_decrypt.clicked.connect(self.process_decryption)
        btn_layout.addWidget(self.btn_decrypt)
        self.btn_clear = QPushButton("Effacer")
        self.btn_clear.clicked.connect(self.clear_fields)
        btn_layout.addWidget(self.btn_clear)
        self.btn_export = QPushButton("Exporter en .pnach")
        self.btn_export.clicked.connect(self.export_to_pnach)
        self.btn_export.setEnabled(False)
        btn_layout.addWidget(self.btn_export)
        decrypt_layout.addLayout(btn_layout)
        splitter.addWidget(decrypt_panel)
        self.setCentralWidget(splitter)

    def process_decryption(self):
        code_type = self.code_type_combo.currentText()
        encrypted_codes_input = self.txt_encrypted.toPlainText().strip()
        self.current_decrypted_items = []
        self.txt_decrypted_raw.clear()
        self.txt_pnach.clear()
        self.btn_export.setEnabled(False)
        if not encrypted_codes_input:
            QMessageBox.warning(self, "Aucun code", f"Veuillez entrer des codes {code_type} à décrypter.")
            return
        input_lines = encrypted_codes_input.splitlines()
        try:
            if code_type == "ARMAX":
                decrypted_raw_display_lines = self._process_armax_codes(input_lines)
            else:
                decrypted_raw_display_lines = self._process_ar2_codes(input_lines)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du décryptage : {str(e)}")
            return
        
        self.txt_decrypted_raw.setPlainText("\n".join(decrypted_raw_display_lines))
        
        if self.current_decrypted_items:
            pnach_output_lines = self._generate_pnach_lines(self.current_decrypted_items)
            self.txt_pnach.setPlainText("\n".join(pnach_output_lines))

            self.btn_export.setEnabled(True)

    def _process_armax_codes(self, input_lines):
        raw_output_lines = ["--- Codes ARMAX Décryptés ---"]
        processed_items_for_pnach = []
        
        current_description = None
        armax_codes_to_decrypt_batch = []
        descriptions_for_codes_in_batch = []

        for line_num, line in enumerate(input_lines, 1):
            cleaned_line = line.strip()
            if not cleaned_line:
                continue
            code_candidate = cleaned_line.upper().replace("-", "")
            is_valid_armax = len(code_candidate) == 13 and all(c in FILTER_CHARS for c in code_candidate)

            if is_valid_armax:
                armax_codes_to_decrypt_batch.append(code_candidate)
                descriptions_for_codes_in_batch.append(current_description)
                current_description = None
            else:
                current_description = cleaned_line

        if not armax_codes_to_decrypt_batch:
            if current_description:
                raw_output_lines.append(f"// {current_description} (Aucun code valide trouvé après cette description)")
            self.current_decrypted_items = []
            return raw_output_lines

        ar2_key_for_ps2 = 0x04030209
        success, decrypted_pairs_batch, game_id, region = armax_batch_decrypt_full_python(armax_codes_to_decrypt_batch, ar2_key_for_ps2)

        if not success:
            raw_output_lines.append("ERREUR LORS DU DECRYPTAGE ARMAX BATCH.")
            for i, (addr, val) in enumerate(decrypted_pairs_batch):
                desc_for_this_code = descriptions_for_codes_in_batch[i]
                if desc_for_this_code:
                    raw_output_lines.append(f"// {desc_for_this_code} (Code original: {armax_codes_to_decrypt_batch[i]})")
                raw_output_lines.append(f"{addr:08X} {val:08X} (potentiellement incorrect)")
            self.current_decrypted_items = []
            return raw_output_lines

        for i, (addr, val) in enumerate(decrypted_pairs_batch):
            desc_for_this_code = descriptions_for_codes_in_batch[i]
            if desc_for_this_code:
                raw_output_lines.append(f"// {desc_for_this_code}")
            raw_output_lines.append(f"{addr:08X} {val:08X}")
            processed_items_for_pnach.append((desc_for_this_code, addr, val))
        
        self.current_decrypted_items = processed_items_for_pnach
        return raw_output_lines


    def _process_ar2_codes(self, input_lines):
        raw_output_lines = [f"--- Codes AR2/GS2 Décryptés (Seed: {AR1_SEED:08X}) ---"]
        processed_items_for_pnach = []
        
        current_description = None
        ar2_codes_to_decrypt_batch_u32 = []
        descriptions_for_code_pairs_in_batch = []
        for line_num, line in enumerate(input_lines, 1):
            cleaned_line = line.strip()
            if not cleaned_line:
                continue
            
            parts = cleaned_line.split()
            is_valid_ar2 = False
            addr, val = 0, 0
            if len(parts) == 2:
                try:
                    addr = int(parts[0], 16)
                    val = int(parts[1], 16)
                    if not (0 <= addr <= 0xFFFFFFFF and 0 <= val <= 0xFFFFFFFF):
                        raise ValueError("Hors plage u32")
                    is_valid_ar2 = True
                except ValueError:
                    is_valid_ar2 = False
            
            if is_valid_ar2:
                ar2_codes_to_decrypt_batch_u32.extend([addr, val])
                descriptions_for_code_pairs_in_batch.append(current_description)
                current_description = None
            else:
                current_description = cleaned_line

        if not ar2_codes_to_decrypt_batch_u32:
            if current_description:
                raw_output_lines.append(f"// {current_description} (Aucun code valide trouvé après cette description)")
            self.current_decrypted_items = []
            return raw_output_lines

        working_codes_copy = list(ar2_codes_to_decrypt_batch_u32)
        ar2_set_seed(AR1_SEED)
        decrypted_size_u32 = ar2_batch_decrypt_arr(working_codes_copy)

        if decrypted_size_u32 <= 0 and ar2_codes_to_decrypt_batch_u32:
            raw_output_lines.append("ERREUR ou aucun code de données après décryptage AR2/GS2.")
            original_pair_idx = 0
            for i in range(0, len(ar2_codes_to_decrypt_batch_u32), 2):
                desc = descriptions_for_code_pairs_in_batch[original_pair_idx]
                if desc:
                    raw_output_lines.append(f"// {desc}")
                raw_output_lines.append(f"{ar2_codes_to_decrypt_batch_u32[i]:08X} {ar2_codes_to_decrypt_batch_u32[i+1]:08X} (non décrypté ou clé)")
                original_pair_idx += 1
            self.current_decrypted_items = []
            return raw_output_lines

              
        desc_idx = 0
        for i in range(0, decrypted_size_u32, 2):
            if i + 1 < decrypted_size_u32:
                dec_addr, dec_val = working_codes_copy[i], working_codes_copy[i+1]
                

                desc_for_this_pair = None
                if desc_idx < len(descriptions_for_code_pairs_in_batch):
                    desc_for_this_pair = descriptions_for_code_pairs_in_batch[desc_idx]
                
                if desc_for_this_pair:
                    raw_output_lines.append(f"// {desc_for_this_pair}")
                raw_output_lines.append(f"{dec_addr:08X} {dec_val:08X}")
                processed_items_for_pnach.append((desc_for_this_pair, dec_addr, dec_val))
                desc_idx +=1

        self.current_decrypted_items = processed_items_for_pnach
        return raw_output_lines

    def _generate_pnach_lines(self, items_with_desc):
        lines = [
            "gametitle=Nom du Jeu Ici [SLUS_XXX.XX/SLES_XXX.XX]",
            "comment=Codes générés par PS2 Cheats Hub",
            ""
        ]
        for desc, addr, val in items_with_desc:
            if desc:
                lines.append(f"// {desc}")
            lines.append(f"patch=1,EE,{addr:08X},extended,{val:08X}")
        return lines

    def export_to_pnach(self):
        if not self.current_decrypted_items:
            QMessageBox.warning(self, "Aucun code", "Aucun code décrypté à exporter.")
            return
        
        game_title_input, ok_title = QInputDialog.getText(self, "Nom du Jeu pour PNACH",
                                                          "Entrez le nom complet du jeu (ex: Final Fantasy X [SLUS_203.12]):")
        if not ok_title or not game_title_input.strip():
            QMessageBox.information(self, "Annulé", "Exportation PNACH annulée (nom du jeu manquant).")
            return

        game_crc_input, ok_crc = QInputDialog.getText(self, "CRC du Jeu pour PNACH",
                                                      "Entrez le CRC hexadécimal à 8 chiffres du jeu (ex: A1B2C3D4):")
        if not ok_crc or not game_crc_input.strip():
            QMessageBox.information(self, "Annulé", "Exportation PNACH annulée (CRC manquant).")
            return

        game_crc_cleaned = game_crc_input.strip().upper()
        if not (len(game_crc_cleaned) == 8 and all(c in "0123456789ABCDEF" for c in game_crc_cleaned)):
            QMessageBox.critical(self, "CRC Invalide", "Le CRC doit être une chaîne hexadécimale de 8 caractères.")
            return

        pnach_content_lines = [f"gametitle={game_title_input.strip()}"]
        pnach_content_lines.append(self._generate_pnach_lines(self.current_decrypted_items)[1])
        pnach_content_lines.append("")
        for desc, addr, val in self.current_decrypted_items:
            if desc:
                pnach_content_lines.append(f"// {desc}")
            pnach_content_lines.append(f"patch=1,EE,{addr:08X},extended,{val:08X}")

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Sauvegarder le fichier PNACH",
            f"{game_crc_cleaned}.pnach",
            "Fichiers PNACH (*.pnach);;Tous les fichiers (*)"
        )

        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write("\n".join(pnach_content_lines))
                QMessageBox.information(self, "Succès", f"Fichier PNACH sauvegardé avec succès:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur de Sauvegarde", f"Impossible de sauvegarder le fichier PNACH:\n{e}")

    def clear_fields(self):
        self.txt_encrypted.clear()
        self.txt_decrypted_raw.clear()
        self.txt_pnach.clear()
        self.current_decrypted_items = []
        self.btn_export.setEnabled(False)

if __name__ == "__main__":
    print(">>> Début de l'exécution du script.")
    app = QApplication(sys.argv)
    print(">>> QApplication créée.")
    db_manager = PS2DatabaseManager()
    print(">>> PS2DatabaseManager créée et chargée.")
    win = PS2CheatsHubQt(db_manager)
    print(">>> Fenêtre principale PS2CheatsHubQt créée.")
    win.show()
    print(">>> win.show() appelé. L'interface devrait apparaître.")

    sys.exit(app.exec())
