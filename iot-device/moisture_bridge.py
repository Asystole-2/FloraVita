import os
import serial
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

# Serial Setup
ser = serial.Serial('COM7', 9600, timeout=1)

print(f"--- Moisture Bridge Active: {HARDWARE_ID} ---")

while True:
    if ser.in_waiting > 0:
        try:
            line = ser.readline().decode('utf-8').strip()
            if line.startswith("MOISTURE:"):
                parts = line.split(":")

                data = {
                    "hardware_id": HARDWARE_ID,
                    "moisture": float(parts[1]),
                    "status": parts[3],
                    "timestamp": time.time()
                }
                pubnub.publish().channel("moisture-data").message(data).sync()
                print(f"Published telemetry for {HARDWARE_ID}: {parts[1]}%")
        except Exception as e:
            print(f"Serial Error: {e}")

    time.sleep(0.1)