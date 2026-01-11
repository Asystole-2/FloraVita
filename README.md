# 🌱 Smart Automated Plant Irrigation System

An IoT-based smart irrigation system that monitors soil moisture and automatically waters plants with manual override capability via a web dashboard.

## 🔗 Live Project

> **Live Website:** (https://flrvta.eu/)

## 📋 Table of Contents

* [Features](https://www.google.com/search?q=%23-features)
* [System Architecture](https://www.google.com/search?q=%23-system-architecture)
* [Hardware Setup](https://www.google.com/search?q=%23-hardware-setup)
* [Database Design](https://www.google.com/search?q=%23-database-design)
* [PubNub Setup](https://www.google.com/search?q=%23-pubnub-setup)
* [Installation](https://www.google.com/search?q=%23-installation)
* [Security](https://www.google.com/search?q=%23-security-features)
* [Data Flow](#-data-flow-architecture)


## 🚀 Features

* **Real-time Monitoring**: Continuous soil moisture tracking.
* **Automated Watering**: Triggers pump when moisture falls below a set threshold.
* **Manual Control**: Web dashboard with a "Water Now" button.
* **Historical Data**: MySQL storage to visualize moisture trends and pump logs.
* **Hybrid IoT**: Sensor data sent via Laptop; Pump controlled via Raspberry Pi.

## 📈 System Architecture

The system uses a distributed architecture where the sensor and the actuator (pump) are managed by different hardware nodes communicating via PubNub.

<img width="803" height="697" alt="System Architecture" src="https://github.com/user-attachments/assets/a86343ad-eea9-4514-b7ba-4d2e310674a5" />

1. **Input**: Capacitive Soil Moisture Sensor connected to the **Laptop** (via Arduino/Serial).
2. **Logic/Cloud**: Laptop publishes data to **PubNub**.
3. **Storage**: **MySQL** stores historical readings and notifications.
4. **Output**: **Raspberry Pi** subscribes to PubNub commands to trigger the Relay and Pump.

## 🔌 Hardware Setup

### Complete Component List

| Component | Quantity | Purpose |
| --- | --- | --- |
| Raspberry Pi 4 | 1 | Controls the Pump |
| Laptop | 1 | Reads Sensor Data |
| Capacitive Soil Sensor | 1 | Measures moisture |
| 5V 1-Channel Relay | 1 | Controls water pump power |
| Mini Submersible Pump | 1 | Water delivery |
| 4x AA Battery Holder | 1 | Isolated pump power |

### Wiring Diagram

<img width="1034" height="710" alt="Wiring Diagram" src="https://github.com/user-attachments/assets/e63fcf8e-1ee1-4ccf-ae62-60743b2d5158" />

## 🗄️ Database Design

The system uses a MySQL database to manage users, track plant health, and log all automated actions.

### Entity Relationship Diagram (ERD)

<img width="803" height="697" alt="ERD" src="https://github.com/user-attachments/assets/141c2e0b-74af-4d6e-a7be-2b8368d08e12" />

### SQL Setup Script

This script creates the database and populates it with sample data so the UI works immediately upon setup.

```sql
CREATE DATABASE IF NOT EXISTS SmartIrrigation;
USE SmartIrrigation;

-- 1. Users table (Supports Google OAuth)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'technician', 'user') DEFAULT 'user',
    google_id VARCHAR(255) NULL UNIQUE,
    profile_picture TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Plants table (IoT Config)
CREATE TABLE IF NOT EXISTS plants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    user_id INT,
    hardware_id VARCHAR(50) UNIQUE,
    moisture_threshold INT DEFAULT 30,
    watering_duration INT DEFAULT 10,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. Moisture Readings
CREATE TABLE IF NOT EXISTS moisture_readings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plant_id INT,
    moisture_level DECIMAL(5,2),
    pump_status BOOLEAN DEFAULT FALSE,
    is_automated BOOLEAN DEFAULT FALSE,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE CASCADE
);

-- 4. Notifications
CREATE TABLE IF NOT EXISTS user_notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    plant_id INT,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    event_type ENUM('low_moisture', 'auto_watering', 'manual_watering', 'threshold_update', 'system') DEFAULT 'system',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE SET NULL
);

-- SEEDING DATA
INSERT INTO users (username, email, password, first_name) VALUES ('admin_user', 'admin@example.com', 'hash123', 'Admin');
INSERT INTO plants (name, location, user_id, hardware_id, moisture_threshold) VALUES ('Office Fern', 'Desk', 1, 'ESP32-01', 35);

```

---

## 📡 PubNub Setup

1. **Create App**: Log in to [PubNub Dashboard](https://dashboard.pubnub.com/).
2. **Enable Features**: Enable Presence, Stream Controller, and **PAM (Access Manager)**.
3. **Channels**:
* `plant-moisture-data`: Sensor updates.
* `plant-pump-commands`: Control signals for the Raspberry Pi.

---

## 🔧 Installation

### 1. Clone & Environment

```bash
git clone https://github.com/Asystole-2/FloraVita.git
cd smart-plant-irrigation
python -m venv venv
source venv/bin/activate
pip install pubnub RPi.GPIO python-dotenv mysql-connector-python

```

### 2. Configure Secrets

Create a `.env` file:

```env
PUBNUB_PUBLISH_KEY=your_pub_key
PUBNUB_SUBSCRIBE_KEY=your_sub_key
DB_HOST=localhost
DB_USER=root
DB_PASS=your_password

```

---

## 🔒 Security Features

* **PubNub PAM**: Only authorized auth-keys can send pump commands.
* **Hardware Isolation**: The pump uses an external battery pack to prevent Raspberry Pi power surges.
* **Environment Variables**: No hardcoded credentials in the source code.

--- 
