CREATE DATABASE IF NOT EXISTS parking_analyzer;
USE parking_analyzer;

CREATE TABLE IF NOT EXISTS parking_areas (
    area_id INT PRIMARY KEY AUTO_INCREMENT,
    area_name VARCHAR(50) NOT NULL UNIQUE,
    capacity INT NOT NULL CHECK (capacity > 0)
);

CREATE TABLE IF NOT EXISTS parking_transactions (
    transaction_id INT PRIMARY KEY AUTO_INCREMENT,
    vehicle_id VARCHAR(20) NOT NULL,
    area_id INT NOT NULL,
    entry_time DATETIME NOT NULL,
    exit_time DATETIME NULL,
    duration_hours DECIMAL(8,2) NULL,
    CONSTRAINT fk_area
        FOREIGN KEY (area_id) REFERENCES parking_areas(area_id),
    INDEX idx_vehicle_active (vehicle_id, exit_time),
    INDEX idx_entry_time (entry_time)
);

INSERT IGNORE INTO parking_areas (area_name, capacity) VALUES
('P1', 50), ('P2', 30), ('P3', 40), ('P4', 20);