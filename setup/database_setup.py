"""
Database Setup for FlightVault
Creates MariaDB database with System-Versioned tables
"""

import mariadb
import sys

def setup_database():
    """Create FlightVault database with system-versioned tables"""
    
    try:
        conn = mariadb.connect(
            user="root",
            password="password",
            host="localhost",
            port=3306
        )
        cursor = conn.cursor()
        
        print("🔧 Creating FlightVault database...")
        
        cursor.execute("CREATE DATABASE IF NOT EXISTS flightvault")
        cursor.execute("USE flightvault")
        
        print("📋 Creating system-versioned tables...")
        
        # Airports table
        cursor.execute("""
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
        ) WITH SYSTEM VERSIONING
        """)
        
        # Airlines table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS airlines (
            airline_id INT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            alias VARCHAR(255),
            iata_code VARCHAR(2),
            icao_code VARCHAR(3),
            callsign VARCHAR(255),
            country VARCHAR(100),
            active CHAR(1)
        ) WITH SYSTEM VERSIONING
        """)
        
        # Routes table
        cursor.execute("""
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
        ) WITH SYSTEM VERSIONING
        """)
        
        conn.commit()
        
        # Verify system versioning
        cursor.execute("SHOW CREATE TABLE airports")
        result = cursor.fetchone()
        if "SYSTEM VERSIONING" in result[1]:
            print("✅ System versioning enabled successfully")
        
        print("🎉 Database setup complete!")
        print("\nNext: python setup/data_loader.py")
        
        cursor.close()
        conn.close()
        
    except mariadb.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database()