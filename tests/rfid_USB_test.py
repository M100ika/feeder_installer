import time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from _config_manager import ConfigManager

from chafon_rfid.base import CommandRunner, ReaderCommand, ReaderInfoFrame, ReaderResponseFrame, ReaderType
from chafon_rfid.command import (CF_GET_READER_INFO, CF_SET_BUZZER_ENABLED, CF_SET_RF_POWER)
from chafon_rfid.response import G2_TAG_INVENTORY_STATUS_MORE_FRAMES
from chafon_rfid.transport_serial import SerialTransport
from chafon_rfid.uhfreader288m import G2InventoryCommand, G2InventoryResponseFrame

config_manager = ConfigManager()

RFID_READER_PORT = config_manager.get_setting("RFID_Reader", "reader_port")  
RFID_READER_POWER = int(config_manager.get_setting("RFID_Reader", "reader_power"))
RFID_READER_TIMEOUT = int(config_manager.get_setting("RFID_Reader", "reader_timeout"))
RFID_READER_BUZZER = int(config_manager.get_setting("RFID_Reader", "reader_buzzer"))


def __get_reader_type(runner):
    get_reader_info = ReaderCommand(CF_GET_READER_INFO)
    reader_info = ReaderInfoFrame(runner.run(get_reader_info))
    return reader_info.type


def __run_command(transport, command):
    transport.write(command.serialize())
    status = ReaderResponseFrame(transport.read_frame()).result_status
    return status

def __set_power(transport):
    return __run_command(transport, ReaderCommand(CF_SET_RF_POWER, data=[RFID_READER_POWER]))

def __set_buzzer_enabled(transport):
    return __run_command(transport, ReaderCommand(CF_SET_BUZZER_ENABLED, data=[RFID_READER_BUZZER and 1 or 0]))


def __read_tag():
    transport = SerialTransport(device=RFID_READER_PORT) 
    runner = CommandRunner(transport)
    tag_id = None  

    try:
        reader_type = __get_reader_type(runner)
        if reader_type in (ReaderType.UHFReader86, ReaderType.UHFReader86_1):
            get_inventory_cmd = G2InventoryCommand(q_value=4, antenna=0x80)
            frame_type = G2InventoryResponseFrame
            __set_power(transport)
            __set_buzzer_enabled(transport)
        else:
            print('Unsupported reader type: {}'.format(reader_type))
            return None
    except ValueError as e:
        print('Unknown reader type: {}'.format(e))
        return None

    start_time = time.time()
    while tag_id is None:
        try:
            transport.write(get_inventory_cmd.serialize())
            inventory_status = None
            while inventory_status is None or inventory_status == G2_TAG_INVENTORY_STATUS_MORE_FRAMES:
                if time.time() - start_time > RFID_READER_TIMEOUT: 
                    print("Timeout reached, stopping tag reading.")
                    return None
                resp = frame_type(transport.read_frame())
                inventory_status = resp.result_status
                tags_generator = resp.get_tag()
                try:
                    first_tag = next(tags_generator, None)  
                    if first_tag:
                        tag_id = first_tag.epc.hex()  
                        break  
                except StopIteration:
                    continue  
        except KeyboardInterrupt:
            print("Operation cancelled by user.")
            break
        except Exception as e:
            print(f'Error: {e}')
            continue

    transport.close()
    if tag_id:
        modified_tag_id = tag_id[:-10]
        final_tag_id = modified_tag_id[-12:]
        return final_tag_id
    else:
        return None
    
if __name__ == "__main__":
    print(f'Начало теста rfid_reader модуля - считывание через USB')
    print(f'Пожалуйста заполните ../config/config.ini [RFID_Reader] reader_port = \nК примеру: /dev/ttyUSB0')
    print(f'Если вы не знаете порт пожалуйста сделайте следующие шаги: ')
    print(f'1. Отключите USB от rfid_reader;')
    print(f'2. Откройте терминал (ctrl+alt+t) и введите следующую команду: /dev/tty*;')
    print(f'3. Запомните список. Список возможно будет большой, но внимание нужно обратить на ttyUSB* или ttyACM*;')
    print(f'4. Вставьте USB обратно в raspberry и снова введите команду: /dev/tty*;')
    print(f'5. Должен появиться новый ttyUSB* или ttyACM*')
    print(f'6. Перепишите его в ../config/config.ini [RFID_Reader] reader_port = СЮДА\nК примеру: /dev/ttyUSB0')
    tag = __read_tag()
    while tag is None: 
        tag = __read_tag()
    
    print(tag)