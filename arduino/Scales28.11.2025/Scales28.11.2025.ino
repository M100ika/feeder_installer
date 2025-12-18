#include "HX711.h"

// HX711 circuit wiring
const int LOADCELL_DOUT_PIN = 6;  // DOUT
const int LOADCELL_SCK_PIN  = 5;  // SCK

HX711 scale;

void setup() {
  // Запускаем UART
  Serial.begin(9600);

  // Инициализируем HX711, коэффициент усиления 128 на канале A
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN, 128);

  // Если нужен цифровой датчик на пине 2 — оставляем
  pinMode(2, INPUT);
}

void loop() {
  if (Serial.available() > 0) {
    int inByte = Serial.read();

    if (inByte == 1) {
      // Рукопожатие: "я жив"
      Serial.println("Arduino");
    }
    else if (inByte == 2) {
      // Запрос АЦП: читаем HX711 и отправляем 4 байта (big-endian)

      // Блокирующее чтение с HX711
      long adc_val = scale.read();  // 24-битное значение, sign-extended в 32 бита

      // Преобразуем в 4 байта big-endian
      uint8_t array[4];
      array[0] = (adc_val >> 24) & 0xFF;
      array[1] = (adc_val >> 16) & 0xFF;
      array[2] = (adc_val >> 8)  & 0xFF;
      array[3] = (adc_val)       & 0xFF;

      Serial.write(array, 4);
    }
  }

}
