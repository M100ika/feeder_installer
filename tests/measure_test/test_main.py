import _feeder_module as fdr
from loguru import logger
import _config as cfg
import os

debug_level = "DEBUG" if int(cfg.get_setting("Parameters", "debug")) == 1 else "CRITICAL"

"""Инициализация logger для хранения записи о всех действиях программы"""
logger.add('../feeder_log/feeder.log', format="{time} {level} {message}", 
level=debug_level, rotation="1 day", retention= '1 month', compression="zip")  

if not os.path.exists("../../config/config.ini"):    # Если конфиг файла не существует
    cfg.create_config()     # Создать конфиг файл


def main():
    logger.info(f'\033[1;35mFeeder project. Weight measurment test file.\033[0m')
    fdr.calibrate_or_start()
    port = cfg.get_setting("Parameters", "arduino_port")  
    while True:
        arduino_start = fdr.start_obj(port)
        weight = fdr.measure_weight(arduino_start)
        logger.info(f"Weight is: {weight}\n")
        arduino_start.disconnect()
    

main()