"""
Data Loader for FlightVault
Loads OpenFlights dataset into system-versioned tables
"""

import mariadb
import csv
import sys
import os

def load_data():
    """Load OpenFlights data"""
    
    try:
        from src.config import DATABASE_CONFIG
        conn = mariadb.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        
        print("📊 Loading OpenFlights dataset...")
        
        # Load airports
        airports_count = load_airports(cursor)
        
        # Load airlines  
        airlines_count = load_airlines(cursor)
        
        # Load routes
        routes_count = load_routes(cursor)
        
        conn.commit()
        
        print(f"\n✅ Data loaded successfully!")
        print(f"   Airports: {airports_count:,}")
        print(f"   Airlines: {airlines_count:,}")
        print(f"   Routes: {routes_count:,}")
        
        print(f"\nNext: python cli/flightvault.py status")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Loading failed: {e}")
        sys.exit(1)

def load_airports(cursor):
    """Load airports data"""
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'airports.dat')
    
    count = 0
    with open(data_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) >= 14:
                try:
                    cursor.execute("""
                        INSERT IGNORE INTO airports 
                        (airport_id, name, city, country, iata_code, icao_code, 
                         latitude, longitude, altitude, timezone, dst, tz_database, type, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        int(row[0]) if row[0] != '\\N' else None,
                        row[1].strip('"'),
                        row[2].strip('"'),
                        row[3].strip('"'),
                        row[4].strip('"') if row[4] != '\\N' else None,
                        row[5].strip('"') if row[5] != '\\N' else None,
                        float(row[6]) if row[6] != '\\N' else None,
                        float(row[7]) if row[7] != '\\N' else None,
                        int(row[8]) if row[8] != '\\N' else None,
                        float(row[9]) if row[9] != '\\N' else None,
                        row[10].strip('"') if row[10] != '\\N' else None,
                        row[11].strip('"') if row[11] != '\\N' else None,
                        row[12].strip('"') if row[12] != '\\N' else None,
                        row[13].strip('"') if row[13] != '\\N' else None
                    ))
                    if cursor.rowcount > 0:
                        count += 1
                except:
                    continue
    return count

def load_airlines(cursor):
    """Load airlines data"""
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'airlines.dat')
    
    count = 0
    with open(data_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) >= 8:
                try:
                    cursor.execute("""
                        INSERT IGNORE INTO airlines 
                        (airline_id, name, alias, iata_code, icao_code, callsign, country, active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        int(row[0]) if row[0] != '\\N' else None,
                        row[1].strip('"'),
                        row[2].strip('"') if row[2] != '\\N' else None,
                        row[3].strip('"') if row[3] != '\\N' else None,
                        row[4].strip('"') if row[4] != '\\N' else None,
                        row[5].strip('"') if row[5] != '\\N' else None,
                        row[6].strip('"'),
                        row[7].strip('"')
                    ))
                    if cursor.rowcount > 0:
                        count += 1
                except:
                    continue
    return count

def load_routes(cursor):
    """Load routes data"""
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'routes.dat')
    
    count = 0
    with open(data_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) >= 9:
                try:
                    cursor.execute("""
                        INSERT INTO routes 
                        (airline_code, airline_id, source_airport, source_airport_id, 
                         destination_airport, destination_airport_id, codeshare, stops, equipment)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row[0].strip('"') if row[0] != '\\N' else None,
                        int(row[1]) if row[1] != '\\N' else None,
                        row[2].strip('"') if row[2] != '\\N' else None,
                        int(row[3]) if row[3] != '\\N' else None,
                        row[4].strip('"') if row[4] != '\\N' else None,
                        int(row[5]) if row[5] != '\\N' else None,
                        row[6].strip('"') if row[6] != '\\N' else None,
                        int(row[7]) if row[7] != '\\N' else 0,
                        row[8].strip('"') if row[8] != '\\N' else None
                    ))
                    if cursor.rowcount > 0:
                        count += 1
                except:
                    continue
    return count

if __name__ == "__main__":
    load_data()