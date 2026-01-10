// Soil Moisture Sensor Code for Arduino Nano - RUN ON ARDUINO IDE
// Save as: soil_moisture_to_pi.ino

const int SENSOR_PIN = A0;  // Soil moisture sensor pin

// Calibration values - ADJUST THESE AFTER TESTING!
const int DRY_VALUE = 1023;   // Sensor in dry air
const int WET_VALUE = 300;    // Sensor in water
const int UPDATE_INTERVAL = 2000;  // Send data every 2 seconds

void setup() {
  // Initialize serial communication at 9600 baud
  Serial.begin(9600);
  
  // Set sensor pin as input
  pinMode(SENSOR_PIN, INPUT);
  
  // Wait for serial to initialize and sensor to stabilize
  delay(3000);
  
  // Send startup message
  Serial.println("=================================");
  Serial.println("Soil Moisture Sensor V1.2");
  Serial.println("Connected to Arduino Nano");
  Serial.println("=================================");
  Serial.print("Dry Value: "); Serial.println(DRY_VALUE);
  Serial.print("Wet Value: "); Serial.println(WET_VALUE);
  Serial.println("Starting readings...");
  Serial.println("=================================");
}

void loop() {
  // Read the sensor value (0-1023)
  int sensorValue = analogRead(SENSOR_PIN);
  
  // Convert to percentage (inverted: higher value = drier)
  // Map from dry->wet to 0-100%
  int moisturePercent = map(sensorValue, DRY_VALUE, WET_VALUE, 0, 100);
  
  // Constrain to 0-100% range
  moisturePercent = constrain(moisturePercent, 0, 100);
  
  // Send formatted data to Raspberry Pi
  Serial.print("MOISTURE:");   // Label for Pi to parse
  Serial.println(moisturePercent);  // The actual value
  
  // Optional: Also send raw value for debugging
  static unsigned int counter = 0;
  if (counter++ % 5 == 0) {  // Send raw value every 5 readings
    Serial.print("RAW:");
    Serial.println(sensorValue);
  }
  
  // Wait before next reading
  delay(UPDATE_INTERVAL);
}