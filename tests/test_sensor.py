#!/usr/bin/env python3
"""
CAPACITIVE SOIL MOISTURE SENSOR V1.2 TEST SCRIPT
Reads data from Arduino Nano via serial connection.
Arduino must be running the soil moisture reading code.
"""

import serial
import time
import sys
import glob
from datetime import datetime

# ============ CONFIGURATION ============
SERIAL_PORT = '/dev/serial0'  # Default for Pi GPIO serial
# Alternatives if not working:
# '/dev/ttyAMA0' (older Pi models)
# '/dev/ttyUSB0' (if using USB adapter)
BAUD_RATE = 9600
CALIBRATION_SECONDS = 5  # Time for sensor to stabilize


# =======================================

def list_serial_ports():
    """List all available serial ports"""
    print("\nAvailable serial ports:")
    ports = []

    # Linux ports
    for port in glob.glob('/dev/tty[A-Za-z]*'):
        ports.append(port)

    if ports:
        for port in sorted(ports):
            print(f"  {port}")
    else:
        print("  No serial ports found!")

    return ports


def connect_serial():
    """Establish serial connection to Arduino"""
    print(f"\nConnecting to {SERIAL_PORT} at {BAUD_RATE} baud...")

    try:
        ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1  # 1 second timeout
        )

        # Wait for connection to establish
        time.sleep(2)
        print("✓ Serial connection established!")
        return ser

    except serial.SerialException as e:
        print(f"✗ Serial connection failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Ensure Arduino is connected to Pi GPIO:")
        print("   Arduino TX → Pi GPIO 15 (RX)")
        print("   Arduino RX → Pi GPIO 14 (TX)")
        print("   GND → GND")
        print("2. Check if serial is enabled:")
        print("   Run: sudo raspi-config")
        print("   Interface Options → Serial Port")
        print("   Disable login shell, enable serial hardware")
        print("3. Try alternative port from list above")
        return None
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return None


def read_sensor_values(ser, duration_seconds=30):
    """
    Read and display sensor values
    duration_seconds: How long to run the test
    """
    if not ser:
        print("No serial connection!")
        return

    print("\n" + "=" * 60)
    print("SOIL MOISTURE SENSOR LIVE READINGS")
    print("=" * 60)
    print("Format: Raw ADC | Moisture % | Status")
    print("-" * 60)

    # Calibration period
    print(f"\nCalibrating for {CALIBRATION_SECONDS} seconds...")
    calibration_data = []
    start_time = time.time()

    while time.time() - start_time < CALIBRATION_SECONDS:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                calibration_data.append(line)
        time.sleep(0.1)

    print("Calibration complete! Starting readings...\n")

    # Main reading loop
    start_time = time.time()
    readings = []

    try:
        while time.time() - start_time < duration_seconds:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()

                if line:
                    # Parse the moisture data
                    if line.startswith("MOISTURE:"):
                        try:
                            moisture_percent = int(line.split(":")[1])

                            # Simulate raw ADC value (since Arduino sends %)
                            # In actual Arduino code, you might want to send raw too
                            raw_adc = 1023 - (moisture_percent * 6.23)  # Approximation

                            # Determine status
                            if moisture_percent < 30:
                                status = "TOO DRY"
                            elif moisture_percent < 60:
                                status = "OPTIMAL"
                            else:
                                status = "TOO WET"

                            # Get timestamp
                            timestamp = datetime.now().strftime("%H:%M:%S")

                            # Display reading
                            print(f"[{timestamp}] RAW: {int(raw_adc):4d} | "
                                  f"MOISTURE: {moisture_percent:3d}% | {status}")

                            readings.append(moisture_percent)

                        except (ValueError, IndexError):
                            print(f"Malformed data: {line}")
                    else:
                        # Display any other serial data
                        print(f"Serial data: {line}")

            time.sleep(0.5)  # Small delay to avoid CPU overload

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user!")

    finally:
        # Statistics
        if readings:
            print("\n" + "-" * 60)
            print("READING STATISTICS:")
            print(f"  Total readings: {len(readings)}")
            print(f"  Average moisture: {sum(readings) / len(readings):.1f}%")
            print(f"  Minimum moisture: {min(readings)}%")
            print(f"  Maximum moisture: {max(readings)}%")

        print("\nTest complete!")
        print("=" * 60)


