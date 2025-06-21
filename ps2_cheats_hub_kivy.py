"""
Version Kivy de PS2 Cheats Hub pour Android (et multiplateforme)
Interface simplifiée pour décryptage de codes PS2 (ARMAX/AR2).
"""
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.core.window import Window

from armax_ps2_logic import armax_batch_decrypt_full_python, FILTER_CHARS
from ar2_ps2_logic import ar2_set_seed, ar2_batch_decrypt_arr, AR1_SEED

class MainWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.padding = 10
        self.spacing = 10

        self.code_type_label = Label(text="Type de code : ARMAX ou AR2/GS2", size_hint_y=None, height=30)
        self.add_widget(self.code_type_label)

        self.code_type_input = TextInput(text="ARMAX", multiline=False, size_hint_y=None, height=40)
        self.add_widget(self.code_type_input)

        self.input_label = Label(text="Codes à décrypter (un par ligne)", size_hint_y=None, height=30)
        self.add_widget(self.input_label)

        self.input_codes = TextInput(hint_text="Collez vos codes ici...", size_hint_y=None, height=120)
        self.add_widget(self.input_codes)

        self.decrypt_btn = Button(text="Décrypter", size_hint_y=None, height=50)
        self.decrypt_btn.bind(on_press=self.decrypt_codes)
        self.add_widget(self.decrypt_btn)

        self.output_label = Label(text="Résultat :", size_hint_y=None, height=30)
        self.add_widget(self.output_label)

        self.output = TextInput(readonly=True, size_hint_y=1)
        self.add_widget(self.output)

    def decrypt_codes(self, instance):
        code_type = self.code_type_input.text.strip().upper()
        input_lines = self.input_codes.text.strip().splitlines()
        try:
            if code_type == "ARMAX":
                ar2_key_for_ps2 = 0x04030209
                success, decrypted_pairs_batch, game_id, region = armax_batch_decrypt_full_python(
                    [l.upper().replace("-", "") for l in input_lines if l.strip()], ar2_key_for_ps2)
                if not success:
                    self.output.text = "Erreur lors du décryptage ARMAX."
                    return
                lines = [f"{addr:08X} {val:08X}" for addr, val in decrypted_pairs_batch]
                self.output.text = "\n".join(lines)
            else:
                ar2_codes = []
                for line in input_lines:
                    parts = line.strip().split()
                    if len(parts) == 2:
                        try:
                            addr = int(parts[0], 16)
                            val = int(parts[1], 16)
                            ar2_codes.extend([addr, val])
                        except Exception:
                            continue
                ar2_set_seed(AR1_SEED)
                working_codes_copy = list(ar2_codes)
                decrypted_size_u32 = ar2_batch_decrypt_arr(working_codes_copy)
                lines = []
                for i in range(0, decrypted_size_u32, 2):
                    if i + 1 < decrypted_size_u32:
                        lines.append(f"{working_codes_copy[i]:08X} {working_codes_copy[i+1]:08X}")
                self.output.text = "\n".join(lines)
        except Exception as e:
            self.output.text = f"Erreur : {e}"

class PS2CheatsHubKivyApp(App):
    def build(self):
        Window.clearcolor = (0.12, 0.12, 0.12, 1)
        return MainWidget()

if __name__ == "__main__":
    PS2CheatsHubKivyApp().run()
