import os
import RPi.GPIO as GPIO
from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.callbacks import SubscribeCallback
from dotenv import load_dotenv
import time

load_dotenv()

RELAY_PIN = 27

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.HIGH)  # Start OFF (HIGH = OFF for active-low relay)


class PumpSubscriber(SubscribeCallback):
    def message(self, pubnub, message):
        msg = message.message
        cmd = msg.get("command")

        # Listen to ALL pump commands
        if cmd == "PUMP_ON":
            GPIO.output(RELAY_PIN, GPIO.LOW)  # Engage Relay (LOW = ON)
            print(f"[{time.strftime('%H:%M:%S')}] 💧 Pump ON - Plant: {msg.get('plant_name', 'Unknown')}")
        elif cmd == "PUMP_OFF":
            GPIO.output(RELAY_PIN, GPIO.HIGH)  # Stop Relay (HIGH = OFF)
            print(f"[{time.strftime('%H:%M:%S')}] ⏹️ Pump OFF - Plant: {msg.get('plant_name', 'Unknown')}")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] Unknown command: {cmd}")

    def status(self, pubnub, status):
        if status.category == "PNConnectedCategory":
            print(f"[{time.strftime('%H:%M:%S')}] Connected to PubNub - Ready for pump commands")

    def presence(self, pubnub, presence):
        pass  # Optional: Handle presence events


# Setup PubNub
pn_config = PNConfiguration()
pn_config.subscribe_key = os.getenv('PUBNUB_SUBSCRIBE_KEY')
pn_config.publish_key = os.getenv('PUBNUB_PUBLISH_KEY')
pn_config.user_id = "raspberry_pi"

pubnub = PubNub(pn_config)
pubnub.add_listener(PumpSubscriber())

print("=" * 50)
print("🌱 FloraVita Pump Controller")
print(f"📡 PubNub Key: {pn_config.subscribe_key[:10]}...")
print(f"🔌 Relay Pin: {RELAY_PIN} (HIGH = OFF, LOW = ON)")
print("=" * 50)
print(f"[{time.strftime('%H:%M:%S')}] ⏳ Waiting for pump commands...")

# Subscribe to pump-commands channel
pubnub.subscribe().channels("pump-commands").execute()

# Keep the program running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print(f"\n[{time.strftime('%H:%M:%S')}] 👋 Shutting down...")
    GPIO.output(RELAY_PIN, GPIO.HIGH)  # Ensure pump is OFF
    GPIO.cleanup()
    print(f"[{time.strftime('%H:%M:%S')}] ✅ Cleanup complete")