"""Feeder version 3. Edition by Suieubayev Maxat.
feeder_module.py - это модуль функции кормушки. 
Contact number +7 775 818 48 43. Email maxat.suieubayev@gmail.com"""

#!/usr/bin/sudo python3

from requests.exceptions import HTTPError
from datetime import datetime
from loguru import logger
from _chafon_rfid_lib import RFIDReader
import _sql_database as sql
from _config_manager import ConfigManager
import _adc_data as ADC
import time
import requests
import binascii
import socket
import json
import threading
import queue
import time
#import RPi.GPIO as GPIO
import timeit

config_manager = ConfigManager()

TCP_IP = '192.168.1.250'  # Chafon 5300 reader address
TCP_PORT = 60000          # Chafon 5300 port
BUFFER_SIZE = 1024

ARDUINO_PORT = config_manager.get_setting("Parameters", "arduino_port")     
RELAY_PIN = int(config_manager.get_setting("Relay", "sensor_pin"))
RFID_TIMEOUT = int(config_manager.get_setting("RFID_Reader", "reader_timeout"))

RFID_READER_USB = int(config_manager.get_setting("RFID_Reader", "reader_usb"))


def _get_relay_state():
    # GPIO.setmode(GPIO.BCM)
    # GPIO.setup(RELAY_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    # relay_state = GPIO.input(RELAY_PIN)
    # GPIO.cleanup() 
    # return relay_state == GPIO.HIGH
    return 1


def _check_relay_state(check_count=10, threshold=5) -> bool:
    """
    Проверяет состояние реле определенное количество раз и выполняет действие,
    если реле находится в состоянии HIGH достаточное количество раз.

    Args:
    pin_number (int): Номер пина, к которому подключено реле.
    check_count (int): Количество проверок состояния реле.
    threshold (int): Пороговое значение для количества раз, когда реле должно быть в состоянии HIGH.

    Returns:
    bool: True, если реле было в состоянии HIGH достаточное количество раз, иначе False.
    """
    try:
        high_count = 0
        for _ in range(check_count):
            if _get_relay_state():
                high_count += 1
                if high_count >= threshold:
                    return True
            time.sleep(0.1)  

        return False
    except Exception as e:
        logger.error(f"_Check_relay_state function error: {e}")


def initialize_arduino(port):
    try:
        arduino_object = ADC.ArduinoSerial(port)
        arduino_object.connect()
        if arduino_object.isOpen():
            logger.info(f'Connection established on port {port}')
            try:
                offset = float(config_manager.get_setting("Calibration", "offset"))
                scale = float(config_manager.get_setting("Calibration", "scale"))
                arduino_object.set_offset(offset)
                arduino_object.set_scale(scale)
            except Exception as e:
                logger.error(f'Error setting calibration: {e}')
                return None
        else:
            logger.error(f'Failed to open connection on port {port}')
            return None
        
        return arduino_object
    
    except Exception as e:
        logger.error(f'Error connecting to Arduino on port {port}: {e}')
        return None


def __post_request(event_time, feed_time, animal_id, end_weight, feed_weight) -> dict:
    try:
        equipment_type = config_manager.get_setting("Parameters", "type")
        serial_number = config_manager.get_setting("Parameters", "serial_number")
        payload = {
            "Eventdatetime": event_time,
            "EquipmentType": equipment_type,
            "SerialNumber": serial_number,
            "FeedingTime": feed_time,
            "RFIDNumber": animal_id,
            "WeightLambda": end_weight,
            "FeedWeight": feed_weight
        }
        return payload
    except ValueError as v:
        logger.error(f'__Post_request function error: {v}')


def check_internet():
    try:
        mstr = "http://google.com"
        res = requests.get(mstr)
        if res.status_code == 200:
            sql.internetOn()
    except:
        logger.error(f'No internet')


def __send_post(postData):
    url = config_manager.get_setting("Parameters", "url")
    headers = {'Content-type': 'application/json'}
    try:
        post = requests.post(url, data = json.dumps(postData), headers = headers, timeout=30)
        logger.info(f'{post.status_code}')
    except HTTPError as http_err:
        logger.error(f'HTTP error occurred: {http_err}')
    except Exception as err:
        logger.error(f'Other error occurred: {err}')
    # finally:
    #     if type(post) != requests.models.Response:
    #         sql.noInternet(postData)


