"""Feeder version 3. Edition by Suieubayev Maxat.
feeder_module.py - это модуль функции кормушки. 
Contact number +7 775 818 48 43. Email maxat.suieubayev@gmail.com"""

#!/usr/bin/sudo python3

from requests.exceptions import HTTPError
from datetime import datetime
from loguru import logger
import sql_database as sql
import _config as cfg
import statistics
import adc_data as ADC
import time
import requests
import binascii
import socket
import sys
import json
import threading
import queue
import time
import re
#import RPi.GPIO as GPIO
import timeit


def _get_relay_state(pin_number):
    # GPIO.setmode(GPIO.BCM)
    # GPIO.setup(pin_number, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    # relay_state = GPIO.input(pin_number)
    # GPIO.cleanup() 
    # return relay_state == GPIO.HIGH
    return 1

def _start_obj(port):
    try:
        obj = ADC.ArduinoSerial(port)
        obj.connect()
        offset, scale = float(cfg.get_setting("Calibration", "offset")), float(cfg.get_setting("Calibration", "scale"))
        obj.set_offset(offset)
        obj.set_scale(scale)
        return obj
    except Exception as e:
        logger.error(f'Error connecting: {e}')

def connect_arduino_to_get_dist(s):
    s.flushInput() # Cleaning buffer of Serial Port
    s.flushOutput() # Cleaning output buffer of Serial Port
    distance = (str(s.readline()))
    distance = re.sub("b|'|\r|\n", "", distance[:-5])
    #while (float(distance)) < 50:
    #    distance = (str(s.readline()))
    #    distance = re.sub("b|'|\r|\n", "", distance[:-5])
    #    distance = float(distance)
    #    return distance
    return distance


def _post_request(event_time, feed_time, animal_id, end_weight, feed_weight):
    try:
        feeder_type = cfg.get_setting("Parameters", "type")
        serial_number = cfg.get_setting("Parameters", "serial_number")
        payload = {
            "Eventdatetime": event_time,
            "EquipmentType": feeder_type,
            "SerialNumber": serial_number,
            "FeedingTime": feed_time,
            "RFIDNumber": animal_id,
            "WeightLambda": end_weight,
            "FeedWeight": feed_weight
        }
        return payload
    except ValueError as v:
        logger.error(f'_Post_request function error: {v}')


def check_internet():
    try:
        mstr = "http://google.com"
        res = requests.get(mstr)
        if res.status_code == 200:
            sql.internetOn()
    except:
        logger.error(f'No internet')


def _send_post(postData):
    url = cfg.get_setting("Parameters", "url")
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


def __connect_rfid_reader():                                      # Connection to RFID Reader through TCP and getting cow ID in str format
    try:    
        logger.info(f'Start connect RFID function')
        TCP_IP = '192.168.1.250'                                #chafon 5300 reader address
        TCP_PORT = 60000                                        #chafon 5300 port
        BUFFER_SIZE = 1024
        animal_id = "b'435400040001'"                           # Id null starting variable
        animal_id_new = "b'435400040001'"
        null_id = "b'435400040001'"

        if animal_id == null_id: # Send command to reader waiting id of animal
            logger.info(f' In the begin: Animal ID: {animal_id}')
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((TCP_IP, TCP_PORT))
            s.send(bytearray([0x53, 0x57, 0x00, 0x06, 0xff, 0x01, 0x00, 0x00, 0x00, 0x50])) #Chafon RU5300 Answer mode reading mode command
            data = s.recv(BUFFER_SIZE)
            animal_id= str(binascii.hexlify(data))
            animal_id_new = animal_id[:-5] #Cutting the string from unnecessary information after 4 signs 
            animal_id_new = animal_id_new[-12:] #Cutting the string from unnecessary information before 24 signs
            logger.info(f'After end: Animal ID: {animal_id}')
            s.close()             
        if animal_id_new == null_id: # Id null return(0)
            __connect_rfid_reader()
        else: # Id checkt return(1)
            animal_id = "b'435400040001'"

            return animal_id_new
    except Exception as e:
        logger.error(f'Error connect RFID reader {e}')


def rfid_label():
    try:
        labels = []
        sec = 5
        start_time = time.time()
        stop_time = start_time + sec
        while len(labels) < sec:
            cow_id = __connect_rfid_reader()
            labels.append(cow_id)
            if time.time() >= stop_time:
                break

        if len(labels) < sec:
            animal_id = labels[-1]
        else:
            animal_id = max([j for i,j in enumerate(labels) if j in labels[i+1:]]) if labels != list(set(labels)) else -1
        return animal_id
    except ValueError as v:
        logger.error(f'_Post_request function error: {v}')


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


# def instant_weight(s):
#     try:
#         s.flushInput() 
#         weight = (str(s.readline())) 
#         weight_new = re.sub("b|'|\r|\n", "", weight[:-5])
#         return weight_new
#     except ValueError as e:
#         logger.error(f'Instant_weight function Error: {e}')



