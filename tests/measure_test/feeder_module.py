"""Feeder version 3. Edition by Suieubayev Maxat.
feeder_module.py - это модуль функции кормушки. 
Contact number +7 775 818 48 43. Email maxat.suieubayev@gmail.com"""

#!/usr/bin/sudo python3

from requests.exceptions import HTTPError
from loguru import logger
import _config as cfg
import adc_data as ADC
import time
import threading
import queue
import time


def start_obj(port):
    try:
        obj = ADC.ArduinoSerial(port)
        obj.connect()
        offset, scale = float(cfg.get_setting("Calibration", "offset")), float(cfg.get_setting("Calibration", "scale"))
        obj.set_offset(offset)
        obj.set_scale(scale)
        return obj
    except Exception as e:
        logger.error(f'Error connecting: {e}')


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


def calibrate_or_start():
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
        logger.error(f'Error during calibration or starting measurement: {e}')


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
        logger.error(f'calibrate Fail')
        arduino.disconnect()


def measure_weight(obj):
    try:
        weight = obj.calc_mean()
        #logger.debug(f'{type(weight_finall)}, {type(weight_arr)}, {type(start_timedate)}')
        return weight
    except Exception as e:
        logger.error(f'measure_weight Error: {e}')

