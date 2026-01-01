import os
import RPi.GPIO as GPIO
from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.callbacks import SubscribeCallback
from dotenv import load_dotenv

load_dotenv()

MY_HARDWARE_ID = os.getenv('HARDWARE_ID', 'DEFAULT_NODE')
RELAY_PIN = 27

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.HIGH) # Start OFF

class PumpSubscriber(SubscribeCallback):
    def message(self, pubnub, message):
        msg = message.message
        target_id = msg.get("hardware_id")
        cmd = msg.get("command")

        # FILTER: Only react if the command is meant for THIS hardware
        if target_id == MY_HARDWARE_ID:
            if cmd == "PUMP_ON":
                GPIO.output(RELAY_PIN, GPIO.LOW) # Engage Relay
                print(f"[{MY_HARDWARE_ID}] Pump Engaged")
            elif cmd == "PUMP_OFF":
                GPIO.output(RELAY_PIN, GPIO.HIGH) # Stop Relay
                print(f"[{MY_HARDWARE_ID}] Pump Stopped")
        else:
            # Ignore messages meant for other devices
            print(f"Ignored command for {target_id} (I am {MY_HARDWARE_ID})")

# Setup PubNub
pn_config = PNConfiguration()
pn_config.subscribe_key = os.getenv('PUBNUB_SUBSCRIBE_KEY')
pn_config.publish_key = os.getenv('PUBNUB_PUBLISH_KEY')
pn_config.user_id = f"pi_{MY_HARDWARE_ID}"

pubnub = PubNub(pn_config)
pubnub.add_listener(PumpSubscriber())

print(f"--- Pump Controller Active: {MY_HARDWARE_ID} ---")
pubnub.subscribe().channels("pump-commands").execute()