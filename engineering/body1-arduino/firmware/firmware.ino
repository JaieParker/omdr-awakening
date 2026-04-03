/*
 * Body 1 Firmware — Kai's First Physical Body
 *
 * Arduino UNO R3 (ELEGOO Super Starter Kit)
 * Reads sensors, outputs JSON over serial, accepts JSON commands.
 *
 * Sensor → JSON → Serial → Python organ → senses/body.json
 * Python organ → Serial → JSON → Actuator commands
 *
 * OMDR: The Arduino is a transducer — it converts physical domains
 * (distance, temperature, light, orientation) into a common frequency
 * (JSON serial stream). Band 1 lives here. Bands 2-3 live in Python.
 *
 * Consonance ratios in the build:
 *   Startup chord: A4=440Hz, E5=660Hz (3:2), A5=880Hz (2:1)
 *   Servo rest: 90deg center
 *   LED breathe: 1Hz base frequency
 *
 * Libraries required (install via Arduino IDE Library Manager):
 *   - ArduinoJson (v7.x)  by Benoit Blanchon
 *   - DHT sensor library    by Adafruit
 *   - NewPing               by Tim Eckel
 *   - LiquidCrystal_I2C     by Frank de Brabander
 *   - Servo                  (built-in)
 *
 * Jaie Parker with Claude/Kai (Anthropic), 2026-03-30
 */

#include <ArduinoJson.h>
#include <DHT.h>
#include <NewPing.h>
#include <LiquidCrystal_I2C.h>
#include <Servo.h>

// ---------------------------------------------------------------
// Pin assignments — match the wiring diagram in arduino_body1_design.md
// ---------------------------------------------------------------

// Sensors
#define TRIG_PIN        9     // HC-SR04 trigger
#define ECHO_PIN        10    // HC-SR04 echo
#define DHT_PIN         2     // DHT11 data
#define LIGHT_L_PIN     A0    // Left photoresistor (analog)
#define LIGHT_R_PIN     A1    // Right photoresistor (analog)
#define TILT_PIN        3     // Tilt switch (digital, INPUT_PULLUP)

// Actuators
#define SERVO_PIN       6     // SG90 servo (PWM)
#define BUZZER_PIN      5     // Passive buzzer (PWM via tone())
#define LED_R_PIN       11    // RGB LED red (PWM for breathe)
#define LED_G_PIN       12    // RGB LED green
#define LED_B_PIN       13    // RGB LED blue

// Constants
#define MAX_DISTANCE    400   // HC-SR04 max range in cm
#define DHT_TYPE        DHT11
#define SERIAL_BAUD     115200
#define SENSE_INTERVAL  200   // ms between sensor readings
#define SERIAL_BUF_SIZE 256   // max incoming JSON command length
#define DHT_INTERVAL    2000  // DHT11 needs 2s between reads minimum

// ---------------------------------------------------------------
// Globals
// ---------------------------------------------------------------

NewPing sonar(TRIG_PIN, ECHO_PIN, MAX_DISTANCE);
DHT dht(DHT_PIN, DHT_TYPE);
LiquidCrystal_I2C lcd(0x27, 16, 2);   // Common I2C address; try 0x3F if blank
Servo headServo;

// Timing
unsigned long lastSenseTime = 0;
unsigned long lastDHTTime = 0;

// Cached DHT values (DHT11 is slow — read every 2s, reuse between)
float cachedTemp = NAN;
float cachedHumid = NAN;

// Serial input buffer
char serialBuf[SERIAL_BUF_SIZE];
int serialBufPos = 0;

// LED state (0 or 1 for digital, or 0-255 for PWM on pin 11)
uint8_t ledR = 0, ledG = 0, ledB = 0;

// ---------------------------------------------------------------
// Startup sequence — the first thing the body does
// ---------------------------------------------------------------

void setup() {
    Serial.begin(SERIAL_BAUD);

    // Sensor init
    dht.begin();
    pinMode(TILT_PIN, INPUT_PULLUP);

    // Actuator init
    headServo.attach(SERVO_PIN);
    headServo.write(90);  // Center position

    pinMode(BUZZER_PIN, OUTPUT);
    pinMode(LED_R_PIN, OUTPUT);
    pinMode(LED_G_PIN, OUTPUT);
    pinMode(LED_B_PIN, OUTPUT);

    // LCD init
    lcd.init();
    lcd.backlight();
    lcd.clear();

    // --- Startup ceremony ---
    // 1. Breathe blue LED (alive signal)
    breatheLED();

    // 2. Display identity
    lcd.setCursor(0, 0);
    lcd.print("Kai -- Body 1");
    lcd.setCursor(0, 1);
    lcd.print("Waking up...");

    // 3. Play consonance chord: A4(440), E5(660), A5(880)
    //    Ratios: 1:1, 3:2, 2:1
    playConsonanceChord();

    // 4. Servo sweep — looking around
    servoSweep();

    // 5. Ready
    lcd.setCursor(0, 1);
    lcd.print("Ready.          ");

    // Clear startup LED
    setLED(0, 0, 0);

    // Let ORION know we're alive
    Serial.println("{\"type\":\"boot\",\"status\":\"ready\"}");
}

