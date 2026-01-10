import RPi.GPIO as GPIO
import time
import sys

# ============ CONFIGURATION ============
RELAY_PIN = 27  # GPIO pin connected to relay IN1
TEST_CYCLES = 3  # Number of on/off cycles
ON_DURATION = 2  # Seconds pump runs each cycle
OFF_DURATION = 3  # Seconds between cycles


# =======================================

def setup():
    """Initialize GPIO and relay"""
    print("=" * 50)
    print("PUMP AND RELAY TEST SCRIPT")
    print("=" * 50)
    print(f"Relay GPIO Pin: {RELAY_PIN}")
    print(f"Test Cycles: {TEST_CYCLES}")
    print(f"Pump ON Duration: {ON_DURATION}s")
    print(f"Pump OFF Duration: {OFF_DURATION}s")
    print("-" * 50)

    # Set GPIO mode
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RELAY_PIN, GPIO.OUT)

    # Ensure relay starts in OFF state

    GPIO.output(RELAY_PIN, GPIO.HIGH)
    time.sleep(1)

    print("GPIO initialized. Relay should be OFF.")
    print("Make sure battery holder switch is ON!")
    print("-" * 50)


def test_relay():
    """Cycle relay on/off to test pump"""
    print("Starting relay test...")
    print("Press Ctrl+C to stop early")
    print()

    try:
        for cycle in range(1, TEST_CYCLES + 1):
            print(f"\nCYCLE {cycle}/{TEST_CYCLES}")

            # Turn RELAY ON (pump should start)
            print(f"  Turning relay ON for {ON_DURATION}s...", end="", flush=True)
            GPIO.output(RELAY_PIN, GPIO.LOW)

            # Visual countdown
            for sec in range(ON_DURATION, 0, -1):
                print(f" {sec}", end="", flush=True)
                time.sleep(1)
            print(" ✓")

            # Turn RELAY OFF
            print(f"  Turning relay OFF for {OFF_DURATION}s...", end="", flush=True)
            GPIO.output(RELAY_PIN, GPIO.HIGH)

            # Visual countdown
            for sec in range(OFF_DURATION, 0, -1):
                print(f" {sec}", end="", flush=True)
                time.sleep(1)
            print(" ✓")

        print("\n" + "=" * 50)
        print("TEST COMPLETE!")

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user!")

    finally:
        cleanup()


def manual_control():
    """Manual control mode - user controls pump with keyboard"""
    print("\n" + "=" * 50)
    print("MANUAL CONTROL MODE")
    print("=" * 50)
    print("Commands:")
    print("  'o' or 'on'  : Turn pump ON")
    print("  'f' or 'off' : Turn pump OFF")
    print("  'q' or 'quit': Exit program")
    print("-" * 50)

    try:
        while True:
            cmd = input("\nEnter command: ").strip().lower()

            if cmd in ['o', 'on']:
                GPIO.output(RELAY_PIN, GPIO.LOW)
                print("  → Pump ON")

            elif cmd in ['f', 'off']:
                GPIO.output(RELAY_PIN, GPIO.HIGH)
                print("  → Pump OFF")

            elif cmd in ['q', 'quit', 'exit']:
                print("  → Exiting...")
                break

            else:
                print("  → Unknown command. Use: on/off/quit")

    except KeyboardInterrupt:
        print("\nExiting...")

    finally:
        cleanup()


def cleanup():
    """Clean up GPIO and ensure pump is off"""
    print("\nCleaning up...")
    GPIO.output(RELAY_PIN, GPIO.HIGH)  # Ensure relay OFF
    time.sleep(0.5)
    GPIO.cleanup()
    print("GPIO cleaned up. Pump should be OFF.")
    print("=" * 50)


def main():
    """Main menu"""
    print("\nSelect test mode:")
    print("1. Automatic cycling test")
    print("2. Manual control mode")
    print("3. Quick 1-second test")
    print("4. Exit")

    try:
        choice = input("\nEnter choice (1-4): ").strip()

        if choice == '1':
            setup()
            test_relay()
        elif choice == '2':
            setup()
            manual_control()
        elif choice == '3':
            setup()
            print("\nQuick test - turning pump ON for 1 second...")
            GPIO.output(RELAY_PIN, GPIO.LOW)
            time.sleep(1)
            GPIO.output(RELAY_PIN, GPIO.HIGH)
            print("Quick test complete!")
            cleanup()
        elif choice == '4':
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice. Please run again.")

    except Exception as e:
        print(f"\nError: {e}")
        cleanup()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram terminated by user.")
        sys.exit(0)