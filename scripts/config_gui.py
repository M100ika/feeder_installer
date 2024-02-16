import tkinter as tk
from tkinter import ttk, messagebox
import sys
from pathlib import Path
import subprocess
from tkinter import simpledialog

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from _config_manager import ConfigManager 


class ConfigGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Конфигуратор оборудования")
        self.config_manager = ConfigManager("../config/config.ini")
        self.create_style() 
        self.user_level = tk.StringVar(value="user")
        self.draw_gui()
        self.disable_editing()


    def create_style(self):
        self.style = ttk.Style()
        self.style.configure('TLabel', font=('Arial', 10), padding=5)
        self.style.configure('TCheckbutton', font=('Arial', 10), padding=5)
        self.style.configure('TButton', font=('Arial', 10, 'bold'), padding=5)
        self.style.configure('TEntry', font=('Arial', 10), padding=5)
        self.style.configure('TLabelframe', font=('Arial', 12, 'bold'), padding=10)
        self.style.configure('TLabelframe.Label', font=('Arial', 12, 'bold'), padding=5)
        self.style.theme_use('classic')


    def save_changes(self):
        for section, entries in self.entries.items():
            for setting, info in entries.items():
                var = info['var']
                if isinstance(var, tk.IntVar) or isinstance(var, tk.StringVar):
                    value = var.get()  
                else:
                    continue 
                
                self.config_manager.update_setting(section, setting, str(value))
        messagebox.showinfo("Сохранение", "Настройки сохранены успешно!")

        # sudo_password = simpledialog.askstring("Пароль sudo", "Введите пароль sudo:", show='*')
        # if sudo_password is not None:
        #     try:
        #        
        #         command = 'echo {} | sudo -S systemctl restart feeder.service'.format(sudo_password)
        #         process = subprocess.run(command, shell=True, check=True, text=True, input=sudo_password, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #         messagebox.showinfo("Перезапуск сервиса", "Сервис успешно перезапущен!")
        #     except subprocess.CalledProcessError as e:
        #         messagebox.showerror("Ошибка", f"Не удалось перезапустить сервис: {e.stderr}")
        # else:
        #     messagebox.showinfo("Отмена", "Операция отменена пользователем.")

        try:
            # subprocess.run(['sudo', 'systemctl', 'restart', 'feeder.service'], check=True)
            messagebox.showinfo("Перезапуск сервиса", "Сервис успешно перезапущен!")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Ошибка", f"Не удалось перезапустить сервис: {e}")
            # /etc/sudoers
            # yourusername ALL=(ALL) NOPASSWD: /bin/systemctl restart feeder.service

    def draw_gui(self):
        self.notebook = ttk.Notebook(self.root)
        self.user_frame = ttk.Frame(self.notebook)
        self.mainframe = ttk.Frame(self.notebook)
        self.notebook.add(self.user_frame, text='Пользователь')
        self.notebook.add(self.mainframe, text='Настройки')
        self.notebook.pack(expand=True, fill='both')

        self.draw_settings_tab()
        self.draw_user_tab()

    def draw_settings_tab(self):
        self.entries = {}
        config = self.config_manager.get_config()

        self.mainframe.columnconfigure(0, weight=1)
        self.mainframe.rowconfigure(0, weight=1)

        exclude_list = [
            ('Parameters', 'url'),
            ('Parameters', 'median_url'),
            ('Parameters', 'array_url'),  
            ('DbId', 'id'),
            ('DbId', 'version'),
        ]

        checkbox_options = {
            ('Parameters', 'debug'): 'Debug',
            ('RFID_Reader', 'reader_buzzer'): 'Reader Buzzer',
            ('RFID_Reader', 'reader_usb'): 'Reader USB',
            ('Calibration', 'calibration_mode'): 'Calibration Mode'
        }

        readonly_options = {
            ('Calibration', 'offset'),
            ('Calibration', 'scale'),
        }

        row_number = 0
        for section in config.sections():
            self.entries[section] = {}

            section_frame = ttk.LabelFrame(self.mainframe, text=section) 
            section_frame.grid(column=0, row=row_number, sticky=(tk.W, tk.E), padx=5, pady=5)
            section_frame.columnconfigure(1, weight=1)

            section_row_number = 0
            for option in config[section]:
                if (section, option) in exclude_list:
                    continue

                row = ttk.Frame(section_frame)
                row.grid(row=section_row_number, column=0, columnspan=2, sticky=(tk.E, tk.E), padx=5, pady=2)

                label = ttk.Label(row, text=option)
                label.grid(row=0, column=0, sticky=tk.W)

                if (section, option) in checkbox_options.keys():
                    var = tk.IntVar(value=int(config.get(section, option)))
                    cb = ttk.Checkbutton(row, variable=var, onvalue=1, offvalue=0)
                    cb.grid(row=0, column=1, sticky=tk.W)
                    self.entries[section][option] = {'var': var, 'widget': cb}
                else:
                    entry_var = tk.StringVar(value=config.get(section, option))
                    entry = ttk.Entry(row, textvariable=entry_var)
                    if (section, option) in readonly_options:
                        entry.config(state='readonly')
                    entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
                    self.entries[section][option] = {'var': entry_var, 'widget': entry}

                section_row_number += 1

            row_number += 1

        save_button = ttk.Button(self.mainframe, text="Сохранить изменения", command=self.save_changes)  
        save_button.grid(row=row_number, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)


    def draw_user_tab(self):
        ttk.Label(self.user_frame, text="Выберите ваш уровень доступа:").pack(pady=10)
        ttk.Radiobutton(self.user_frame, text="Обычный пользователь", variable=self.user_level, value="user", command=self.update_access_level).pack(anchor=tk.W)
        ttk.Radiobutton(self.user_frame, text="Технический специалист", variable=self.user_level, value="admin", command=self.update_access_level).pack(anchor=tk.W)


    def update_access_level(self):
        if self.user_level.get() == "admin":
            entered_password = simpledialog.askstring("Пароль", "Введите пароль технического специалиста:", show='*')
            if entered_password is not None and self.check_password(entered_password):
                self.enable_editing()
            else:
                messagebox.showwarning("Ошибка", "Неверный пароль!")
                self.user_level.set("user")
        else:
            self.disable_editing()


    def enable_editing(self):
        for section, options in self.entries.items():
            for option, info in options.items():
                widget = info['widget']
                if isinstance(widget, ttk.Entry) or isinstance(widget, ttk.Checkbutton):
                    widget.config(state='normal')  


    def disable_editing(self):
        for section, options in self.entries.items():
            for option, info in options.items():
                widget = info['widget']
                if isinstance(widget, ttk.Entry):
                    widget.config(state='readonly')  
                elif isinstance(widget, ttk.Checkbutton):
                    widget.config(state='disabled')


    def check_password(self, entered_password):
        correct_password = "01" 
        return entered_password == correct_password


def main():
    root = tk.Tk()
    app = ConfigGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()