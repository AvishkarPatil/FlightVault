

import os

DATABASE_CONFIG = {
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'database': os.getenv('DB_NAME', 'flightvault')
}

SETUP_CONFIG = {
    'user': 'root',
    'password': 'password',
    'host': 'localhost',
    'port': 3306
}