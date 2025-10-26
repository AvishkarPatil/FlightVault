# FlightVault CLI - Complete Command Reference

## Basic Commands

### 1. System Status Check
```bash
python src/cli/flightvault.py status
```
**Shows:** Database connection, table health, record counts, recent activity

### 2. Timeline Explorer
```bash
# Last 24 hours (default)
python src/cli/flightvault.py timeline --table airports

# Custom time window
python src/cli/flightvault.py timeline --table airports --hours 48
python src/cli/flightvault.py timeline --table routes --hours 1

# All tables
python src/cli/flightvault.py timeline --table airlines --hours 12
```
**Shows:** Minute-by-minute activity, change counts, status levels (CRITICAL/WARNING/NORMAL)

## Diff Analysis Commands

### 3. Smart Diff Viewer
```bash
# Basic diff (1 hour back)
python src/cli/flightvault.py diff --table airports

# Custom time window
python src/cli/flightvault.py diff --table airports --hours 6
python src/cli/flightvault.py diff --table airports --hours 24

# Detailed record-by-record comparison
python src/cli/flightvault.py diff --table airports --detailed
python src/cli/flightvault.py diff --table airports --hours 12 --detailed

# Specific timestamp comparison
python src/cli/flightvault.py diff --table airports --timestamp "2025-10-26T22:50:00"
python src/cli/flightvault.py diff --table airports --timestamp "2025-10-26T04:02:00" --detailed
```
**Shows:** Added/deleted/modified records, field-by-field changes, side-by-side comparison

## Smart Recovery Commands

### 4. Intelligent Recovery
```bash
# Dry run (preview only)
python src/cli/flightvault.py recover --table airports --dry-run

# Smart algorithm recovery
python src/cli/flightvault.py recover --table airports --execute

# Specific timestamp recovery
python src/cli/flightvault.py recover --table airports --timestamp "2025-10-26T04:01:00" --execute
python src/cli/flightvault.py recover --table airports --timestamp "2025-10-26T04:01:00" --dry-run

# Different tables
python src/cli/flightvault.py recover --table routes --execute
python src/cli/flightvault.py recover --table airlines --dry-run
```
**Shows:** Confidence scoring, health assessment, recovery preview, execution results

### 5. Smart Algorithm Analysis
```bash
# Algorithm details
python src/cli/flightvault.py algorithm --table airports
python src/cli/flightvault.py algorithm --table routes
python src/cli/flightvault.py algorithm --table airlines
```
**Shows:** Binary search steps, health scoring, boundary detection, confidence calculation

### 6. Selective Restore (Surgical Recovery)
```bash
# Preview mode
python src/cli/flightvault.py selective --table airports

# Execute selective restore
python src/cli/flightvault.py selective --table airports --execute

# Different tables
python src/cli/flightvault.py selective --table routes --execute
python src/cli/flightvault.py selective --table airlines
```
**Shows:** Change classification, dependency validation, surgical recovery execution

## Real-World Scenarios

### Disaster Investigation
```bash
# 1. Check system status
python src/cli/flightvault.py status

# 2. View recent timeline
python src/cli/flightvault.py timeline --table airports --hours 24

# 3. Analyze specific incident
python src/cli/flightvault.py diff --table airports --timestamp "2025-10-26T04:02:00" --detailed
```

### Mass Deletion Recovery
```bash
# 1. Smart algorithm analysis
python src/cli/flightvault.py algorithm --table airports

# 2. Preview recovery
python src/cli/flightvault.py recover --table airports --dry-run

# 3. Execute recovery
python src/cli/flightvault.py recover --table airports --execute
```

### Surgical Data Repair
```bash
# 1. Analyze changes
python src/cli/flightvault.py selective --table airports

# 2. Execute selective restore
python src/cli/flightvault.py selective --table airports --execute
```

### Historical Analysis
```bash
# Long-term trends
python src/cli/flightvault.py timeline --table airports --hours 168  # 1 week
python src/cli/flightvault.py diff --table airports --hours 72 --detailed  # 3 days

# Specific incident investigation
python src/cli/flightvault.py diff --table airports --timestamp "2025-10-25T14:30:00" --detailed
```

## Table Options
All commands support these tables:
- `--table airports` (default)
- `--table airlines` 
- `--table routes`

## Quick Reference
```bash
# Emergency recovery workflow
python src/cli/flightvault.py status
python src/cli/flightvault.py timeline --table airports --hours 2
python src/cli/flightvault.py recover --table airports --dry-run
python src/cli/flightvault.py recover --table airports --execute

# Investigation workflow  
python src/cli/flightvault.py diff --table airports --hours 6 --detailed
python src/cli/flightvault.py algorithm --table airports
python src/cli/flightvault.py selective --table airports --execute
```

## Advanced Usage
```bash
# Combine with system tools
python src/cli/flightvault.py status > system_health.log
python src/cli/flightvault.py timeline --table airports --hours 24 | grep CRITICAL

# Automation scripts
python src/cli/flightvault.py recover --table airports --execute && echo "Recovery completed"
```

## Command Parameters

### Global Parameters
- `--table` : Target table (airports, airlines, routes)

### Timeline Parameters
- `--hours` : Hours to look back (default: 24)

### Diff Parameters
- `--hours` : Hours to look back (default: 1)
- `--timestamp` : Specific timestamp to compare with (ISO format)
- `--detailed` : Show detailed record-by-record comparison

### Recovery Parameters
- `--timestamp` : Specific timestamp to restore to (ISO format)
- `--dry-run` : Preview mode - no changes made
- `--execute` : Execute actual recovery

### Selective Parameters
- `--execute` : Execute selective restore (default: preview mode)

## CLI Features

### Visual Elements
- **Progress Bars**: Real-time operation progress
- **Color Coding**: Green (success), Red (error), Yellow (warning), Cyan (info)
- **Professional Tables**: Clean formatting with borders and alignment
- **Status Panels**: Bordered information panels
- **Spinners**: Loading animations during operations

### Output Formats
- **Summary Tables**: Quick overview of changes
- **Detailed Records**: Field-by-field breakdowns
- **Side-by-Side Comparison**: Before/after views
- **Timeline Views**: Chronological activity display
- **Health Metrics**: Confidence scores and assessments

## Emergency Procedures

### Database Corruption Detected
```bash
# 1. Immediate assessment
python src/cli/flightvault.py status
python src/cli/flightvault.py timeline --table airports --hours 4

# 2. Find corruption boundary
python src/cli/flightvault.py algorithm --table airports

# 3. Preview recovery
python src/cli/flightvault.py recover --table airports --dry-run

# 4. Execute recovery
python src/cli/flightvault.py recover --table airports --execute
```

### Mass Data Loss
```bash
# 1. Analyze scope
python src/cli/flightvault.py diff --table airports --hours 2 --detailed

# 2. Smart recovery
python src/cli/flightvault.py recover --table airports --execute

# 3. Verify results
python src/cli/flightvault.py status
```

### Partial Corruption
```bash
# 1. Identify affected records
python src/cli/flightvault.py selective --table airports

# 2. Surgical repair
python src/cli/flightvault.py selective --table airports --execute
```

---

**FlightVault CLI - Professional disaster recovery toolkit with enterprise-grade visual interface and intelligent algorithms for database time-travel and surgical data recovery.**