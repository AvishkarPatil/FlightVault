-- Initialize FlightVault database with system versioning
USE flightvault;

-- Enable system versioning
SET GLOBAL system_versioning_alter_history = ON;

-- Create airports table with system versioning
CREATE TABLE IF NOT EXISTS airports (
    airport_id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    country VARCHAR(100),
    iata_code VARCHAR(3),
    icao_code VARCHAR(4),
    latitude DECIMAL(10, 6),
    longitude DECIMAL(11, 6),
    altitude INT,
    timezone DECIMAL(4, 2),
    dst CHAR(1),
    tz_database VARCHAR(50),
    type VARCHAR(20),
    source VARCHAR(20)
) WITH SYSTEM VERSIONING;

-- Create airlines table with system versioning
CREATE TABLE IF NOT EXISTS airlines (
    airline_id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    alias VARCHAR(255),
    iata_code VARCHAR(2),
    icao_code VARCHAR(3),
    callsign VARCHAR(255),
    country VARCHAR(100),
    active CHAR(1)
) WITH SYSTEM VERSIONING;

-- Create routes table with system versioning
CREATE TABLE IF NOT EXISTS routes (
    route_id INT AUTO_INCREMENT PRIMARY KEY,
    airline_code VARCHAR(3),
    airline_id INT,
    source_airport VARCHAR(4),
    source_airport_id INT,
    destination_airport VARCHAR(4),
    destination_airport_id INT,
    codeshare CHAR(1),
    stops INT,
    equipment VARCHAR(255)
) WITH SYSTEM VERSIONING;