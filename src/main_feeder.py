"""Feeder version 3. Edition by Suieubayev Maxat.
main_feeder.py - это файл с основной логикой работы кормушки. 
Contact number +7 775 818 48 43. Email maxat.suieubayev@gmail.com"""

#!/usr/bin/sudo python3

import headers as hdr

requirement_list = ['loguru', 'requests', 'numpy', 'RPi.GPIO']
hdr.install_packages(requirement_list)

import feeder_module as fdr
from loguru import logger
from time import sleep
import _config as cfg
import os

debug_level = "DEBUG" if int(cfg.get_setting("Parameters", "debug")) == 1 else "CRITICAL"

"""Инициализация logger для хранения записи о всех действиях программы"""
logger.add('../feeder_log/feeder.log', format="{time} {level} {message}", 
level=debug_level, rotation="1 day", retention= '1 month', compression="zip")  

logger.add('../feeder_log/error_log/errors.log', format="{time} {level} {message}", 
level="ERROR", rotation="1 day", retention= '1 month', compression="zip") 

if not os.path.exists("../config/config.ini"):    # Если конфиг файла не существует
    cfg.create_config()     # Создать конфиг файл
        
       
@logger.catch
def main():
    fdr.feeder_module()

main()



