import os
import RPi.GPIO as GPIO
from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.callbacks import SubscribeCallback
from dotenv import load_dotenv
import time
import sys
import json
import threading

load_dotenv()

RELAY_PIN = 27

gpio_lock = threading.Lock()


def setup_gpio():
    print(f" Setting up GPIO {RELAY_PIN} for LOW-LEVEL TRIGGER...")

    GPIO.setwarnings(False)
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(RELAY_PIN, GPIO.OUT, initial=GPIO.HIGH)

    print(f"🔌 GPIO {RELAY_PIN} initialized = HIGH (Relay OFF, Pump OFF)")
    print(f"   📍 Physical Pin: 33 on Raspberry Pi")
    print(f"   ⚡ Relay Type: ACTIVE-LOW (LOW=ON, HIGH=OFF)")
    print(f"   🔌 Transistor: Amplifying GPIO signal for relay")

    time.sleep(0.5)
    initial_state = GPIO.input(RELAY_PIN)
    print(f"   ✅ Verified: GPIO {RELAY_PIN} = {'HIGH' if initial_state else 'LOW'}")
    return True


def set_pump_state(on):
    """Thread-safe function to control pump """
    with gpio_lock:
        try:
            if on:
                # LOW activates relay for low-level trigger
                GPIO.output(RELAY_PIN, GPIO.LOW)  # LOW = ON
                print(f"   ⚡ GPIO {RELAY_PIN} set to LOW (Transistor ON → Relay ON → Pump ON)")
            else:
                # HIGH deactivates relay
                GPIO.output(RELAY_PIN, GPIO.HIGH)  # HIGH = OFF
                print(f"   ⚡ GPIO {RELAY_PIN} set to HIGH (Transistor OFF → Relay OFF → Pump OFF)")
            return True
        except Exception as e:
            print(f"   ❌ GPIO Error: {e}")
            return False


# Initialize GPIO in main thread
if not setup_gpio():
    print("❌ Failed to initialize GPIO")
    sys.exit(1)


