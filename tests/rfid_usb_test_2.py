import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from _chafon_rfid_lib import RFIDReader

if __name__ == '__main__':
    print(f'Начало теста rfid_reader модуля - считывание через USB')
    print(f'Пожалуйста заполните ../config/config.ini [RFID_Reader] reader_port = \nК примеру: /dev/ttyUSB0')
    print(f'Если вы не знаете порт пожалуйста сделайте следующие шаги: ')
    print(f'1. Отключите USB от rfid_reader;')
    print(f'2. Откройте терминал (ctrl+alt+t) и введите следующую команду: /dev/tty*;')
    print(f'3. Запомните список. Список возможно будет большой, но внимание нужно обратить на ttyUSB* или ttyACM*;')
    print(f'4. Вставьте USB обратно в raspberry и снова введите команду: /dev/tty*;')
    print(f'5. Должен появиться новый ttyUSB* или ttyACM*')
    print(f'6. Перепишите его в ../config/config.ini [RFID_Reader] reader_port = СЮДА\nК примеру: /dev/ttyUSB0')
    rfid_reader = RFIDReader()
    animal_id = rfid_reader.connect()
    while animal_id is None:
        animal_id = rfid_reader.connect()
    print(animal_id)