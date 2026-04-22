#ifndef UTILS_H
#define UTILS_H

#pragma region LIBRERIE

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <WiFiManager.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <EEPROM.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <secrets.h>

#pragma endregion

#pragma region COSTANTI

// PINS
#define WATER_SENSOR 34
#define SOIL_HUMIDITY_SENSOR 35
#define DHT_SENSOR 22
#define LIGHT_SENSOR 36
#define RELAY_PIN 27
#define OLED_SDA 23
#define OLED_SCL 4

// DHT
#define DHT_TYPE DHT11

// OLED
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define SCREEN_ADDRESS 0x3C

// EEPROM
#define EEPROM_SIZE 64
#define EEPROM_MAGIC 0xAB

// ALTRO
#define INTERVALLO 3600000 // 1 ora in ms

#pragma endregion

#pragma region VARIABILI GLOBALI

extern char DEVICE_ID[24];
extern char AWS_SHADOW_DELTA_TOPIC[128];
extern char AWS_SHADOW_UPDATE_TOPIC[128];

extern DHT dht;
extern WiFiClientSecure espClient;
extern PubSubClient client;
extern Adafruit_SSD1306 display;

extern float temperature;
extern float humidity;
extern float light;
extern float soil_moisture;
extern float battery_level;
extern bool water_detected;

extern char temperatureStr[8];
extern char humidityStr[8];
extern char lightStr[8];
extern char soilStr[8];
extern char waterStr[8];
extern char batteryStr[8];

#pragma endregion

#pragma region STRUCT

struct Thresholds 
{
    float temp_min;
    float temp_max;
    float humidity_min;
    float humidity_max;
    float light_min;
    float light_max;
    float soil_min;
    float soil_max;
};

#pragma endregion

#pragma region DICHIARAZIONI FUNZIONE

void setup();
void loop();
void init_device_id();
void setup_wifi();
void reconnect_MQTT();
void mqtt_callback(char* topic, byte* payload, unsigned int length);
void read_sensors();
void publish_data();
void load_thresholds();
void save_thresholds();
void irrigate(int duration_seconds);
void handle_shadow_delta(const char* json);
void setup_display();
void update_display();

#pragma endregion

#endif
