#include <Wire.h>
#include <SPI.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME680.h>

// --- Sensor Configuration ---

// BME680 Setup
// Note: Connect BME680 to I2C pins (Mega: SDA=20, SCL=21)
Adafruit_BME680 bme; 

// HC-SR04 Ultrasonic Distance Sensor
const int trigPin = 40;  
const int echoPin = 38;  

// Digital Photoresistor Module 
const int lightDigitalPin = 37; 

// --- Global Variables ---
long duration;      
float distanceCm;   
float seaLevelPressure = 1013.25; // Standard sea level pressure in hPa

void setup() {
  Serial.begin(9600); 
  Serial.println("Mega Sensor Hub (BME680) Initialized."); 

  // Initialize BME680
  if (!bme.begin()) {
    Serial.println("Could not find a valid BME680 sensor, check wiring!");
    while (1); // Halt if sensor not found
  }

  // Set up oversampling and filter for BME680
  bme.setTemperatureOversampling(BME680_OS_8X);
  bme.setHumidityOversampling(BME680_OS_2X);
  bme.setPressureOversampling(BME680_OS_4X);
  bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
  bme.setGasHeater(320, 150); // 320°C for 150 ms

  // Configure other sensor pins
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(lightDigitalPin, INPUT);

  Serial.println("START"); 
}

void loop() {
  // The BME680 takes a moment to perform readings, especially with the gas heater
  if (! bme.performReading()) {
    Serial.println("Failed to perform BME680 reading :(");
    return;
  }

  // 1. Get BME680 Data
  float temp = bme.temperature;
  float hum = bme.humidity;
  float pres = bme.pressure / 100.0; // Convert Pa to hPa
  float gas = bme.gas_resistance / 1000.0; // Convert Ohms to K-Ohms

  // 2. HC-SR04 Logic
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  duration = pulseIn(echoPin, HIGH);
  distanceCm = duration * 0.0343 / 2.0; 

  // 3. Digital Photoresistor State
  int lightState = digitalRead(lightDigitalPin); 
  
  // --- Output Data in CSV Format ---
  // Format: Hum, Temp, Pres, Gas, Distance, Light
  Serial.print(hum);
  Serial.print(",");
  Serial.print(temp);
  Serial.print(",");
  Serial.print(pres);
  Serial.print(",");
  Serial.print(gas);
  Serial.print(",");
  Serial.print(distanceCm);
  Serial.print(",");
  Serial.println(lightState); 

  delay(10000); 
}
