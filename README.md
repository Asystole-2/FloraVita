# 🌱 Smart Automated Plant Irrigation System

An IoT-based smart irrigation system that monitors soil moisture and automatically waters plants with manual override capability via a web dashboard.

## 🔗 Live Project

> **Live Website:** (https://flrvta.eu/)

## 📋 Table of Contents

* [Features](#-features)
* [System Architecture](#-system-architecture)
* [Hardware Setup](#-hardware-setup)
* [Database Design](#-database-design)
* [PubNub Setup](#-pubnub-setup)
* [Installation](#-installation)
* [Security Features](#-security-features)

## 🚀 Features

* **Real-time Monitoring**: Continuous soil moisture tracking.
* **Automated Watering**: Triggers pump when moisture falls below a set threshold.
* **Manual Control**: Web dashboard with a "Water Now" button.
* **Historical Data**: MySQL storage to visualize moisture trends and pump logs.
* **Hybrid IoT**: Sensor data sent via Laptop; Pump controlled via Raspberry Pi.

## 📈 System Architecture

The system uses a distributed architecture where the sensor and the actuator (pump) are managed by different hardware nodes communicating via PubNub.

The IoT system is built around three key components. First, the IoT Nodes include a Sensor Node, which is a laptop interfaced with a capacitive soil moisture sensor. This node acts as the "Data Producer," sampling analog data, converting it to a digital percentage, and publishing it. Additionally, there is an Actuator Node, a Raspberry Pi interfaced with a 5V Relay and Submersible Pump. This node functions as the "Data Consumer," listening for specific commands to trigger its physical GPIO pins. Second, the Database, implemented in MySQL, serves as the "System of Record." It stores user credentials, historical moisture trends, and a detailed log of every pump activation for both auditing purposes and UI plant card(s). Third, the Web Server acts as the "Control Center," hosting the dashboard, authenticating users via Google OAuth, and interfacing with PubNub to send manual override commands

Data Flow Architecture
The data follows a circular path to ensure the user remains continuously in the loop. It begins with Sensing, where the laptop reads moisture data and publishes it to the moisture-data channel. Next, the Web Server and Database listen to this channel and save each record to MySQL. Then the Web Dashboard fetches the latest MySQL data to display updated UI cards. When a user initiates a Command by clicking "Start Pump", the Web Server publishes a JSON payload to the pump-commands channel. During Actuation, the Raspberry Pi receives this payload and switches the Relay ON, completing the cycle.

<img width="1009" height="692" alt="System Arcgitecture" src="https://github.com/user-attachments/assets/ee96b1b3-b8ce-46cc-93e8-0be6f4b8fc7b" />

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

<img width="1298" height="716" alt="ERD" src="https://github.com/user-attachments/assets/9a14a12b-302a-4b91-a2e8-d5c6690c8ea3" />


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

* **Encryption**: Password hashing in the database.
* **SSL Certification**: Use of an encrypted and secure link between the web server and a browser.
* **Hardware Isolation**: The pump uses an external battery pack to prevent Raspberry Pi power surges.
* **Environment Variables**: No hardcoded credentials in the source code.
 
Security Architecture: Data in Transit
Data is considered "in transit" whenever it moves between IoT devices, the cloud, or the browser. To protect this data, several measures are implemented:
 Transport Layer Security (TLS/SSL) is enforced, meaning all communication with PubNub and the Web Server is forced over HTTPS or secure WebSockets (WSS), preventing Man-in-the-Middle (MITM) attacks. Additionally, PubNub AES Encryption allows data payloads to be encrypted using AES-256 before leaving the device, ensuring that even intercepted packets appear as gibberish without the cipher key. Channel Segmentation is also used by splitting data into two separate channels—one for moisture-data and another for pump-commands—which ensures that a potential leak of sensor data does not grant an attacker the ability to control the hardware.

Security Architecture: Data at Rest
Data is "at rest" in this situation, which is data stored in the MySQL database. To secure this data, several practices are followed:
Password Hashing ensures that user passwords are never stored in plain text. BCrypt was used with a unique salt for every user. Environment Variable Security was maintained by storing sensitive API keys—such as PubNub keys and database credentials—in a .env file, which is explicitly excluded from version control via .gitignore to prevent accidental exposure on platforms like GitHub

Access Control
Web & Database Access is protected through:
SQL Injection Prevention by using Prepared Statements for all database interactions, which blocks attackers from injecting malicious SQL via the UI. Use of OAuth 2.0 integration with Google Login offloads the risk of credential theft to Google’s security infrastructure. 

--- 
