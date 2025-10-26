# FlightVault - Visual Disaster Recovery Tool

**Git for your database using MariaDB System-Versioned Tables**

FlightVault transforms database disasters from hours-long crises into seconds-long fixes through visual time-travel and intelligent recovery algorithms.

## 🎯 The Core Idea

When database disasters strike, FlightVault provides:
- **Visual Timeline Explorer** - Navigate through 24 hours of database history
- **Smart Diff Viewer** - See exactly what changed with color-coded comparisons  
- **Intelligent One-Click Recovery** - Powered by smart restore point algorithm
- **Selective Restore** - Surgical recovery preserving legitimate changes
- **Smart Algorithm** - Binary search through temporal history to find optimal recovery point

## 🚀 Quick Start

### 1. Setup Database
```bash
python setup/database_setup.py
```

### 2. Load Data
```bash
python setup/data_loader.py
```

### 3. Check Status
```bash
python cli/flightvault.py status
```

## 🎮 Features

### Timeline Explorer
```bash
# Show 24-hour timeline of changes
python cli/flightvault.py timeline

# Show last 6 hours
python cli/flightvault.py timeline --hours 6
```

### Smart Diff Viewer
```bash
# Compare current vs 1 hour ago
python cli/flightvault.py diff

# Compare with specific timestamp
python cli/flightvault.py diff --timestamp "2024-01-01T12:00:00"
```

### Intelligent Recovery
```bash
# Preview recovery (dry run)
python cli/flightvault.py recover --dry-run

# Execute recovery
python cli/flightvault.py recover --execute
```

### Selective Restore
```bash
# Surgical recovery - restore only corrupted data
python cli/flightvault.py selective

# Selective restore from specific timestamp
python cli/flightvault.py selective --timestamp "2024-01-01T12:00:00"
```

### Smart Algorithm Details
```bash
# See algorithm in action
python cli/flightvault.py algorithm
```

## 📊 Demo Scenario

**The Crisis**: Delete Mumbai airports
```sql
DELETE FROM airports WHERE city = 'Mumbai';
```

**The Recovery**:
```bash
# 1. Check timeline - see the disaster spike
python cli/flightvault.py timeline

# 2. View the damage
python cli/flightvault.py diff

# 3. Smart recovery finds optimal restore point
python cli/flightvault.py recover --execute
```

**Result**: Recovery in under 30 seconds vs 4+ hours with traditional backups.

## 🧠 Smart Restore Point Algorithm

**The Innovation**: Binary search through temporal history with intelligent health scoring

**How it works**:
1. **Search Window**: Last 24 hours (1,440 minutes)
2. **Binary Search**: Efficiently find disaster boundary  
3. **Health Validation**: Multi-factor scoring at each timestamp
4. **Boundary Detection**: Find exact moment corruption started
5. **Confidence Scoring**: Statistical confidence in selection

**Health Checks**:
- Record count validation
- NULL value detection  
- Foreign key integrity
- Data distribution analysis

## 📁 Project Structure

```
FlightVault/
├── core/                          # Core components
│   ├── temporal_engine.py         # MariaDB temporal operations
│   └── smart_restore_algorithm.py # Smart algorithm (innovation)
├── cli/                           # Command-line interface
│   └── flightvault.py            # Main CLI with all features
├── setup/                         # Database setup
│   ├── database_setup.py         # Create temporal tables
│   └── data_loader.py            # Load OpenFlights data
├── data/                          # OpenFlights CSV files
└── config.py                     # Database configuration
```

## 🔧 Configuration

Update `config.py` with your MariaDB credentials:

```python
DATABASE_CONFIG = {
    'user': 'root',
    'password': 'your_password',
    'host': 'localhost',
    'port': 3306,
    'database': 'flightvault'
}
```

## 🏆 Why FlightVault Wins

### Technical Innovation
- **Smart Algorithm**: Binary search through temporal space with health scoring
- **MariaDB Exclusive**: Leverages System-Versioned Tables (MySQL doesn't have this)
- **Intelligence Layer**: Transforms passive temporal data into active disaster response

### Practical Value  
- **Recovery Time**: Seconds instead of hours
- **Visual Interface**: Makes temporal tables tangible
- **Zero Data Loss**: Precise timestamp restoration
- **Automated Intelligence**: No guessing which timestamp to restore

### Clear Differentiation
- **Focus**: Emergency response (vs audit trails)
- **Innovation**: Smart algorithm (vs simple UI wrapper)
- **Metaphor**: "Git for databases" (instantly understandable)

---

**FlightVault: When disasters strike, recovery takes flight.** ✈️