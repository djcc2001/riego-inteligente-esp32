#include <Arduino.h>ear
#include <Wire.h>
#include <Adafruit_AHTX0.h>

// Sensores: HW-390 (capacitivo GPIO34) + AHT10 (temp/hum I2C 21/22)

Adafruit_AHTX0 aht;
#define SOIL_PIN 34

void setup() {
  Serial.begin(115200);
  delay(1000);
  Wire.begin(21, 22); // AHT10: SDA=GPIO21, SCL=GPIO22
  if (!aht.begin()) {
    Serial.println("ERROR: No se encontro el AHT10.");
    while (1) delay(10);
  }
  // CSV: timestamp_rel(millis), soil_raw, temperatura, humedad_ambiental
  Serial.println("ts,soil_raw,temp,hum");
}

void loop() {                                 // Salida CSV cada 10s: soil_raw, temp, hum
  int soilRaw = analogRead(SOIL_PIN);
  sensors_event_t hum, temp;
  aht.getEvent(&hum, &temp);

  Serial.print(millis());
  Serial.print(",");
  Serial.print(soilRaw);
  Serial.print(",");
  Serial.print(temp.temperature);
  Serial.print(",");
  Serial.println(hum.relative_humidity);

  delay(10000);
}
