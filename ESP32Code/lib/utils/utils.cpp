#include <utils.h>

#pragma region VARIABILI GLOBALI

char DEVICE_ID[24];
char AWS_SHADOW_DELTA_TOPIC[128];
char AWS_SHADOW_UPDATE_TOPIC[128];

extern const char AWS_CERT_CA[] PROGMEM;
extern const char AWS_CERT_CRT[] PROGMEM;
extern const char AWS_CERT_PRIVATE[] PROGMEM;

Thresholds thresholds = {15.0, 30.0, 40.0, 70.0, 400.0, 10000.0, 30.0, 80.0};

DHT dht(DHT_SENSOR, DHT_TYPE);
WiFiClientSecure espClient;
PubSubClient client(espClient);
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

float temperature = 0;
float humidity = 0;
float light = 0;
float soil_moisture = 0;
float battery_level = 100.0;

char temperatureStr[8];
char humidityStr[8];
char lightStr[8];
char soilStr[8];
char waterStr[8];
char batteryStr[8];

bool water_detected = false;

#pragma endregion

void init_device_id()
{
    uint64_t chipId = ESP.getEfuseMac();
    uint32_t uniqueNum = (uint32_t)(chipId & 0xFFFF); // 4 cifre

    snprintf(DEVICE_ID, sizeof(DEVICE_ID), "esp32-%04x", uniqueNum);
    snprintf(AWS_SHADOW_DELTA_TOPIC, sizeof(AWS_SHADOW_DELTA_TOPIC), "$aws/things/%s/shadow/update/delta", DEVICE_ID);
    snprintf(AWS_SHADOW_UPDATE_TOPIC, sizeof(AWS_SHADOW_UPDATE_TOPIC), "$aws/things/%s/shadow/update", DEVICE_ID);
}

void mqtt_callback(char* topic, byte* payload, unsigned int length)
{
    char message[512];
    unsigned int len = min(length, (unsigned int)511);

    memcpy(message, payload, len);
    message[len] = '\0';

    if (strcmp(topic, AWS_SHADOW_DELTA_TOPIC) == 0)
        handle_shadow_delta(message);
}

void setup_wifi()
{
    WiFiManager wm;

    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("WiFi NOT FOUND");
    display.println("Connect to SSID: ");
    display.printf("%s-Setup\n", DEVICE_ID);
    display.display();

    // Se non si connette alle reti salvate, crea un AP col nome del dispositivo
    char apName[30];

    snprintf(apName, sizeof(apName), "%s-Setup", DEVICE_ID);

    if(!wm.autoConnect(apName))
    {
        Serial.println("WiFi Error, restarting...");

        delay(3000);
        ESP.restart();
    } 

    Serial.println("\nWiFi Connected!");
    display.clearDisplay();
    display.setCursor(0,0);
    display.println("WiFi Connected!");
    display.display();
    delay(1000);

    // Configura i certificati per SSL
    espClient.setCACert(AWS_CERT_CA);
    espClient.setCertificate(AWS_CERT_CRT);
    espClient.setPrivateKey(AWS_CERT_PRIVATE);
}

void reconnect_MQTT()
{
    while (!client.connected()) 
    {
        Serial.printf("Connecting MQTT as %s\n", DEVICE_ID);
        display.println("Connecting MQTT...");
        display.display();

        if (client.connect(DEVICE_ID)) 
        {
            client.subscribe(AWS_SHADOW_DELTA_TOPIC);
            Serial.println("Connected to AWS IoT");
        }
        else 
        {
            Serial.print("Failed, rc=");
            Serial.print(client.state());
            Serial.println(" trying again in 5s");

            delay(5000);
        }
    }
}

void read_sensors()
{
    temperature = dht.readTemperature();
    humidity = dht.readHumidity();
    light = analogRead(LIGHT_SENSOR);
    soil_moisture = map(analogRead(SOIL_HUMIDITY_SENSOR), 4095, 0, 0, 100);
    water_detected = (analogRead(WATER_SENSOR) > 500);
}

