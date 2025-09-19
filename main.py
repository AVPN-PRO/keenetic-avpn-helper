# -*- coding: utf-8 -*-

import customtkinter as ctk
import webbrowser
from PIL import Image
from tkinter import filedialog
import threading
import telnetlib
import re
import os
import sys
import json

# --- Функция для правильного пути к ресурсам ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_default_color_theme(resource_path("assets/themes/dark-blue.json"))
        ctk.set_appearance_mode("dark")

        self.translations = {}
        self.info_window = None
        self.info_window_textbox = None
        self.load_translations("ru")

        self.title(self.translations.get("window_title", "Configurator"))
        self.resizable(False, False)

        self.config(bg="#2B2B2B")
        self.frame_bg_color = "#3C3C3C"
        self.main_font = ctk.CTkFont(family="Segoe UI", size=14)
        self.button_font = ctk.CTkFont(family="Segoe UI", size=14, weight="bold")
        self.promo_font = ctk.CTkFont(family="Segoe UI", size=18)
        self.credo_font = ctk.CTkFont(family="Segoe UI", size=16, weight="bold")
        self.warning_font = ctk.CTkFont(family="Segoe UI", size=12)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")
        top_frame.grid_columnconfigure(1, weight=1)

        try:
            self.logo_image = ctk.CTkImage(light_image=Image.open(resource_path("logo.png")), size=(120, 120))
            self.logo_label = ctk.CTkLabel(top_frame, image=self.logo_image, text="")
            self.logo_label.grid(row=0, column=0, rowspan=3, padx=(0, 20))
        except FileNotFoundError:
            self.logo_label = ctk.CTkLabel(top_frame, text="AVPN.PRO", font=ctk.CTkFont(size=30, weight="bold"))
            self.logo_label.grid(row=0, column=0, rowspan=3, padx=10)

        top_right_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        top_right_frame.grid(row=0, column=1, sticky="ne")

        self.instruction_button = ctk.CTkButton(top_right_frame, width=30, font=self.button_font, command=self.show_manual_instructions)
        self.instruction_button.pack(side="left", padx=(0, 10))
        self.lang_selector = ctk.CTkSegmentedButton(top_right_frame, values=["RU", "EN", "AR", "FA"], command=self.change_language)
        self.lang_selector.set("RU")
        self.lang_selector.pack(side="left")

        right_container = ctk.CTkFrame(top_frame, fg_color="transparent")
        right_container.grid(row=1, column=1, rowspan=2, sticky="nsew", pady=(5,0))
        self.promo_label = ctk.CTkLabel(right_container, font=self.promo_font)
        self.promo_label.pack(pady=(0, 5))
        button_frame_top = ctk.CTkFrame(right_container, fg_color="transparent")
        button_frame_top.pack(fill="x")
        self.site_button = ctk.CTkButton(button_frame_top, font=self.button_font, command=lambda: self.open_url("https://avpn.pro/"))
        self.site_button.pack(side="left", expand=True, padx=5, pady=5)
        self.telegram_button = ctk.CTkButton(button_frame_top, font=self.button_font, command=lambda: self.open_url("https://t.me/PrivateVPN100Bot"))
        self.telegram_button.pack(side="right", expand=True, padx=5, pady=5)
        self.warning_label = ctk.CTkLabel(right_container, text_color="#FFA500", font=self.warning_font)
        self.warning_label.pack(pady=5)

        self.main_frame = ctk.CTkFrame(self, fg_color=self.frame_bg_color)
        self.main_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.credo_label = ctk.CTkLabel(self, font=self.credo_font, bg_color="transparent")
        self.credo_label.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self._create_widgets()
        self.update_ui_texts()
        self.show_manual_instructions()

    def _create_info_window(self, title_key, content_key):
        if self.info_window is not None and self.info_window.winfo_exists():
            self.info_window.focus()
            return

        self.info_window = ctk.CTkToplevel(self)
        self.info_window.title(self.translations.get(title_key, "Info"))
        self.info_window.geometry("600x650")
        self.info_window.resizable(False, True)
        self.info_window.transient(self)

        def on_close():
            if self.info_window: self.info_window.destroy()
            self.info_window = None
            self.info_window_textbox = None
        self.info_window.protocol("WM_DELETE_WINDOW", on_close)

        self.info_window_textbox = ctk.CTkTextbox(self.info_window, font=self.main_font, wrap="word")
        self.info_window_textbox.pack(expand=True, fill="both", padx=10, pady=10)

        if content_key:
            text_content = self.translations.get(content_key, "Content not found.")
            self.info_window_textbox.insert("1.0", text_content)
        
        self.info_window_textbox.configure(state="disabled")

    def _create_widgets(self):
        conf_file_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        conf_file_frame.pack(pady=(20,10), padx=10, fill="x")
        self.conf_file_entry = ctk.CTkEntry(conf_file_frame, font=self.main_font, state="readonly")
        self.conf_file_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.conf_file_button = ctk.CTkButton(conf_file_frame, font=self.button_font, width=120, command=self.select_conf_file)
        self.conf_file_button.pack(side="left")

        credentials_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        credentials_frame.pack(pady=(20, 20), padx=10, fill="x")
        self.ip_entry = ctk.CTkEntry(credentials_frame, font=self.main_font)
        self.ip_entry.pack(fill="x", pady=5)
        self.user_entry = ctk.CTkEntry(credentials_frame, font=self.main_font)
        self.user_entry.pack(fill="x", pady=5)
        self.pass_entry = ctk.CTkEntry(credentials_frame, font=self.main_font, show="*")
        self.pass_entry.pack(fill="x", pady=5)

        self.start_button = ctk.CTkButton(self.main_frame, font=self.button_font, height=40, command=self.start_configuration_thread)
        self.start_button.pack(pady=(10, 20), padx=10, fill="x")

    def open_url(self, url):
        webbrowser.open_new_tab(url)

    def show_manual_instructions(self):
        self._create_info_window("manual_steps_title", "manual_steps_content")

    def load_translations(self, lang_code):
        path = resource_path(f"languages/{lang_code}.json")
        try:
            with open(path, 'r', encoding='utf-8') as f: self.translations = json.load(f)
        except:
            if lang_code != "ru": self.load_translations("ru")

    def change_language(self, lang_code):
        self.load_translations(lang_code.lower())
        self.update_ui_texts()

        if self.info_window is not None and self.info_window.winfo_exists():
            self.info_window.destroy()
        self.show_manual_instructions()

    def update_ui_texts(self):
        self.title(self.translations.get("window_title"))
        self.promo_label.configure(text=self.translations.get("promo_text"))
        self.site_button.configure(text=self.translations.get("site_button"))
        self.telegram_button.configure(text=self.translations.get("telegram_button"))
        self.warning_label.configure(text=self.translations.get("warning_text"))
        self.credo_label.configure(text=self.translations.get("credo_text"))
        self.instruction_button.configure(text=self.translations.get("manual_instruction_button", "Инструкция"))
        self.conf_file_entry.configure(placeholder_text=self.translations.get("conf_file_placeholder"))
        self.conf_file_button.configure(text=self.translations.get("select_file_button"))
        self.ip_entry.configure(placeholder_text=self.translations.get("ip_placeholder"))
        self.user_entry.configure(placeholder_text=self.translations.get("user_placeholder"))
        self.pass_entry.configure(placeholder_text=self.translations.get("password_placeholder"))
        self.start_button.configure(text=self.translations.get("start_button"))

    def select_conf_file(self):
        filepath = filedialog.askopenfilename(title=self.translations.get("select_file_button"), filetypes=(("Config files", "*.conf"), ("All files", "*.*")))
        if filepath:
            self.conf_file_entry.configure(state="normal"); self.conf_file_entry.delete(0, "end"); self.conf_file_entry.insert(0, filepath); self.conf_file_entry.configure(state="readonly")

    def log_message(self, message):
        if self.info_window and self.info_window.winfo_exists() and self.info_window_textbox:
            self.info_window_textbox.configure(state="normal")
            self.info_window_textbox.insert("end", message + "\n")
            self.info_window_textbox.see("end")
            self.info_window_textbox.configure(state="disabled")

    def start_configuration_thread(self):
        self.start_button.configure(state="disabled", text=self.translations.get("start_button_working"))
        
        # --- ИЗМЕНЕНИЕ: Очищаем окно инструкции и готовим его к выводу логов ---
        if self.info_window and self.info_window.winfo_exists() and self.info_window_textbox:
            self.info_window.title("Процесс настройки")
            self.info_window_textbox.configure(state="normal")
            self.info_window_textbox.delete("1.0", "end")
            self.info_window_textbox.configure(state="disabled")
        else: # Если пользователь закрыл окно, создаем его заново
            self._create_info_window("Процесс настройки", None)

        config_thread = threading.Thread(target=self.run_configuration_logic)
        config_thread.start()

    def run_configuration_logic(self):
        try:
            self.log_message("▶️ Начало настройки..."); config_path = self.conf_file_entry.get(); router_ip = self.ip_entry.get() or "192.168.1.1"; username = self.user_entry.get() or "admin"; password = self.pass_entry.get()
            if not config_path or not password: self.log_message("❌ ОШИБКА: Не выбран .conf файл или не введен пароль."); raise ValueError("Missing credentials")
            self.log_message("📄 Чтение ASC-параметров из файла..."); asc_data = self._parse_asc_config(config_path)
            if not asc_data: self.log_message("❌ ОШИБКА: Не удалось прочитать ASC-параметры."); raise ValueError("ASC parsing failed")
            self.log_message("   ✅ Параметры успешно прочитаны."); self.log_message(f"📡 Поиск WireGuard-интерфейса на {router_ip}..."); interface_name = self._find_last_wireguard_interface(router_ip, username, password)
            if not interface_name: self.log_message("❌ ОШИБКА: Не удалось найти интерфейс. Убедитесь, что вы загрузили .conf в роутер."); raise ValueError("Interface not found")
            self.log_message(f"   ✅ Найден интерфейс: {interface_name}"); self.log_message("⚙️ Применение ASC и DNS настроек..."); success = self._execute_final_config(router_ip, username, password, interface_name, asc_data)
            if not success: self.log_message("❌ ОШИБКА: Не удалось применить настройки через Telnet."); raise ValueError("Config execution failed")

            self.log_message("\n" + "="*53)
            self.log_message("✅✅✅ НАСТРОЙКА УСПЕШНО ЗАВЕРШЕНА! ✅✅✅")
            self.log_message("="*53)
            
            final_title = self.translations.get("final_instructions_title", "")
            final_content = self.translations.get("final_instructions_content", "")
            self.log_message(f"\n{final_title}\n{final_content}")

        except Exception as e:
            self.log_message(f"\n🔥🔥🔥 ПРОИЗОШЛА КРИТИЧЕСКАЯ ОШИБКА! 🔥🔥🔥")
        finally:
            self.start_button.configure(state="normal", text=self.translations.get("start_button"))
            if self.info_window and self.info_window.winfo_exists():
                self.info_window.title(self.translations.get("window_title"))

    def _parse_asc_config(self, config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f: content = f.read()
            asc_params = []; param_keys = ["Jc", "Jmin", "Jmax", "S1", "S2", "H1", "H2", "H3", "H4"]
            for key in param_keys:
                match = re.search(rf"^{key}\s*=\s*(\S+)", content, re.MULTILINE)
                if match: asc_params.append(match.group(1))
            return " ".join(asc_params) if len(asc_params) == len(param_keys) else None
        except: return None

    def _find_last_wireguard_interface(self, ip, username, password):
        try:
            with telnetlib.Telnet(ip, 23, timeout=10) as tn:
                tn.read_until(b"Login: "); tn.write(username.encode('ascii') + b"\n"); tn.read_until(b"Password: "); tn.write(password.encode('ascii') + b"\n")
                tn.expect([b">"], timeout=5); tn.write(b"show running-config\n"); response_bytes = tn.read_until(b"\n>", timeout=20)
                response_str = response_bytes.decode('utf-8', errors='ignore'); matches = re.findall(r"^interface\s+(Wireguard\d+)", response_str, re.MULTILINE)
                return matches[-1] if matches else None
        except: return None

    def _execute_final_config(self, ip, username, password, interface_name, asc_params):
        commands = [f"interface {interface_name}", f"wireguard asc {asc_params}", "exit", "no ip name-server", "dns-proxy https upstream https://1.1.1.1/dns-query", "dns-proxy https upstream https://9.9.9.9/dns-query", "system configuration save"]
        try:
            with telnetlib.Telnet(ip, 23, timeout=10) as tn:
                tn.read_until(b"Login: "); tn.write(username.encode('ascii') + b"\n"); tn.read_until(b"Password: "); tn.write(password.encode('ascii') + b"\n")
                tn.expect([b">"], timeout=5)
                for cmd in commands:
                    self.after(10, lambda c=cmd: self.log_message(f"   > Отправка команды: {c[:30]}..."))
                    tn.write(cmd.encode('ascii') + b"\n"); tn.read_until(b">", timeout=10)
                return True
        except: return False

if __name__ == "__main__":
    app = App()
    app.mainloop()