def _calibrate_or_start():
    try:
        logger.info(f'\nSelect an option:\n[1] Calibrate\n[2] Start Measurement')
        choice = '2'
        choice = input_with_timeout("Your choice (1/2):", 5)
        time.sleep(5)

        if choice == '1':
            offset, scale = calibrate()
            cfg.update_setting("Calibration", "Offset", offset)
            cfg.update_setting("Calibration", "Scale", scale)

    except Exception as e:
        logger.error(f'Calibrate or start Error: {e}')


def calibrate():
    try:
        logger.info(f'\033[1;33mStarting the calibration process.\033[0m')
        port = cfg.get_setting("Parameters", "arduino_port")
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
        cfg.update_setting("Calibration", "Offset", offset)
        cfg.update_setting("Calibration", "Scale", scale)
        arduino.disconnect()
        del arduino
        return offset, scale
    except:
        logger.error(f'calibration Fail')
        arduino.disconnect()


def _rfid_scale_calib():
    try:
        logger.info(f'\033[1;33mStarting the RFID scale calibration process.\033[0m')
        logger.info(f'\033There should be {cfg.get_setting("Calibration", "weight")} kg.\033[')
        port = cfg.get_setting("Parameters", "arduino_port")
        arduino = ADC.ArduinoSerial(port, 9600, timeout=1)
        arduino.connect()
        measured_weight = (arduino.calib_read()-arduino.get_offset())
        scale = int(measured_weight)/int(cfg.get_setting("Calibration", "weight"))
        arduino.set_scale(scale)
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
        port = cfg.get_setting("Parameters", "arduino_port")
        arduino = ADC.ArduinoSerial(port, 9600, timeout=1)
        arduino.connect()
        offset = arduino.calib_read()
        arduino.set_offset(offset)
        logger.info(f'Calibration details\n\n —Offset: {offset}')
        arduino.disconnect()
        del arduino
        logger.info(f'\033[1;33mRFID taring process finished succesfully.\033[0m')
    except:
        logger.error(f'RFID taring process Failed')
        arduino.disconnect()



def _first_weight(obj):
    try:
        for i in range(5):
            obj._get_measure()
        return obj._get_measure()
    except Exception as e:
        logger.error(f'start_weight Error: {e}')


def __function_timer(timeout_time):
    try:
        logger.info(f'Function timer')
        start = time.time()
        stop_seconds = timeout_time
        while time.time() - start < stop_seconds:
            None
        return False
    except:
        logger.error(f'function_timer error.')


def feeder_module():
    _calibrate_or_start()
    port = cfg.get_setting("Parameters", "arduino_port")     
    relay_pin = cfg.get_setting("Relay", "sensor_pin")
    logger.debug(f"'\033[1;35mFeeder project.\033[0m'")
    while True:
        try:        
            if _get_relay_state(int(relay_pin)):  
                weight = _start_obj(port)
                start_weight = _first_weight(weight)       
                start_time = timeit.default_timer()      
                animal_id = __connect_rfid_reader()      

                logger.info(f'Start weight: {start_weight}')    
                logger.info(f'Start time: {start_time}')
                logger.info(f'Animal_id: {animal_id}')
                end_time = start_time      
                end_weight = start_weight

                process_calibration(animal_id)

                while _get_relay_state(int(relay_pin)):
                    end_time = timeit.default_timer()       
                    end_weight = weight._get_measure()
                    logger.info(f'Feed weight: {end_weight}')
                    time.sleep(1)
                    if _get_relay_state(int(relay_pin)) == False: # На всякий случай
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
                    post_data = _post_request(eventTime, feed_time_rounded, animal_id, final_weight_rounded, end_weight)    #400
                    _send_post(post_data)
                weight.disconnect()
        except Exception as e:
            logger.error(f'Error: {e}')
            weight.disconnect()

def process_calibration(animal_id):
    try:
        if animal_id == cfg.get_setting("Calibration", "taring_rfid"):
            _rfid_offset_calib()
        elif animal_id == cfg.get_setting("Calibration", "scaling_rfid"):
            _rfid_scale_calib()        
    except Exception as e:
        logger.error(f'Calibration with RFID: {e}')

def process_feeding(weight):
    try:
        start_weight = _first_weight(weight)       
        start_time = timeit.default_timer()            
        animal_id = __connect_rfid_reader()
            
        logger.info(f'Start weight: {start_weight}')      
        logger.info(f'Start time: {start_time}')           
        logger.info(f'Animal ID: {animal_id}')

        process_calibration(animal_id, logger) 
    except Exception as e:
        logger.error(f'Calibration with RFID: {e}')

def feeder_module_v2():
    _calibrate_or_start(cfg, logger)
    port = cfg.get_setting("Parameters", "arduino_port")     
    relay_pin = cfg.get_setting("Relay", "sensor_pin")
    logger.debug("Feeder project.")

    while True:  # Функция, определяющая, должен ли цикл продолжаться
        try:        
            if _get_relay_state(int(relay_pin)):  
                with create_connection(port) as weight:
                    process_feeding(weight, relay_pin, cfg, logger)
        except SpecificException as e:  # Замените на конкретный тип исключения
            logger.error(f'Error: {e}')