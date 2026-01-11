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
<img width="1034" height="710" alt="image" src="https://github.com/user-attachments/assets/e63fcf8e-1ee1-4ccf-ae62-60743b2d5158" />

```

### Important Safety Notes

⚠️ **CRITICAL SAFETY MEASURES:**
1. **Always use relay** - Never connect pump directly to GPIO pins
2. **Isolate power** - Use separate batteries for pump vs Raspberry Pi
3. **Waterproof connections** if used outdoors
4. **Test with water** in sink before connecting to plants

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

<img width="803" height="697" alt="Screenshot 2026-01-11 174119" src="https://github.com/user-attachments/assets/a86343ad-eea9-4514-b7ba-4d2e310674a5" />

  ```                                                                 