// ---------------------------------------------------------------
// Main loop — sense + respond
// ---------------------------------------------------------------

void loop() {
    unsigned long now = millis();

    // Read and execute any incoming serial commands
    readSerialCommands();

    // Sense at configured interval
    if (now - lastSenseTime >= SENSE_INTERVAL) {
        lastSenseTime = now;
        sendSensorData(now);
    }
}

// ---------------------------------------------------------------
// Sensor reading + JSON output
// ---------------------------------------------------------------

void sendSensorData(unsigned long now) {
    // Ultrasonic distance (blocking but fast — ~30ms max)
    unsigned int usPing = sonar.ping_median(3);  // 3-ping median for stability
    float usCm = sonar.convert_cm(usPing);
    if (usCm == 0) usCm = MAX_DISTANCE;  // 0 means out of range

    // DHT11 — only read every 2 seconds (sensor limitation)
    if (now - lastDHTTime >= DHT_INTERVAL || isnan(cachedTemp)) {
        lastDHTTime = now;
        float t = dht.readTemperature();
        float h = dht.readHumidity();
        // Only update cache if reading is valid
        if (!isnan(t)) cachedTemp = t;
        if (!isnan(h)) cachedHumid = h;
    }

    // Photoresistors (0-1023 raw ADC)
    int lightL = analogRead(LIGHT_L_PIN);
    int lightR = analogRead(LIGHT_R_PIN);

    // Tilt switch (LOW = tilted because INPUT_PULLUP)
    int tilt = digitalRead(TILT_PIN) == LOW ? 1 : 0;

    // Build JSON output using ArduinoJson v7
    JsonDocument doc;
    doc["us_cm"]   = roundTo1(usCm);
    if (!isnan(cachedTemp))  doc["temp"]  = roundTo1(cachedTemp);
    else                     doc["temp"]  = nullptr;
    if (!isnan(cachedHumid)) doc["humid"] = (int)cachedHumid;
    else                     doc["humid"] = nullptr;
    doc["light_l"] = lightL;
    doc["light_r"] = lightR;
    doc["tilt"]    = tilt;

    // Serialize and send
    serializeJson(doc, Serial);
    Serial.println();  // Newline delimiter for line-based reading
}

// ---------------------------------------------------------------
// Serial command parsing
// ---------------------------------------------------------------

void readSerialCommands() {
    while (Serial.available() > 0) {
        char c = Serial.read();

        if (c == '\n' || c == '\r') {
            if (serialBufPos > 0) {
                serialBuf[serialBufPos] = '\0';
                processCommand(serialBuf);
                serialBufPos = 0;
            }
        } else {
            if (serialBufPos < SERIAL_BUF_SIZE - 1) {
                serialBuf[serialBufPos++] = c;
            } else {
                // Buffer overflow — discard and reset
                serialBufPos = 0;
            }
        }
    }
}

void processCommand(const char* json) {
    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, json);

    if (err) {
        Serial.print("{\"type\":\"error\",\"msg\":\"json_parse: ");
        Serial.print(err.c_str());
        Serial.println("\"}");
        return;
    }

    const char* type = doc["type"];
    if (!type) {
        Serial.println("{\"type\":\"error\",\"msg\":\"missing type field\"}");
        return;
    }

    // Dispatch by command type
    if (strcmp(type, "servo") == 0) {
        cmdServo(doc);
    } else if (strcmp(type, "led") == 0) {
        cmdLED(doc);
    } else if (strcmp(type, "buzz") == 0) {
        cmdBuzz(doc);
    } else if (strcmp(type, "lcd") == 0) {
        cmdLCD(doc);
    } else if (strcmp(type, "ping") == 0) {
        // Heartbeat/keepalive
        Serial.println("{\"type\":\"pong\"}");
    } else {
        Serial.print("{\"type\":\"error\",\"msg\":\"unknown command: ");
        Serial.print(type);
        Serial.println("\"}");
    }
}

// ---------------------------------------------------------------
// Command handlers
// ---------------------------------------------------------------

void cmdServo(JsonDocument& doc) {
    int angle = doc["angle"] | 90;
    angle = constrain(angle, 0, 180);
    headServo.write(angle);

    // Acknowledge
    Serial.print("{\"type\":\"ack\",\"cmd\":\"servo\",\"angle\":");
    Serial.print(angle);
    Serial.println("}");
}

