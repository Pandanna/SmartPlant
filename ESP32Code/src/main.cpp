#include <utils.h>

unsigned long last_publish = 0;

#pragma region MAIN

void setup()
{
    Serial.begin(9600);

    pinMode(RELAY_PIN, OUTPUT);
    digitalWrite(RELAY_PIN, LOW);

    dht.begin();
    EEPROM.begin(EEPROM_SIZE);
    load_thresholds();
    setup_display();

    init_device_id();
    setup_wifi();

    client.setServer(AWS_IOT_ENDPOINT, AWS_IOT_PORT);
    client.setCallback(mqtt_callback);
    
    Serial.println("Setup complete");
}

void loop()
{
    if (!client.connected()) 
    {
        reconnect_MQTT();
        read_sensors();
        publish_data();
        update_display();

        last_publish = millis();
    }

    client.loop();

    unsigned long now = millis();

    if ((now - last_publish) >= INTERVALLO) 
    {
        read_sensors();
        publish_data();
        update_display();

        last_publish = now;
    }

    delay(100);
}

#pragma endregion
