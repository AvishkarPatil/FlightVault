# FlightVault CLI Commands

## Core Commands

### System Status
```bash
python flightvault.py status
```
Displays database connection status, table health metrics, and recent activity summary.

### Timeline Analysis
```bash
python flightvault.py timeline --table airports
python flightvault.py timeline --table airports --hours 48
```
Shows chronological database changes with minute-level granularity.

### Data Comparison
```bash
python flightvault.py diff --table airports
python flightvault.py diff --table airports --timestamp "2025-10-26T14:30:00"
python flightvault.py diff --table airports --hours 6 --detailed
```
Compares database states between timestamps, showing added/modified/deleted records.

### Smart Recovery
```bash
python flightvault.py recover --table airports --dry-run
python flightvault.py recover --table airports --execute
python flightvault.py recover --table airports --timestamp "2025-10-26T14:30:00" --execute
```
Executes database restoration using AI-powered optimal restore point detection.

### Algorithm Analysis
```bash
python flightvault.py algorithm --table airports
```
Displays binary search analysis, health scoring details, and confidence metrics.

### Selective Restore
```bash
python flightvault.py selective --table airports
python flightvault.py selective --table airports --execute
```
Surgical recovery that preserves legitimate changes while restoring corrupted data.

## Parameters

| Parameter | Description | Default |
|-----------|-------------|----------|
| `--table` | Target table (airports, airlines, routes) | airports |
| `--hours` | Hours to analyze back in time | 24 |
| `--timestamp` | Specific ISO timestamp for comparison | - |
| `--detailed` | Show field-level record comparison | false |
| `--dry-run` | Preview changes without execution | false |
| `--execute` | Execute actual restore operation | false |

**Note:** For selective restore, default is preview mode. Use `--execute` to perform actual selective recovery.

## Usage Examples

```bash
# Check system health
python flightvault.py status

# View recent changes
python flightvault.py timeline --table airports --hours 12

# Compare states
python flightvault.py diff --table airports --hours 2

# Preview recovery
python flightvault.py recover --table airports --dry-run

# Execute recovery
python flightvault.py recover --table airports --execute

# Selective restore (surgical recovery)
python flightvault.py selective --table airports
python flightvault.py selective --table airports --execute

# Algorithm analysis
python flightvault.py algorithm --table airports
```