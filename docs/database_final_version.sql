-- 1. DATABASE INITIALIZATION
CREATE DATABASE IF NOT EXISTS SmartIrrigation;
USE SmartIrrigation;

-- 2. SCHEMA DEFINITION

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'technician', 'user') DEFAULT 'user',
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    google_id VARCHAR(255) NULL UNIQUE,
    profile_picture TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Plants table: Includes hardware_id and watering logic
CREATE TABLE IF NOT EXISTS plants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    user_id INT,
    hardware_id VARCHAR(50) UNIQUE, -- Unique ID for the ESP32/IoT device
    moisture_threshold INT DEFAULT 30,
    watering_duration INT DEFAULT 10, -- How long the pump runs (seconds)
    image_url VARCHAR(255) DEFAULT 'default_plant.png',
    environment_desc VARCHAR(255) DEFAULT 'Bright, consistent sunlight, near a window',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Moisture Readings table
CREATE TABLE IF NOT EXISTS moisture_readings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plant_id INT,
    moisture_level DECIMAL(5,2),
    pump_status BOOLEAN DEFAULT FALSE,
    is_automated BOOLEAN DEFAULT FALSE,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE CASCADE
);

-- Notifications table
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

-- 3. DATA SEEDING (Run once to populate the UI for testing)

-- Create 2 initial users
INSERT INTO users (username, email, password, role, first_name, last_name) VALUES
('alice_green', 'alice@example.com', 'hashed_pass_1', 'admin', 'Alice', 'Green'),
('bob_farmer', 'bob@example.com', 'hashed_pass_2', 'user', 'Bob', 'Farmer');

-- Link plants to users (Using hardware IDs for your IoT logic)
INSERT INTO plants (name, location, user_id, hardware_id, moisture_threshold, watering_duration) VALUES
('Kitchen Basil', 'South Window', 1, 'ESP32-KITCH-01', 40, 15),
('Office Fern', 'Main Desk', 2, 'ESP32-OFFIC-02', 35, 10),
('Mint Pot', 'Patio', 2, 'ESP32-PATIO-03', 40, 12),
('Living Room Lily', 'Corner Stand', 2, 'ESP32-LIVING-04', 30, 8),
('Greenhouse Tomato', 'Bed A1', 1, 'ESP32-GNRH-05', 45, 20);

-- Populate historical readings for the dashboard
INSERT INTO moisture_readings (plant_id, moisture_level, pump_status, is_automated, recorded_at) VALUES
(1, 42.10, FALSE, FALSE, NOW() - INTERVAL 12 HOUR),
(1, 38.40, TRUE,  TRUE,  NOW() - INTERVAL 10 HOUR),
(2, 45.50, FALSE, FALSE, NOW() - INTERVAL 48 HOUR),
(2, 34.80, TRUE,  TRUE,  NOW() - INTERVAL 24 HOUR),
(3, 42.00, TRUE,  FALSE, NOW() - INTERVAL 5 HOUR),
(4, 28.50, FALSE, FALSE, NOW() - INTERVAL 1 HOUR);

-- Generate initial notifications
INSERT INTO user_notifications (user_id, plant_id, title, message, event_type) VALUES
(1, 1, 'Auto-Watering Success', 'Kitchen Basil was watered for 15s.', 'auto_watering'),
(2, 4, 'Thirsty Plant!', 'Living Room Lily is below 30% moisture.', 'low_moisture'),
(2, NULL, 'System Connected', 'Your account is now synced with the cloud.', 'system');