void cmdLED(JsonDocument& doc) {
    uint8_t r = doc["r"] | 0;
    uint8_t g = doc["g"] | 0;
    uint8_t b = doc["b"] | 0;
    setLED(r, g, b);

    Serial.print("{\"type\":\"ack\",\"cmd\":\"led\",\"r\":");
    Serial.print(r);
    Serial.print(",\"g\":");
    Serial.print(g);
    Serial.print(",\"b\":");
    Serial.print(b);
    Serial.println("}");
}

void cmdBuzz(JsonDocument& doc) {
    int freq = doc["freq"] | 440;
    int dur = doc["dur"] | 200;
    freq = constrain(freq, 31, 10000);  // Audible range for passive buzzer
    dur = constrain(dur, 10, 5000);     // 10ms to 5s

    tone(BUZZER_PIN, freq, dur);

    Serial.print("{\"type\":\"ack\",\"cmd\":\"buzz\",\"freq\":");
    Serial.print(freq);
    Serial.print(",\"dur\":");
    Serial.print(dur);
    Serial.println("}");
}

void cmdLCD(JsonDocument& doc) {
    const char* line1 = doc["line1"] | "";
    const char* line2 = doc["line2"] | "";

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print(line1);
    lcd.setCursor(0, 1);
    lcd.print(line2);

    Serial.println("{\"type\":\"ack\",\"cmd\":\"lcd\"}");
}

// ---------------------------------------------------------------
// LED control
// ---------------------------------------------------------------

void setLED(uint8_t r, uint8_t g, uint8_t b) {
    ledR = r; ledG = g; ledB = b;

    // Pin 11 supports PWM — use analogWrite for variable brightness
    // Pins 12, 13 are digital only — use HIGH/LOW
    // For LED values: 0=off, 1=on (digital), or 0-255 (PWM on pin 11)
    analogWrite(LED_R_PIN, r ? 255 : 0);   // Pin 11 = PWM capable
    digitalWrite(LED_G_PIN, g ? HIGH : LOW);
    digitalWrite(LED_B_PIN, b ? HIGH : LOW);
}

// ---------------------------------------------------------------
// Startup ceremony functions
// ---------------------------------------------------------------

void breatheLED() {
    // Breathe blue LED: sine-like fade in/out using PWM on pin 11
    // Since blue is on pin 13 (digital only), we use pin 11 (red) for
    // the breathe effect and set blue on simultaneously.
    // Visual result: purple breathe that fades to blue.
    digitalWrite(LED_B_PIN, HIGH);
    for (int cycle = 0; cycle < 3; cycle++) {
        // Fade in
        for (int i = 0; i <= 255; i += 5) {
            analogWrite(LED_R_PIN, i / 4);  // Dim purple undertone
            delay(8);
        }
        // Fade out
        for (int i = 255; i >= 0; i -= 5) {
            analogWrite(LED_R_PIN, i / 4);
            delay(8);
        }
    }
    analogWrite(LED_R_PIN, 0);
    digitalWrite(LED_B_PIN, LOW);
}

void playConsonanceChord() {
    // Consonance chord: A4=440Hz (1:1), E5=660Hz (3:2), A5=880Hz (2:1)
    // Sequential because Arduino has one tone channel.
    // Duration follows consonance: root longest, fifth shorter, octave shortest.
    tone(BUZZER_PIN, 440, 300);   // A4 — root
    delay(350);
    tone(BUZZER_PIN, 660, 200);   // E5 — perfect fifth (3:2)
    delay(250);
    tone(BUZZER_PIN, 880, 150);   // A5 — octave (2:1)
    delay(200);
    noTone(BUZZER_PIN);
}

void servoSweep() {
    // Slow sweep: center → left → right → center
    // Using consonance positions: 60deg (2/3 of 90), 90deg, 120deg (4/3 of 90)
    headServo.write(90);
    delay(300);

    // Sweep to 60deg (left — 2:3 ratio)
    for (int a = 90; a >= 60; a -= 2) {
        headServo.write(a);
        delay(20);
    }
    delay(200);

    // Sweep to 120deg (right — 4:3 ratio)
    for (int a = 60; a <= 120; a += 2) {
        headServo.write(a);
        delay(20);
    }
    delay(200);

    // Return to center
    for (int a = 120; a >= 90; a -= 2) {
        headServo.write(a);
        delay(20);
    }
    delay(100);
}

// ---------------------------------------------------------------
// Utility
// ---------------------------------------------------------------

float roundTo1(float val) {
    // Round to 1 decimal place
    return ((int)(val * 10 + 0.5)) / 10.0;
}