class PumpSubscriber(SubscribeCallback):
    def message(self, pubnub, message):
        """Called when a message is received in background thread"""
        print(f"\n" + "=" * 50)
        print(f"📥 MESSAGE RECEIVED FROM PUBLISHER!")
        print(f"   Channel: {message.channel}")
        print(f"   Message: {json.dumps(message.message, indent=2)}")
        print(f"=" * 50)

        msg = message.message
        cmd = msg.get("command")
        plant_name = msg.get('plant_name', 'Unknown')
        plant_id = msg.get('plant_id', 'Unknown')
        reason = msg.get('reason', 'manual')
        current_moisture = msg.get('current_moisture')
        threshold = msg.get('threshold')

        if cmd == "PUMP_ON":
            if reason == "automatic":
                # Automatic watering based on threshold
                print(f"   🌱 AUTOMATIC WATERING ACTIVATED!")
                print(f"   🌿 Plant: {plant_name} (ID: {plant_id})")
                print(f"   📊 Moisture: {current_moisture}% < Threshold: {threshold}%")
                print(f"   🔄 Reason: Automated threshold-based watering")
            else:
                # Manual watering
                print(f"   👆 MANUAL WATERING ACTIVATED!")
                print(f"   🌿 Plant: {plant_name} (ID: {plant_id})")
                print(f"   🔄 Reason: {reason}")

            if set_pump_state(True):
                if reason == "automatic":
                    print(f"   ✅ AUTOMATIC PUMP ACTIVE - {plant_name}")
                else:
                    print(f"   ✅ MANUAL PUMP ACTIVE - {plant_name}")
                print(f"   🔌 Signal: GPIO LOW → Transistor ON → Relay ON")

                # Log the pump activation
                self.log_pump_activity(plant_id, plant_name, "ON", reason, current_moisture, threshold)
            else:
                print(f"   ❌ Failed to turn pump ON")

        elif cmd == "PUMP_OFF":
            print(f"   ⏹️ Turning pump OFF")
            print(f"   🌿 Plant: {plant_name} (ID: {plant_id})")
            print(f"   🔄 Reason: {reason}")

            if set_pump_state(False):
                print(f"   ✅ PUMP INACTIVE - {plant_name}")
                print(f"   🔌 Signal: GPIO HIGH → Transistor OFF → Relay OFF")

                # Log the pump deactivation
                self.log_pump_activity(plant_id, plant_name, "OFF", reason)
            else:
                print(f"   ❌ Failed to turn pump OFF")

        else:
            print(f"   ⚠️ Unknown command: {cmd}")

    def log_pump_activity(self, plant_id, plant_name, state, reason, moisture=None, threshold=None):
        """Log pump activity for monitoring"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

        if state == "ON":
            if reason == "automatic":
                log_msg = f"[{timestamp}] AUTO: Pump ON for {plant_name} (Moisture: {moisture}% < {threshold}%)"
            else:
                log_msg = f"[{timestamp}]  MANUAL: Pump ON for {plant_name}"
        else:
            if reason == "automatic_complete":
                log_msg = f"[{timestamp}] AUTO: Pump OFF for {plant_name} (Watering complete)"
            elif reason == "manual_complete":
                log_msg = f"[{timestamp}] MANUAL: Pump OFF for {plant_name} (Watering complete)"
            else:
                log_msg = f"[{timestamp}] Pump OFF for {plant_name}"

        try:
            with open("pump_activity.log", "a") as log_file:
                log_file.write(log_msg + "\n")
            print(f"   📝 Activity logged: {log_msg}")
        except Exception as e:
            print(f"   ⚠️ Could not write to log file: {e}")

    def status(self, pubnub, status):
        """Called on connection status changes"""
        print(f"\n📡 PUBLISH/SUBSCRIBE STATUS: {status.category}")

        if status.category == "PNConnectedCategory":
            print(f"   SUCCESS: Connected to PubNub Cloud!")
            print(f"   📡 Ready to receive commands on 'pump-commands' channel")
            print(f"   💧 Listening for automatic/manual watering commands")
        elif status.category == "PNNetworkUpCategory":
            print(f"   🌐 Network connection established")


# Setup PubNub
print("\n" + "=" * 60)
print("🌱 FLORAVITA PUMP CONTROLLER - WITH TRANSISTOR DRIVER")
print("=" * 60)

pn_config = PNConfiguration()
pn_config.subscribe_key = os.getenv('PUBNUB_SUBSCRIBE_KEY')
pn_config.publish_key = os.getenv('PUBNUB_PUBLISH_KEY')
pn_config.user_id = "raspberry_pi_pump_controller"

# Connection settings
pn_config.subscribe_request_timeout = 10
pn_config.connect_timeout = 10

# Debug: Show keys (masked for security)
if pn_config.subscribe_key:
    print(f"📡 PubNub Subscribe Key: {pn_config.subscribe_key[:15]}...")
else:
    print("❌ ERROR: PubNub subscribe key not found in .env file!")
    sys.exit(1)

pubnub = PubNub(pn_config)
pubnub.add_listener(PumpSubscriber())

# Get initial state
initial_gpio_state = GPIO.input(RELAY_PIN)
pump_state = "OFF" if initial_gpio_state == GPIO.HIGH else "ON"  # Inverted for low-trigger

print(f"🔌 GPIO Pin: {RELAY_PIN} (Pin 33 on Pi)")
print(f"🔋 Relay Logic: LOW = ON, HIGH = OFF (ACTIVE-LOW with transistor)")
print(f"🔋 Current GPIO State: {'HIGH' if initial_gpio_state else 'LOW'}")
print(f"💧 Pump State: {pump_state}")
print(f"📝 Logging pump activity to: pump_activity.log")
print("=" * 60)

# Subscribe to channel
try:
    print(f"\n[{time.strftime('%H:%M:%S')}] 📡 Subscribing to PubNub channel 'pump-commands'...")
    pubnub.subscribe().channels("pump-commands").execute()
    print(f"[{time.strftime('%H:%M:%S')}] ✅ Subscription request sent to PubNub")
    print(f"[{time.strftime('%H:%M:%S')}] 💧 Ready for automatic/manual watering commands")

    # Wait a moment for connection
    time.sleep(2)

except Exception as e:
    print(f"❌ Error subscribing to PubNub: {e}")
    print(f"   Error type: {type(e).__name__}")

# Main loop
print(f"\n[{time.strftime('%H:%M:%S')}] ✅ Pump Controller is running!")
print(f"   Initial pump state: {pump_state}")
print(f"   Listening for automatic watering (based on plant thresholds)")
print(f"   Listening for manual watering commands")
print("   Press Ctrl+C to exit\n")

try:
    last_gpio_state = initial_gpio_state
    while True:
        time.sleep(1)

        # Check for state changes
        with gpio_lock:
            current_gpio_state = GPIO.input(RELAY_PIN)

        if current_gpio_state != last_gpio_state:
            old_pump_state = "OFF" if last_gpio_state == GPIO.HIGH else "ON"
            new_pump_state = "OFF" if current_gpio_state == GPIO.HIGH else "ON"
            print(f"[{time.strftime('%H:%M:%S')}] 🔄 Pump state changed: {old_pump_state} → {new_pump_state}")
            print(f"   GPIO: {'HIGH' if last_gpio_state else 'LOW'} → {'HIGH' if current_gpio_state else 'LOW'}")
            last_gpio_state = current_gpio_state

except KeyboardInterrupt:
    print(f"\n[{time.strftime('%H:%M:%S')}]  Shutting down pump controller...")

except Exception as e:
    print(f"\n❌ Unexpected error: {e}")

finally:
    # Always ensure pump is OFF and cleanup
    print(f"   🔌 Setting GPIO {RELAY_PIN} to HIGH (Transistor OFF → Relay OFF → Pump OFF)")
    set_pump_state(False)  # This sets GPIO HIGH
    time.sleep(0.5)  # Wait for relay to deactivate
    GPIO.cleanup()
    print(f"[{time.strftime('%H:%M:%S')}] ✅ GPIO cleanup complete")
    sys.exit(0)