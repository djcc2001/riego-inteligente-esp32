#include <Arduino.h>
#include <Wire.h>
#include <WiFiManager.h>
#include <HTTPClient.h>
#include <Adafruit_AHTX0.h>
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "modelo_riego.h"

// ---------- Sensores ----------
Adafruit_AHTX0 aht;
#define SOIL_PIN 34

// ---------- Red / servidor ----------
WiFiManager wm;
const char* SERVER_URL = "http://3.129.19.217:3003/api/lectura";

// ---------- Modelo Logistic Regression (TFLite Micro) ----------
constexpr int kTensorArenaSize = 10 * 1024;
alignas(16) uint8_t tensor_arena[kTensorArenaSize];

const tflite::Model* model = nullptr;
tflite::MicroInterpreter* interpreter = nullptr;
TfLiteTensor* input = nullptr;
TfLiteTensor* output = nullptr;

// Normalizacion (del scaler_final entrenado en Colab)
const float MEAN[3]  = {1559.949f, 18.747f, 29.322f};   // soil_raw, temp, hum
const float SCALE[3] = {567.371f,  5.106f,  7.900f};

// Orden de clases segun el LabelEncoder: 0=OPTIMO, 1=SATURADO, 2=SECO
const char* CLASES[3] = {"OPTIMO", "SATURADO", "SECO"};

// ---------- Inicializacion del modelo ----------
bool inicializarModelo() {
  model = tflite::GetModel(modelo_riego_tflite);
  if (model->version() != TFLITE_SCHEMA_VERSION) {
    Serial.println("ERROR: version de schema no coincide.");
    return false;
  }

  static tflite::AllOpsResolver resolver;
  static tflite::MicroInterpreter static_interpreter(
      model, resolver, tensor_arena, kTensorArenaSize);
  interpreter = &static_interpreter;

  if (interpreter->AllocateTensors() != kTfLiteOk) {
    Serial.println("ERROR: AllocateTensors fallo.");
    return false;
  }

  input = interpreter->input(0);
  output = interpreter->output(0);
  return true;
}

// ---------- Envio HTTP con reintentos ----------
void enviarDatos(int soilRaw, float temperatura, float humedadAmbiental,
                  const char* prediccion, float confianza) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi no conectado, se omite el envio.");
    return;
  }

  String payload = "{\"device_id\":\"esp32-001\",";
  payload += "\"soil_raw\":" + String(soilRaw) + ",";
  payload += "\"temp\":" + String(temperatura, 2) + ",";
  payload += "\"hum\":" + String(humedadAmbiental, 2) + ",";
  payload += "\"prediccion\":\"" + String(prediccion) + "\",";
  payload += "\"confianza\":" + String(confianza, 3) + "}";

  const int MAX_INTENTOS = 3;
  for (int intento = 1; intento <= MAX_INTENTOS; intento++) {
    HTTPClient http;
    http.begin(SERVER_URL);
    http.addHeader("Content-Type", "application/json");
    http.setConnectTimeout(10000);
    http.setTimeout(10000);

    int httpCode = http.POST(payload);
    Serial.print("Intento "); Serial.print(intento);
    Serial.print(" - Codigo HTTP: "); Serial.println(httpCode);

    if (httpCode == 200) {
      Serial.println("Respuesta: " + http.getString());
      http.end();
      return;
    }

    http.end();
    if (intento < MAX_INTENTOS) {
      delay(1500);
    }
  }
  Serial.println("Fallo el envio tras " + String(MAX_INTENTOS) + " intentos.");
}

// ---------- Setup ----------
void setup() {
  Serial.begin(115200);
  delay(1000);

  // Sensores
  if (!aht.begin()) {
    Serial.println("ERROR: No se encontro el AHT10.");
    while (1) delay(10);
  }
  Serial.println("AHT10 OK.");

  // WiFi
  bool conectado = wm.autoConnect("RiegoESP32-Setup");
  if (!conectado) {
    Serial.println("No se pudo conectar. Reiniciando...");
    ESP.restart();
  }
  Serial.println("WiFi conectado: " + WiFi.localIP().toString());
  delay(2000);

  // Modelo TFLite
  Serial.println("Inicializando modelo...");
  if (!inicializarModelo()) {
    Serial.println("ERROR fatal inicializando el modelo.");
    while (1) delay(10);
  }
  Serial.println("Modelo cargado correctamente.");
}

// ---------- Loop principal ----------
void loop() {
  // 1. Leer sensores (valores CRUDOS)
  int soilRaw = analogRead(SOIL_PIN);
  sensors_event_t humidity, temp;
  aht.getEvent(&humidity, &temp);
  float temperatura = temp.temperature;
  float humedadAmbiental = humidity.relative_humidity;

  // 2. Normalizar + cuantizar usando los parametros reales del tensor
  float valoresNorm[3] = {
    (soilRaw - MEAN[0]) / SCALE[0],
    (temperatura - MEAN[1]) / SCALE[1],
    (humedadAmbiental - MEAN[2]) / SCALE[2]
  };

  for (int i = 0; i < 3; i++) {
    int32_t q = (int32_t)round(valoresNorm[i] / input->params.scale) + input->params.zero_point;
    if (q < -128) q = -128;
    if (q > 127) q = 127;
    input->data.int8[i] = (int8_t)q;
  }

  // 3. Inferencia
  if (interpreter->Invoke() != kTfLiteOk) {
    Serial.println("ERROR: fallo la inferencia.");
    delay(5000);
    return;
  }

  // 4. Des-cuantizar salida y elegir la clase con mayor probabilidad
  float salida[3];
  for (int i = 0; i < 3; i++) {
    salida[i] = (output->data.int8[i] - output->params.zero_point) * output->params.scale;
  }

  int claseIdx = 0;
  for (int i = 1; i < 3; i++) {
    if (salida[i] > salida[claseIdx]) claseIdx = i;
  }
  const char* prediccion = CLASES[claseIdx];
  float confianza = salida[claseIdx];

  // 5. Mostrar por Serial
  Serial.println("----- Lectura -----");
  Serial.print("soil_raw="); Serial.print(soilRaw);
  Serial.print(" temp="); Serial.print(temperatura);
  Serial.print(" hum="); Serial.println(humedadAmbiental);
  Serial.print("Prediccion: "); Serial.print(prediccion);
  Serial.print(" (confianza="); Serial.print(confianza, 3); Serial.println(")");

  // 6. Enviar a AWS
  enviarDatos(soilRaw, temperatura, humedadAmbiental, prediccion, confianza);

  delay(10000);
}