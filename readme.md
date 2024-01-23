# Проект: Feeder
**Версия**: 7.1  
**Автор**: Суйеубаев Максат Жамбылович
**Email**: maxat.suieubayev@gmail.com  

## Введение
Проект "Feeder" является продвинутым решением для сбора и отправки данных с устройства, известного как "Кормушка". Он разработан для эффективного мониторинга и управления процессом кормления животных, используя последние технологии и инновации.

### Основные Особенности Версии 7.1
- **Скачивание и установка одной командой**: Проект теперь можно установить с помощью единственной команды, упрощая начальную настройку и развертывание.
  ```bash
   curl -sSL https://raw.githubusercontent.com/M100ika/feeder_installer/main/install.sh | bash
- **Улучшенный сбор данных**: Версия 2.2 включает в себя новый и усовершенствованный метод сбора весовых данных, значительно повышая точность и надежность измерений.
- **Интеграция с Arduino**: С этой версии система оснащена платформой Arduino для сбора информации от тензодатчиков, что позволяет получать более детализированные и точные данные о весе.
- **Отключение ведения журнала в config.ini**: Добавлена возможность отключения ведения журнала через настройки в config.ini.
- **Журналы хранятся 1 месяц**: Журналы системы теперь хранятся в течение 10 дней, обеспечивая оптимальный баланс между историей и использованием дискового пространства.
- **Отдельный журнал ошибок**: Для упрощения отладки и мониторинга в систему добавлен отдельный журнал для записи ошибок.
- **Дополнительные конфигурационные файлы**: Введены новые конфигурационные файлы, расширяющие возможности настройки и кастомизации проекта.
- **Добавление калибровки с помощью RFID меток**: Добавлена дополнительная возможность калибровки коэффициентов с помощью rfid меток
- **Расширение файла config.ini**: Файл config.ini получил дополнительные редактируемые параметры

Этот проект посвящен созданию удобного и надежного инструмента для фермеров и владельцев животных, стремящихся оптимизировать и автоматизировать процесс кормления. С каждым обновлением мы стремимся расширять возможности "Кормушки", улучшая её функциональность и удобство использования.

## Структрука проекта:
feeder_installer/
│
├── arduino/                  # Все файлы, относящиеся к коду Arduino
│   ├── HX711-master.zip      # Библиотека АЦП HX711
│   └── SerialCallResponse_RPi/  # Папка проекта для Arduino
│       └──SerialCallResponse_RPi.ino   # Проект Arduino
│
├── feeder_log                # Журналы проекта
│   ├── feeder.log            # Журнал всех сообщений
│   └── error_log            
│       └── errors.log        # Журнал ошибок
│
├── src/                      # Исходный код Python проекта
│   ├── adc_data.py           # Модуль для работы с АЦП
│   ├── _config.py            # Модуль конфигурационных настроек
│   ├── feeder_module.py      # Модуль функций кормушки
│   ├── headers.py            # Заголовки, общие константы
│   ├── main_feeder.py        # Основной исполняемый скрипт
│   └── sql_database.py       # Взаимодействие с базой данных
│
├── tests/                    # Тесты проекта
│   ├── relay.py              # Тест датчика прерывания луча
│   ├── rfid_reader_test.py   # Тест модуля считывания rfid метов
│   ├── test_post.py          # Тест связи с сервером
│   ├── measure_test          # Папка теста датчика веса
│       └──...
│
├── config/                   # Конфигурационные файлы
│   ├── config.ini            # Настройки проекта
│   └── feeder.service        # Файл сервиса для systemd
|
├── docs/                     # Документация
│   └── feeder_doc/           # Папка документации кормушки
│        └── feeder_main.puml # Алгоритм главного файла кормушки  
│
├── scripts/                  # Дополнительные скрипты
│   └── install.sh            # Скрипт установки
│
└── README.md                 # Краткое описание проекта


## Инструкция по запуску проекта:
    1. Перед началом работы с данным проектом создайте в распберри папку 
mkdir /pi/home/feeder_v2.1. 
    2. Перенесите файлы adc_data.py, config.py, config.ini, headers.py, 
feeder_module.py, main_feeder.py
    3. В случае если устройсво новое необходимо заполнить данные об этом 
устройсве пройдя по следующей ссылке 
https://docs.google.com/spreadsheets/d/1XeYxa0_bUGq_OvfEMQHy445ZObuPY38OtOF7z158Gro/edit#gid=0
    4. Заполните файл config.ini, пример в пункте 5
    5. Если устройство использовалось ранее возьмите необходимые данные
из таблицы по ссылке выше и перенесите данные в файл config.ini. К примеру
    *****************************************
    [Parameters]
    model = pcf_fdr_07
    type = Feeder
    serial_number = feeder0423v21-1                             <- Здесь вводим данные из таблицы
    url = https://smart-farm.kz:8502/api/v2/RawFeedings
    median_url = http://194.4.56.86:8501/api/weights
    array_url = https://smart-farm.kz:8502/v2/OneTimeWeighings
    arduino_port = /dev/ttyACM0                                 <- Проверить с помощью команды ls /dev/tty* . Варианты: ttyACM0, ttyUSB0 или ttyUSB1
    debug = 1                                                   <- Ставим 0 после проведения тестов. 0 - отключает логи кроме error. 
    null_rfid = b'435400040001'   
    rfid_read_times = 10                                        <- 10 раз опрашиваем считыватель


    [Calibration]
    taring_rfid = b'435400041111'                               <- RFID метка для автоматического тарирования. Изменить на нужный
    scaling_rfid = b'435400041111'                              <- RFID метка для автоматической калибровки. Изменить на нужный
    weight = 80                                                 <- Эталонный вес для калибровки. Изменить на нужный
    offset = 16766507
    scale = -3358.285714285714

    [DbId]
    id = 30
    version = 7.1

    [Relay]
    sensor_pin = 17
    ******************************************
    6. Запустите файл main_feeder.py
    7. Дальнейшие действия описаны в файле scales/max_scales/scales_without_sprayer/Version6.1/readme.txt

## Инструкция по Калибровке Системы Взвешивания
**Настройка Конфигурации**
Перед началом калибровки необходимо настроить файл конфигурации **config.ini**:
    **1.Тарирование:**
    - taring_rfid: введите RFID номер метки тарирования.
    **2. Калибровка Веса:**
    - scaling_rfid: введите RFID номер метки калибровки веса.
    - weight: укажите вес, на который будет производиться калибровка.

**Процедура Тарирования**
    1. Подготовка:
    - Убедитесь, что на весах ничего нет и показания весов равны нулю.
    2. Выполнение:
    - Закройте датчик прерывания луча.
    - Считайте метку taring_rfid.
    - Через секунду после считывания метки откройте датчик.

**Процедура Калибровки Веса**
    1. Подготовка:
    - Установите на весах заданный вес, указанный в параметре config.ini/weight.
    2. Выполнение:
    - Закройте датчик прерывания луча.
    - Считайте метку scaling_rfid.
    - Через секунду после считывания метки откройте датчик.
    
**Примечание:** Важно проводить процедуру калибровки в условиях, исключающих внешние воздействия (например, вибрации или движение), которые могут повлиять на точность измерений.