def __connect_rfid_reader_ethernet():
    try:    
        logger.info('Start connect RFID function')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((TCP_IP, TCP_PORT))
            s.send(bytearray([0x53, 0x57, 0x00, 0x06, 0xff, 0x01, 0x00, 0x00, 0x00, 0x50])) # Chafon RU5300 Answer mode reading mode command
            s.settimeout(RFID_TIMEOUT)
            for attempt in range(1, 4):
                try:
                    data = s.recv(BUFFER_SIZE)
                    animal_id = binascii.hexlify(data).decode('utf-8')[:-10][-12:]
                    logger.info(f'After end: Animal ID: {animal_id}')
                    return animal_id if animal_id != None else None
                except socket.timeout:
                    logger.info(f'Timeout occurred on attempt {attempt}')
        return None
    except Exception as e:
        logger.error(f'Error connect RFID reader {e}')
        return None


def __get_input(message, channel): # Функция для получения введенного значения
                                   # Ничего не менять ее!
    response = input(message)
    channel.put(response)


def input_with_timeout(message, timeout):   # Функция создания второго потока.
                                            # Временная задержка во время которой можно ввести значение
                                            # Ничего не менять!
    channel = queue.Queue()
    message = message + " [{} sec timeout] ".format(timeout)
    thread = threading.Thread(target=__get_input, args=(message, channel))
    thread.daemon = True
    thread.start()

    try:
        response = channel.get(True, timeout)
        return response
    except queue.Empty:
        pass
    return None


def _calibrate_or_start():
    try:
        logger.info(f'\nSelect an option:\n[1] Calibrate\n[2] Start Measurement')
        choice = '2'
        choice = input_with_timeout("Your choice (1/2):", 5)
        time.sleep(5)

        if choice == '1':
            calibrate()

    except Exception as e:
        logger.error(f'Calibrate or start Error: {e}')


def calibrate():
    try:
        logger.info(f'\033[1;33mStarting the calibration process.\033[0m')
        port = config_manager.get_setting("Parameters", "arduino_port")
        arduino = ADC.ArduinoSerial(port, 9600, timeout=1)
        arduino.connect()
        logger.info(f"Ensure the scale is clear. Press any key once it's empty and you're ready to proceed.")
        time.sleep(1)
        input()
        offset = arduino.calib_read()
        logger.info("Offset: {}".format(offset))
        arduino.set_offset(offset)
        logger.info("Place a known weight on the scale and then press any key to continue.")
        input()
        measured_weight = (arduino.calib_read()-arduino.get_offset())
        logger.info("Please enter the item's weight in kg.\n>")
        item_weight = input()
        scale = int(measured_weight)/int(item_weight)
        arduino.set_scale(scale)
        logger.info(f"\033[1;33mCalibration complete.\033[0m")
        logger.info(f'Calibration details\n\n —Offset: {offset}, \n\n —Scale factor: {scale}')
        config_manager.update_setting("Calibration", "Offset", offset)
        config_manager.update_setting("Calibration", "Scale", scale)
        arduino.disconnect()
        del arduino
    except:
        logger.error(f'calibration Fail')
        arduino.disconnect()


def _rfid_scale_calib():
    try:
        logger.info(f'\033[1;33mStarting the RFID scale calibration process.\033[0m')
        logger.info(f'\033There should be {config_manager.get_setting("Calibration", "weight")} kg.\033[')
        port = config_manager.get_setting("Parameters", "arduino_port")
        arduino = ADC.ArduinoSerial(port, 9600, timeout=1)
        arduino.connect()
        measured_weight = (arduino.calib_read()-arduino.get_offset())
        scale = int(measured_weight)/int(config_manager.get_setting("Calibration", "weight"))
        arduino.set_scale(scale)
        config_manager.update_setting("Calibration", "Scale", scale)
        logger.info(f'Calibration details\n\n —Scale factor: {scale}')
        arduino.disconnect()
        del arduino
        logger.info(f'\033[1;33mRFID scale calibration process finished succesfully.\033[0m')
    except:
        logger.error(f'calibrate Fail')
        arduino.disconnect()


def _rfid_offset_calib():
    try:
        logger.info(f'\033[1;33mStarting the RFID taring process.\033[0m')
        port = config_manager.get_setting("Parameters", "arduino_port")
        arduino = ADC.ArduinoSerial(port, 9600, timeout=1)
        arduino.connect()
        offset = arduino.calib_read()
        arduino.set_offset(offset)
        config_manager.update_setting("Calibration", "Offset", offset)
        logger.info(f'Calibration details\n\n —Offset: {offset}')
        arduino.disconnect()
        del arduino
        logger.info(f'\033[1;33mRFID taring process finished succesfully.\033[0m')
    except:
        logger.error(f'RFID taring process Failed')
        arduino.disconnect()


