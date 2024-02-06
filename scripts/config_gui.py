import tkinter as tk
from tkinter import ttk, messagebox
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from _config_manager import ConfigManager  # Убедитесь, что config_manager находится в PYTHONPATH


class ConfigGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Конфигуратор оборудования")
        self.config_manager = ConfigManager("../config/config.ini")

        self.create_style()  # Создаем стили
        self.draw_gui()

    def create_style(self):
        self.style = ttk.Style()
        self.style.configure('TLabel', font=('Arial', 10), padding=5)
        self.style.configure('TCheckbutton', font=('Arial', 10), padding=5)
        self.style.configure('TButton', font=('Arial', 10, 'bold'), padding=5)
        self.style.configure('TEntry', font=('Arial', 10), padding=5)
        self.style.configure('TLabelframe', font=('Arial', 12, 'bold'), padding=10)
        self.style.configure('TLabelframe.Label', font=('Arial', 12, 'bold'), padding=5)
       
        try:
            # Предполагаем, что файл темы находится в папке 'theme' в текущем каталоге скрипта
            self.root.tk.call('source', 'Azure-ttk-theme-main/theme/light.tcl')
            self.style.theme_use('azure-light')
        except tk.TclError as e:
            messagebox.showerror("Ошибка темы", f"Не удалось загрузить тему Azure: {e}")
            self.style.theme_use('default') 
        #self.style.theme_use('classic')

    def save_changes(self):
        for section, entries in self.entries.items():
            for setting, entry in entries.items():
                if isinstance(entry, tk.IntVar):
                    value = entry.get()  # Для чекбоксов
                else:
                    value = entry.get()  # Для текстовых полей
                self.config_manager.update_setting(section, setting, str(value))
        messagebox.showinfo("Сохранение", "Настройки сохранены успешно!")

    def draw_gui(self):
        self.entries = {}
        config = self.config_manager.get_config()

        mainframe = ttk.Frame(self.root, padding="3 3 12 12")
        mainframe.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)

        # Определите список исключений
        exclude_list = [
            ('Parameters', 'url'),
            ('Parameters', 'median_url'),
            ('Parameters', 'array_url'),
            ('Calibration', 'offset'),  
            ('Calibration', 'scale'),   
            ('DbId', 'id'),
            ('DbId', 'version'),
        ]

        checkbox_options = {
            ('Parameters', 'debug'): 'Debug',
            ('RFID_Reader', 'reader_buzzer'): 'Reader Buzzer',
            ('RFID_Reader', 'reader_usb'): 'Reader USB',
            ('Calibration', 'calibration_mode'): 'Calibration Mode'
        }

        row_number = 0
        for section in config.sections():
            # Создайте словарь для секции перед добавлением виджетов
            self.entries[section] = {}

            section_frame = ttk.LabelFrame(mainframe, text=section)
            section_frame.grid(column=0, row=row_number, sticky=(tk.W, tk.E), padx=5, pady=5)
            section_frame.columnconfigure(1, weight=1)

            section_row_number = 0
            for option in config[section]:
                if (section, option) in exclude_list:
                    continue  # Пропустите добавление этой опции, если она в списке исключений

                row = ttk.Frame(section_frame)
                row.grid(row=section_row_number, column=0, columnspan=2, sticky=(tk.E, tk.E), padx=5, pady=2)
                section_frame.columnconfigure(0, weight=1)  # Даем второй колонке возможность растягиваться

                label = ttk.Label(row, text=option)
                label.grid(row=0, column=0, sticky=tk.N)

                if (section, option) in checkbox_options.keys():
                    var = tk.IntVar(value=int(config.get(section, option)))
                    cb = ttk.Checkbutton(row, variable=var, onvalue=1, offvalue=0)
                    cb.grid(row=0, column=1, sticky=tk.E)  # Правое выравнивание для чекбокса
                    self.entries[section][option] = var
                else:
                    entry_var = tk.StringVar(value=config.get(section, option))
                    entry = ttk.Entry(row, textvariable=entry_var)
                    entry.grid(row=0, column=1, sticky=(tk.E, tk.W), padx=5, pady=2)  # Растягивание Entry от левого до правого края
                    self.entries[section][option] = entry_var
                    
                section_row_number += 1

            row_number += 1

        # Расположение кнопки "Сохранить изменения" внизу
        save_button = ttk.Button(mainframe, text="Сохранить изменения", command=self.save_changes)
        save_button.grid(row=row_number, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)

def main():
    root = tk.Tk()
    app = ConfigGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()