def calibration_mode(ser):
    """Guide user through sensor calibration"""
    print("\n" + "=" * 60)
    print("SENSOR CALIBRATION MODE")
    print("=" * 60)
    print("This will help you find your sensor's range.")
    print("\nSteps:")
    print("1. Keep sensor in DRY air (not soil)")
    print("2. Then place sensor in WATER")
    print("3. Record the values for Arduino calibration")
    print("-" * 60)

    input("\nPress Enter when ready for DRY air reading...")

    print("\nTaking DRY air readings for 5 seconds...")
    dry_readings = []
    start_time = time.time()

    while time.time() - start_time < 5:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line.startswith("MOISTURE:"):
                moisture = int(line.split(":")[1])
                dry_readings.append(moisture)
                print(f"  Dry reading: {moisture}%")
        time.sleep(0.5)

    if dry_readings:
        dry_avg = sum(dry_readings) / len(dry_readings)
        print(f"\n✓ DRY average: {dry_avg:.1f}%")

    input("\nNow place sensor in WATER (not conductive mineral water!). Press Enter...")

    print("\nTaking WATER readings for 5 seconds...")
    wet_readings = []
    start_time = time.time()

    while time.time() - start_time < 5:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line.startswith("MOISTURE:"):
                moisture = int(line.split(":")[1])
                wet_readings.append(moisture)
                print(f"  Wet reading: {moisture}%")
        time.sleep(0.5)

    if wet_readings:
        wet_avg = sum(wet_readings) / len(wet_readings)
        print(f"\n✓ WET average: {wet_avg:.1f}%")

    if dry_readings and wet_readings:
        print("\n" + "=" * 60)
        print("CALIBRATION RESULTS:")
        print(f"  Dry air (max): ~{max(dry_readings)}%")
        print(f"  In water (min): ~{min(wet_readings)}%")
        print("\nUpdate Arduino code with these values:")
        print(f"  map(sensorValue, {max(dry_readings) * 10}, {min(wet_readings) * 10}, 0, 100)")
        print("  (Multiply by 10 to convert % to raw ADC approximation)")

    print("\nCalibration complete!")
    print("=" * 60)


def continuous_monitor(ser):
    """Continuous monitoring mode"""
    print("\n" + "=" * 60)
    print("CONTINUOUS MONITORING MODE")
    print("=" * 60)
    print("Press Ctrl+C to stop")
    print("-" * 60)

    try:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith("MOISTURE:"):
                    moisture = int(line.split(":")[1])
                    timestamp = datetime.now().strftime("%H:%M:%S")

                    # Create simple visual indicator
                    bars = int(moisture / 5)  # 20 bars max
                    visual = "[" + "█" * bars + " " * (20 - bars) + "]"

                    print(f"[{timestamp}] {visual} {moisture:3d}%")

            time.sleep(2)  # Update every 2 seconds

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")


def main():
    """Main menu for sensor testing"""
    print("=" * 60)
    print("CAPACITIVE SOIL MOISTURE SENSOR V1.2 TEST")
    print("=" * 60)

    # Check Arduino is connected
    print("\nPrerequisites:")
    print("1. Arduino must be running the soil moisture code")
    print("2. Connected to Pi via GPIO serial")
    print("3. Sensor connected to Arduino A0")
    print("-" * 60)

    # List available ports
    list_serial_ports()

    # Connect to Arduino
    ser = connect_serial()
    if not ser:
        print("\nFailed to connect. Exiting.")
        sys.exit(1)

    # Main menu
    while True:
        print("\n" + "=" * 60)
        print("TEST MENU:")
        print("1. Live readings (30 seconds)")
        print("2. Calibration mode")
        print("3. Continuous monitoring")
        print("4. Test different durations")
        print("5. Exit")
        print("-" * 60)

        try:
            choice = input("\nSelect option (1-5): ").strip()

            if choice == '1':
                read_sensor_values(ser, 30)
            elif choice == '2':
                calibration_mode(ser)
            elif choice == '3':
                continuous_monitor(ser)
            elif choice == '4':
                try:
                    secs = int(input("Enter duration in seconds: "))
                    read_sensor_values(ser, secs)
                except ValueError:
                    print("Invalid duration!")
            elif choice == '5':
                print("Exiting...")
                break
            else:
                print("Invalid choice!")

        except KeyboardInterrupt:
            print("\n\nReturning to menu...")

    # Cleanup
    if ser and ser.is_open:
        ser.close()
        print("Serial port closed.")

    print("\nTest complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram terminated by user.")
        sys.exit(0)