void publish_data()
{
    dtostrf(temperature, 1, 1, temperatureStr);
    dtostrf(humidity, 1, 1, humidityStr);
    dtostrf(light, 1, 0, lightStr);
    dtostrf(soil_moisture, 1, 1, soilStr);
    dtostrf(battery_level, 1, 0, batteryStr);
    strcpy(waterStr, water_detected ? "true" : "false");

    char topic[128];

    auto pub = [&](const char* subtopic, const char* val) 
    {
        snprintf(topic, sizeof(topic), "smartplant/%s/%s", DEVICE_ID, subtopic);
        client.publish(topic, val);
    };

    pub("temperature", temperatureStr);
    pub("humidity", humidityStr);
    pub("light", lightStr);
    pub("soil", soilStr);
    pub("battery", batteryStr);
    pub("rain", waterStr);

    Serial.printf("Device: %s\n", DEVICE_ID);
    Serial.printf("Temp: %s C\n", temperatureStr);
    Serial.printf("Hum: %s %%\n", humidityStr);
    Serial.printf("Soil: %s %%\n", soilStr);
    Serial.printf("Light: %s LUX\n", lightStr);
    Serial.printf("Batt: %s %%\n", batteryStr);
    Serial.printf("Water: %s\n", water_detected ? "YES" : "NO");
    Serial.println("-----------------------");
}

void irrigate(int duration_seconds)
{
    Serial.print("Irrigazione: ");
    Serial.println(duration_seconds);
    
    unsigned long start = millis();
    digitalWrite(RELAY_PIN, HIGH);
    
    while (millis() - start < (unsigned long)duration_seconds * 1000) 
    {
        client.loop(); 
        delay(10);
    }
    
    digitalWrite(RELAY_PIN, LOW);
}

void handle_shadow_delta(const char* json)
{
    if (strstr(json, "\"pump\":true")) 
    {
        int duration = 30;
        char* ptr = strstr(json, "\"duration\":");

        if (ptr) 
            duration = atoi(ptr + 11);

        irrigate(duration);
        client.publish(AWS_SHADOW_UPDATE_TOPIC, "{\"state\":{\"reported\":{\"pump\":false}}}");
    }

    auto updateFloat = [&](const char* key, float &var) 
    {
        char* ptr = strstr(json, key);

        if (ptr) 
        {
            ptr = strchr(ptr, ':');

            if (ptr) 
                var = atof(ptr + 1);
        }
    };

    updateFloat("\"temp_min\"", thresholds.temp_min);
    updateFloat("\"temp_max\"", thresholds.temp_max);
    updateFloat("\"humidity_min\"", thresholds.humidity_min);
    updateFloat("\"humidity_max\"", thresholds.humidity_max);
    updateFloat("\"light_min\"", thresholds.light_min);
    updateFloat("\"light_max\"", thresholds.light_max);
    updateFloat("\"soil_min\"", thresholds.soil_min);
    updateFloat("\"soil_max\"", thresholds.soil_max);

    save_thresholds();
    
    char reported[320];

    snprintf(reported, sizeof(reported), 
        "{\"state\":{\"reported\":{\"temp_min\":%.1f,\"temp_max\":%.1f,\"humidity_min\":%.1f,\"humidity_max\":%.1f,\"light_min\":%.1f,\"light_max\":%.1f,\"soil_min\":%.1f,\"soil_max\":%.1f,\"config_synced\":true}}}",
        thresholds.temp_min, thresholds.temp_max, thresholds.humidity_min, thresholds.humidity_max, thresholds.light_min, thresholds.light_max, thresholds.soil_min, thresholds.soil_max);
    
    client.publish(AWS_SHADOW_UPDATE_TOPIC, reported);
}

void load_thresholds()
{
    byte magic;

    EEPROM.get(0, magic);
    
    if (magic == EEPROM_MAGIC) 
        EEPROM.get(1, thresholds);
}

void save_thresholds()
{
    EEPROM.put(0, (byte)EEPROM_MAGIC);
    EEPROM.put(1, thresholds);
    EEPROM.commit();
}

void setup_display()
{
    Wire.begin(OLED_SDA, OLED_SCL);

    if(display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) 
    {
        display.clearDisplay();
        display.setTextColor(SSD1306_WHITE);
        display.setTextSize(1);
        display.setCursor(0,0);
        display.display();
    }
}

void update_display()
{
    String deviceIdStr = String(DEVICE_ID);
    deviceIdStr.toUpperCase();

    display.clearDisplay();
    display.setTextSize(1);

    display.setCursor(0, 0);
    display.printf("DeviceID: %s\n", deviceIdStr.c_str());
    display.drawFastHLine(0, 10, 128, SSD1306_WHITE);
    display.setCursor(0, 12);
    display.printf("Temperature: %s C\n", temperatureStr);
    display.printf("Humidity: %s %%\n", humidityStr);
    display.printf("Moisture: %s %%\n", soilStr);
    display.printf("Lux: %s\n", lightStr);
    display.printf("Battery: %s %%\n", batteryStr);
    
    display.display(); 
}
