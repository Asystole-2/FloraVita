CREATE DATABASE IF NOT EXISTS SmartIrrigation;
USE SmartIrrigation;

-- Users table: Handles authentication, roles, and profile settings
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'technician', 'user') DEFAULT 'user',
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    bio TEXT,
    profile_picture VARCHAR(255) DEFAULT 'default_profile.png',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

--  Plants table: Defines the monitored plants/IOT devices
-- Stores thresholds used for automated actuation logic
CREATE TABLE IF NOT EXISTS plants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    user_id INT,
    moisture_threshold INT DEFAULT 30, -- Trigger pump below this percentage
    status ENUM('active', 'maintenance', 'inactive') DEFAULT 'active',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

--  Moisture Readings table: Stores historical sensor data
-- Includes 'is_automated' to track system-led vs user-led watering
CREATE TABLE IF NOT EXISTS moisture_readings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plant_id INT,
    moisture_level DECIMAL(5,2),
    pump_status BOOLEAN DEFAULT FALSE,
    is_automated BOOLEAN DEFAULT FALSE, -- Identifies if the system triggered the pump
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE CASCADE
);

--  Notifications table: Stores alerts for watering needs and actions
CREATE TABLE IF NOT EXISTS user_notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    plant_id INT,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    event_type ENUM('low_moisture', 'auto_watering', 'manual_watering', 'system') DEFAULT 'system',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE SET NULL
);

-- Register 2 users then insert the sample data
INSERT INTO plants (name, location, user_id, moisture_threshold) VALUES
('Office Fern', 'Main Desk', 2, 35),
('Kitchen Basil', 'South Window', 1, 40),
('Mint Pot', 'Patio', 2, 40),
('Living Room Lily', 'Corner Stand', 2, 30),
('Greenhouse Tomato', 'Bed A1', 1, 45 );

