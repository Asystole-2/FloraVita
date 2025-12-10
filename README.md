# 🌱 Smart Automated Plant Irrigation System

An IoT-based smart irrigation system that monitors soil moisture and automatically waters plants with manual override capability via web dashboard.

## 📋 Table of Contents
- [Features](#-features)
- [Hardware Setup](#-hardware-setup)
- [PubNub Setup](#-pubnub-setup)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Security](#-security-features)
- [Data Flow](#-data-flow-architecture)


## 🚀 Features

- **Real-time Monitoring**: Continuous soil moisture tracking
- **Automated Watering**: Triggers pump when moisture falls below threshold
- **Manual Control**: Web dashboard with "Water Now" button
- **Historical Data**: Visualize moisture trends over time
- **Security**: PubNub PAM security for command channels

## 🔌 Hardware Setup

### Complete Component List

| Component | Quantity | Purpose | Irish Supplier |
|-----------|----------|---------|----------------|
| Raspberry Pi 4 | 1 | Main controller | Already have |
| Capacitive Soil Moisture Sensor | 1 | Measures soil moisture | [Hobby Components](https://www.hobbycomponents.com/sensors/539-capacitive-soil-moisture-sensor-v20) |
| 5V 1-Channel Relay Module | 1 | Safely controls water pump | [Cool Components](https://coolcomponents.ie/products/1-channel-relay-module) |
| Mini Submersible Pump (3-6V) | 1 | Water delivery | [Amazon UK](https://www.amazon.co.uk/Makerfire-Submersible-Micro-Water-Pump/dp/B01N6RZQOV) |
| 4x AA Battery Holder with Switch | 1 | Isolated pump power | [RadioParts](https://radioparts.ie/product/4-x-aa-battery-holder-with-leads-and-switch/) |
| AA Batteries (Rechargeable) | 4 | Pump power source | Tesco/Dunnes |
| Jumper Wires (M/F, M/M) | 10+ | Connections | [The Pi Hut](https://thepihut.com/products/jumper-wires-pack-of-40) |
| Breadboard | 1 | Prototyping | [Adaptuit](https://adaptuit.ie/product/breadboard-830-point/) |
| Water Container | 1 | Water reservoir | Dealz/Poundland |
| Tubing (3-4mm) | 0.5m | Water delivery | Aquarium/pet store |
| Optional: Project Box | 1 | Enclosure | [RS Components](https://ie.rs-online.com/web/p/junction-boxes/7455289) |

### Wiring Diagram
```
┌─────────────────────────────────────────────────────────────┐
│ RASPBERRY PI 4 │
│ │
│ PIN 1 (3.3V) ──────────────────────┐ │
│ PIN 6 (GND) ──────────────────────┬─────────────────┐ │
│ PIN 11 (GPIO 17) ───────────────────┤ │ │
│ PIN 13 (GPIO 27) ───────────────────┤ │ │
│ PIN 2 (5V) ─────────────────────┤ │ │
│ PIN 14 (GND) ─────────────────────┤ │ │
└──────────────────────────────────────┴─────────────────┴───┘
│ │ │ │ │
│ │ │ │ │
▼ ▼ ▼ ▼ ▼
┌──────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│ SOIL SENSOR │ │ RELAY MODULE │ │ BATTERY PACK │
│ │ │ │ │ │
│ VCC ─────────┘ │ VCC ────────────┘ │ + ────────────────┘
│ GND ────────────┤ GND ───────────────┤ │
│ OUT ────────────┤ IN1 ───────────────┘ │
└─────────────────┤ COM ─────────────────────────────────────┘
│ NO ──────┐ │
└───────────┴──────────────────────────────┘
│
▼
┌──────────────┐
│ WATER PUMP │
│ │
│ + ──────────┘
│ - ──────────────────────────────┐
└──────────────────────────────────┘
```

### Step-by-Step Wiring Instructions

1. **Soil Moisture Sensor:**
   - Red wire (VCC) → Raspberry Pi Pin 1 (3.3V)
   - Black wire (GND) → Raspberry Pi Pin 6 (GND)
   - Yellow wire (OUT) → Raspberry Pi Pin 11 (GPIO 17)

2. **Relay Module:**
   - VCC pin → Raspberry Pi Pin 2 (5V)
   - GND pin → Raspberry Pi Pin 14 (GND)
   - IN1 pin → Raspberry Pi Pin 13 (GPIO 27)

3. **Battery Pack:**
   - Positive (+) wire → Relay COM terminal
   - Negative (-) wire → Pump negative (-) terminal

4. **Water Pump:**
   - Positive (+) wire → Relay NO (Normally Open) terminal
   - Negative (-) wire → Battery pack negative (-) terminal

5. **Add Safety Components (Recommended):**
   - Place a 1A fuse in series with battery positive wire
   - Add a 1N4001 diode across pump terminals (cathode to +, anode to -)

### Important Safety Notes

⚠️ **CRITICAL SAFETY MEASURES:**
1. **Always use relay** - Never connect pump directly to GPIO pins
2. **Isolate power** - Use separate batteries for pump vs Raspberry Pi
3. **Waterproof connections** if used outdoors
4. **Test with water** in sink before connecting to plants
5. **Add fuse** (1A) for pump circuit protection

## 📡 PubNub Setup

### Step 1: Create PubNub Account

1. Go to [PubNub Signup](https://dashboard.pubnub.com/signup)
2. Sign up with email or GitHub
3. Verify your email address

### Step 2: Create New App

1. Login to [PubNub Dashboard](https://dashboard.pubnub.com/)
2. Click "CREATE NEW APP"
3. App Name: `Smart Plant Irrigation`
4. Description: "IoT plant monitoring and control system"
5. Click "CREATE"

### Step 3: Get Your Keys

1. Click on your new app
2. Click "KEYSET" on the left sidebar
3. Note these values:
    Publish Key: pub-c-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    Subscribe Key: sub-c-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    Secret Key: sec-c-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx


### Step 4: Configure Channels

1. In your keyset, ensure these features are enabled:
- ✅ Enable Presence
- ✅ Enable Stream Controller
- ✅ Enable PAM (Access Manager)

2. Create two channels:
- `plant-moisture-data` - For sensor readings (PUBLISH only from device)
- `plant-pump-commands` - For control commands (SUBSCRIBE on device)

### Step 5: Set Up PAM Security

```bash
# Install PubNub CLI (optional but useful)
npm install -g pubnub-cli

# Set up PAM rules (example using curl)
curl -X POST "https://ps.pndsn.com/v2/auth/grant/sub-key/YOUR_SUB_KEY" \
-d "channel=plant-pump-commands" \
-d "auth=irrigation_device" \
-d "read=true" \
-d "write=false" \
-d "ttl=1440"
```
## 🔧 Installation

### 1. Clone Repository
git clone https://github.com/YOUR_USERNAME/smart-plant-irrigation.git
cd smart-plant-irrigation

### 2. Hardware Setup
Follow the wiring diagram above to connect all components.

### 3. Software Setup
```
## Update system
sudo apt update && sudo apt upgrade -y

## Install Python and tools
sudo apt install python3-pip python3-venv git

## Create virtual environment
python3 -m venv venv
source venv/bin/activate

## Install Python packages
pip install pubnub RPi.GPIO python-dotenv

## Install Node.js (for web dashboard)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

## Install Node dependencies
cd web-dashboard
npm install
```
### 4. Configuration
 Copy example config: `cp iot-device/config.example.json iot-device/config.json`

 Edit iot-device/config.json:
```
{
  "pubnub": {
    "publish_key": "pub-c-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "subscribe_key": "sub-c-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "secret_key": "sec-c-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "user_id": "plant_irrigation_system_001"
  },
  "device": {
    "moisture_threshold": 30,
    "pump_duration": 3000,
    "check_interval": 60,
    "sensor_pin": 17,
    "relay_pin": 27
  },
  "channels": {
    "moisture_data": "plant-moisture-data",
    "pump_commands": "plant-pump-commands"
  }
}
```
### Enable GPIO Access
# Add user to GPIO group
sudo usermod -a -G gpio $USER

# Reboot for changes to take effect
sudo reboot

### 🚀 Usage
```
# Running the IoT Device:
cd iot-device
source ../venv/bin/activate
python3 main.py

# Running the Web Dashboard:
cd web-dashboard
npm start
# Access at http://localhost:3000

# Testing Hardware
# Test sensor reading
python3 tests/test_sensor.py

# Test pump activation
python3 tests/test_pump.py --duration 2000

# Test PubNub connection
python3 tests/test_pubnub.py
```

### 📊 Project Structure
```
smart-plant-irrigation/
├── docs/
│   ├── hardware_setup.md
│   └── wiring_diagrams/  #### Fritzing diagrams
├── iot-device/           #### Raspberry Pi code
│   ├── main.py          #### Main control logic
│   ├── sensor.py        #### Soil sensor reading
│   ├── pump.py          #### Pump control logic
│   ├── pubnub_client.py #### PubNub communication
│   └── config.json      #### Configuration (DO NOT COMMIT)
├── tests/               #### Hardware/software tests
├── web-dashboard/       #### React dashboard
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── App.js
│   └── package.json
├── .gitignore
└── README.md
```

### 🔒 Security Features
1. PubNub PAM (Access Manager)
Device-specific auth keys

Channel-level permissions

Time-limited access tokens

Revocable credentials

2. Hardware Security
Separate power supplies

Relay isolation

Fuse protection

Waterproof enclosures

3. Software Security
Environment variables for secrets

Input validation

Command sanitization

Regular security updates



### 📈 Data Flow Architecture
```
┌─────────────────┐    PUBLISH    ┌─────────────────┐    HTTP     ┌─────────────────┐
│   IoT DEVICE    ├──────────────►│    PUBNUB       ├────────────►│  WEB DASHBOARD  │
│  (Raspberry Pi) │   Moisture    │    CLOUD        │   Display   │   (User View)   │
│                 │   Readings    │                 │   Data      │                 │
│  Sensor → GPIO  │               │  Channels:      │             │  Charts & UI    │
│  Pump ← Relay   │               │  - plant-       │             │  Controls       │
└────────┬────────┘               │    moisture-data│             └────────┬────────┘
         │                        │  - plant-       │                      │
         │      SUBSCRIBE         │    pump-commands│              User Action
         └────────────────────────┘                 │            (Click "Water Now")
                    Pump Commands └─────────────────┘                      │
                                                                             ▼
                                                                   ┌─────────────────┐
                                                                   │    PUBNUB       │
                                                                   │    CLOUD        │
                                                                   │                 │
                                                                   │  Command:       │
                                                                   │  {"command":    │
                                                                   │   "WATER_NOW",  │
                                                                   │   "duration":   │
                                                                   │    3000}        │
                                                                   └─────────────────┘

  ```                                                                 




