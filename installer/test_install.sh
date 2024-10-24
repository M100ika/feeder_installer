#!/bin/bash

# Определение абсолютного пути к скрипту
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_PATH="$(dirname "$SCRIPT_PATH")"

# Функция для проверки, выполняется ли скрипт на Raspberry Pi
is_raspberry() {
    uname -a | grep -qi "arm"
    return $?
}

# Проверяем, является ли устройство Raspberry Pi
if ! is_raspberry; then
    PARAM_INI_PATH="$PROJECT_PATH/submod/settings.ini"
    echo -e "[PATHS]\nPROJECT_PATH=$PROJECT_PATH" > "$PARAM_INI_PATH"

    # Запуск Python скрипта для создания ярлыка
    python3 "$PROJECT_PATH/submod/scripts/gui/_create_shortcut.py"
else
    # Запуск Python скрипта для создания ярлыка
    PARAM_INI_PATH="$PROJECT_PATH/submod/settings.ini"
    echo -e "[PATHS]\nPROJECT_PATH=$PROJECT_PATH" > "$PARAM_INI_PATH"
    python3 "/opt/feeder_project/scripts/gui/_create_shortcut.py"
fi
