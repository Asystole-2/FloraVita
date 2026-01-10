import os
import serial
import serial.tools.list_ports
import time
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# CONFIGURATION: Unique ID for this hardware setup
HARDWARE_ID = os.getenv('HARDWARE_ID', 'DEFAULT_NODE')

# PubNub Setup
pn_config = PNConfiguration()
pn_config.subscribe_key = os.getenv('PUBNUB_SUBSCRIBE_KEY')
pn_config.publish_key = os.getenv('PUBNUB_PUBLISH_KEY')
pn_config.user_id = f"bridge_{HARDWARE_ID}"
pubnub = PubNub(pn_config)


def find_arduino_port():
    """Try to automatically find the Arduino port"""
    ports = list(serial.tools.list_ports.comports())

    # Common Arduino descriptions to look for
    arduino_keywords = ['arduino', 'ch340', 'usb serial', 'usb uart']

    for port in ports:
        port_desc = port.description.lower()
        for keyword in arduino_keywords:
            if keyword in port_desc:
                print(f"Found Arduino on {port.device}: {port.description}")
                return port.device

    # If no Arduino found, list available ports
    print("No Arduino found. Available ports:")
    for port in ports:
        print(f"  - {port.device}: {port.description}")

    return None


# Try to find Arduino port
arduino_port = find_arduino_port()

if not arduino_port:
    print("Could not auto-detect Arduino. Please enter COM port manually:")
    arduino_port = input("Enter COM port (e.g., COM3, COM4): ").strip()

try:
    # Try to connect to Arduino
    print(f"Connecting to {arduino_port} at 9600 baud...")
    ser = serial.Serial(arduino_port, 9600, timeout=1)
    time.sleep(2)  # Wait for Arduino to reset
    print(f"Connected to {arduino_port}")

except Exception as e:
    print(f"Failed to connect to {arduino_port}: {e}")
    print("Please check:")
    print("1. Arduino is connected via USB")
    print("2. Correct COM port is selected")
    print("3. No other program is using the port (close Arduino IDE)")
    exit(1)

print(f"--- Moisture Bridge Active: {HARDWARE_ID} ---")
print("Listening for moisture data...")

while True:
    if ser.in_waiting > 0:
        try:
            line = ser.readline().decode('utf-8').strip()
            print(f"Raw data: {line}")  # Debug

            if line.startswith("MOISTURE:"):
                parts = line.split(":")

                if len(parts) >= 4:
                    data = {
                        "hardware_id": HARDWARE_ID,
                        "moisture": float(parts[1]),
                        "status": parts[3],
                        "timestamp": time.time()
                    }

                    try:
                        pubnub.publish().channel("moisture-data").message(data).sync()
                        print(f"Published telemetry for {HARDWARE_ID}: {parts[1]}% ({parts[3]})")
                    except Exception as pubnub_error:
                        print(f"PubNub error: {pubnub_error}")
                else:
                    print(f"Malformed data: {line}")

        except UnicodeDecodeError:
            print("Could not decode serial data (check baud rate)")
        except Exception as e:
            print(f"Error: {e}")

    time.sleep(0.1)