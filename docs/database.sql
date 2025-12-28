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
    image_url VARCHAR(255) DEFAULT 'default_plant.png',
    environment_desc VARCHAR(255) DEFAULT 'Bright, consistent sunlight, near a window',
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

-- Dummy Data for UI

--  Insert Sample Moisture Readings for User 2
INSERT INTO moisture_readings (plant_id, moisture_level, pump_status, is_automated, recorded_at) VALUES
-- Readings for 'Office Fern' (Threshold: 35)
(1, 45.50, FALSE, FALSE, NOW() - INTERVAL 2 DAY),
(1, 32.10, TRUE, TRUE, NOW() - INTERVAL 1 DAY), -- Automated watering triggered
(1, 60.00, FALSE, FALSE, NOW() - INTERVAL 23 HOUR),
(1, 38.20, FALSE, FALSE, NOW()),

-- Readings for 'Mint Pot' (Threshold: 40)
(3, 55.00, FALSE, FALSE, NOW() - INTERVAL 3 DAY),
(3, 38.50, TRUE, TRUE, NOW() - INTERVAL 2 DAY), -- Automated watering triggered
(3, 42.10, FALSE, FALSE, NOW() - INTERVAL 1 DAY),
(3, 39.00, TRUE, FALSE, NOW() - INTERVAL 5 HOUR), -- Manual watering by user

-- Readings for 'Living Room Lily' (Threshold: 30)
(4, 28.50, FALSE, FALSE, NOW() - INTERVAL 12 HOUR), -- Low moisture alert
(4, 50.20, FALSE, FALSE, NOW() - INTERVAL 1 HOUR);

--  Insert Sample Notifications for User 2
INSERT INTO user_notifications (user_id, plant_id, title, message, event_type, is_read) VALUES
-- System/Auto Notifications
(2, 1, 'Auto-Watering Active', 'Office Fern moisture dropped to 32%. Automated irrigation engaged.', 'auto_watering', FALSE),
(2, 3, 'Maintenance Required', 'Mint Pot has reached its threshold. System is hydrating.', 'auto_watering', TRUE),

-- Low Moisture Alerts
(2, 4, 'Critical Moisture Alert', 'Living Room Lily is currently at 28%. Please check the reservoir.', 'low_moisture', FALSE),

-- Manual Action Confirmation
(2, 3, 'Manual Sync Confirmed', 'You manually triggered the pump for Mint Pot.', 'manual_watering', TRUE),

-- General System Message
(2, NULL, 'System Online', 'Your FloraVita Node is successfully synchronized with the cloud registry.', 'system', TRUE);


-- TARGETING PLANT IDs:
-- 1 (Office Fern), 2 (Kitchen Basil), 3 (Mint Pot), 4 (Living Room Lily), 5 (Greenhouse Tomato)

INSERT INTO moisture_readings (plant_id, moisture_level, pump_status, is_automated, recorded_at) VALUES
-- Data for 'Office Fern' (Threshold: 35)
(1, 45.20, FALSE, FALSE, NOW() - INTERVAL 48 HOUR),
(1, 34.80, TRUE,  TRUE,  NOW() - INTERVAL 24 HOUR), -- Auto-watering triggered (below 35)
(1, 58.00, FALSE, FALSE, NOW() - INTERVAL 23 HOUR), -- Post-watering saturation
(1, 41.50, FALSE, FALSE, NOW() - INTERVAL 2 HOUR),

-- Data for 'Kitchen Basil' (Threshold: 40)
(2, 42.10, FALSE, FALSE, NOW() - INTERVAL 12 HOUR),
(2, 38.40, TRUE,  TRUE,  NOW() - INTERVAL 10 HOUR), -- Auto-watering triggered (below 40)
(2, 65.00, FALSE, FALSE, NOW() - INTERVAL 9 HOUR),

-- Data for 'Mint Pot' (Threshold: 40)
(3, 50.00, FALSE, FALSE, NOW() - INTERVAL 72 HOUR),
(3, 40.50, FALSE, FALSE, NOW() - INTERVAL 36 HOUR),
(3, 42.00, TRUE,  FALSE, NOW() - INTERVAL 5 HOUR),  -- Manual watering by user (pump status TRUE)

-- Data for 'Living Room Lily' (Threshold: 30)
(4, 32.00, FALSE, FALSE, NOW() - INTERVAL 15 HOUR),
(4, 29.10, FALSE, FALSE, NOW() - INTERVAL 5 HOUR),  -- Critical low state (no pump yet)
(4, 28.50, FALSE, FALSE, NOW()),

-- Data for 'Greenhouse Tomato' (Threshold: 45)
(5, 60.00, FALSE, FALSE, NOW() - INTERVAL 50 HOUR),
(5, 44.50, TRUE,  TRUE,  NOW() - INTERVAL 10 HOUR), -- Auto-watering triggered
(5, 55.20, FALSE, FALSE, NOW() - INTERVAL 2 HOUR);