def _first_weight(arduino_object):
    try:
        for i in range(5):
            arduino_object._get_measure()
        return arduino_object._get_measure()
    except Exception as e:
        logger.error(f'start_weight Error: {e}')


def __process_calibration(animal_id):
    try:
        if animal_id == config_manager.get_setting("Calibration", "taring_rfid"):
            _rfid_offset_calib()
        elif animal_id == config_manager.get_setting("Calibration", "scaling_rfid"):
            _rfid_scale_calib()        
    except Exception as e:
        logger.error(f'Calibration with RFID: {e}')

def __animal_rfid():
    try:
        if RFID_READER_USB:
            rfid_reader = RFIDReader()
            return rfid_reader.connect()
        else:
            return __connect_rfid_reader_ethernet() 
    except Exception as e:
        logger.error(f'take rfid error: {e}')


def _process_feeding(weight):
    try:
        start_weight = _first_weight(weight)       
        start_time = timeit.default_timer()            
        animal_id = __animal_rfid()
            
        logger.info(f'Start weight: {start_weight}')      
        logger.info(f'Start time: {start_time}')           
        logger.info(f'Animal ID: {animal_id}')

        __process_calibration(animal_id) 

        while True:
            if _check_relay_state():
                end_time = timeit.default_timer()       
                end_weight = weight._get_measure()
                logger.info(f'Feed weight: {end_weight}')
                __process_calibration(animal_id) 
                animal_id = __animal_rfid()
            else:
                break
            time.sleep(1)
            
        logger.info(f'While ended.')

        feed_time = end_time - start_time           
        feed_time_rounded = round(feed_time, 2)
        final_weight = start_weight - end_weight    
        final_weight_rounded = round(final_weight, 2)

        logger.info(f'Finall result')
        logger.info(f'finall weight: {final_weight_rounded}')
        logger.info(f'feed_time: {feed_time_rounded}')

        eventTime = str(str(datetime.now()))

        if feed_time > 10: 
            post_data = __post_request(eventTime, feed_time_rounded, animal_id, final_weight_rounded, end_weight)
            __send_post(post_data)
        weight.disconnect()

    except Exception as e:
        logger.error(f'Calibration with RFID: {e}')


def feeder_module_v71():
    _calibrate_or_start()
    logger.debug(f"'\033[1;35mFeeder project version 7.1.\033[0m'")
    while True:  
        try:        
            if _check_relay_state():
                weight = initialize_arduino(ARDUINO_PORT)
                if weight is not None:
                    try:
                        _process_feeding(weight)
                    finally:
                        weight.disconnect()  
                else:
                    logger.error("Failed to initialize Arduino.")
        except Exception as e: 
            logger.error(f'Error: {e}')


def feeder_module_v61():
    _calibrate_or_start()  
    logger.debug(f"'\033[1;35mFeeder project version 6.1.\033[0m'")
    while True:
        try:        
            if _get_relay_state():  
                weight = initialize_arduino(ARDUINO_PORT)
                start_weight = _first_weight(weight)       
                start_time = timeit.default_timer()      
                animal_id = __connect_rfid_reader_ethernet()      

                logger.info(f'Start weight: {start_weight}')    
                logger.info(f'Start time: {start_time}')
                logger.info(f'Animal_id: {animal_id}')
                end_time = start_time      
                end_weight = start_weight

                __process_calibration(animal_id)

                while _get_relay_state():
                    end_time = timeit.default_timer()       
                    end_weight = weight._get_measure()
                    logger.info(f'Feed weight: {end_weight}')
                    if animal_id == config_manager.get_config("Parameters", "null_rfid"):
                        animal_id = __connect_rfid_reader_ethernet()
                    time.sleep(1)
                    if _get_relay_state() == False: # На всякий случай
                        break
                    
                logger.info(f'While ended.')

                feed_time = end_time - start_time           
                feed_time_rounded = round(feed_time, 2)
                final_weight = start_weight - end_weight    
                final_weight_rounded = round(final_weight, 2)

                logger.info(f'Finall result')
                logger.info(f'finall weight: {final_weight_rounded}')
                logger.info(f'feed_time: {feed_time_rounded}')

                eventTime = str(str(datetime.now()))

                if feed_time > 10: # Если корова стояла больше 10 секунд то отправляем данные
                    post_data = __post_request(eventTime, feed_time_rounded, animal_id, final_weight_rounded, end_weight)    #400
                    __send_post(post_data)
                weight.disconnect()
        except Exception as e:
            logger.error(f'Error: {e}')
            weight.disconnect()
