# Aprovador Fromtis - Combined Version

## Overview

This is a **combined version** of the Aprovador Fromtis system that handles **both Gestor and Consultoria approvals** in a single program.

## What's Different?

### Previous Setup (2 separate programs):
- ❌ `aprovador_gestor.py` - Only approves operations with status '4' (AGUARDANDO APROVAÇÃO DO GESTOR)
- ❌ `aprovador_consultoria.py` - Only approves operations with status '1' (AGUARDANDO APROVAÇÃO DA CONSULTORIA)
- ❌ Required running 2 separate binaries
- ❌ Required 2 separate shell scripts
- ❌ Required 2 separate crontab entries

### New Combined Setup (1 program):
- ✅ `aprovador_combined.py` - Approves **BOTH** types of operations in a single run
- ✅ Single binary to run
- ✅ Single shell script
- ✅ Single crontab entry
- ✅ Unified statistics and logging
- ✅ More efficient (single API call retrieves all operations)

## Features

### Automatic Detection
The program automatically detects which type of approval is needed:
- **Gestor approval**: Status '4' (AGUARDANDO APROVAÇÃO DO GESTOR)
- **Consultoria approval**: Status '1' (AGUARDANDO APROVAÇÃO DA CONSULTORIA)

### Smart Approval Logic
- Uses the correct SOAP endpoint for each approval type
- Applies special cedente rules for consultoria approvals (valorReembolso = '0')
- Handles both approval types in the same query cycle

### Enhanced Statistics
Shows separate counts for:
- Gestor approvals
- Consultoria approvals
- Skipped operations
- Operations by status code

### Error Handling
- ✅ Comprehensive 429 (rate limiting) error handling
- ✅ Exponential backoff retry logic (30s, 60s, 90s)
- ✅ Graceful failure handling
- ✅ 10-second wait between approvals to avoid rate limits

## Files

### Source Code
- `aprovador_fromtis_api/aprovador_combined.py` - Main combined program (359 lines)

### Configuration
- `aprovador_combined.spec` - PyInstaller specification file
- `aprovador_fromtis_api/run_aprovador_combined.sh` - Shell script with PID management

### Binary
- `dist/aprovador_combined` - Standalone executable (28MB)

## How to Deploy

### 1. Build the Binary (if needed)
```bash
cd /home/robot/Dev
.venv/bin/pyinstaller aprovador_combined.spec --clean
```

### 2. Deploy to Production
```bash
# Stop any running instances
pkill -9 -f aprovador_combined

# Copy files
cp dist/aprovador_combined /home/robot/Deploy/aprovador_fromtis_api/
cp aprovador_fromtis_api/run_aprovador_combined.sh /home/robot/Deploy/aprovador_fromtis_api/
chmod +x /home/robot/Deploy/aprovador_fromtis_api/run_aprovador_combined.sh
chmod +x /home/robot/Deploy/aprovador_fromtis_api/aprovador_combined
```

### 3. Test Manually
```bash
cd /home/robot/Deploy/aprovador_fromtis_api
./run_aprovador_combined.sh
```

### 4. Set Up Crontab (Run Every Minute)
```bash
crontab -e
```

Add this line:
```
* * * * * /home/robot/Deploy/aprovador_fromtis_api/run_aprovador_combined.sh >> /home/robot/Deploy/aprovador_fromtis_api/cron_combined.log 2>&1
```

## Migration from Separate Programs

If you want to switch from the separate programs to the combined one:

### Option 1: Replace Both Programs
```bash
# Stop both old programs
pkill -9 -f aprovador_gestor
pkill -9 -f aprovador_consultoria

# Remove old crontab entries
crontab -e
# (Remove the lines for run_aprovador_gestor.sh and run_aprovador_consultoria.sh)

# Add new crontab entry for combined program
# (Add the line shown above)
```

### Option 2: Run in Parallel (for testing)
You can run the combined program alongside the separate ones to verify it works correctly before switching over.

## Monitoring

### Check if Running
```bash
ps aux | grep aprovador_combined
```

### View Logs
```bash
tail -f /home/robot/Deploy/aprovador_fromtis_api/aprovador_combined.log
tail -f /home/robot/Deploy/aprovador_fromtis_api/cron_combined.log
```

### Check PID File
```bash
cat /home/robot/Deploy/aprovador_fromtis_api/aprovador_combined.pid
```

### Stop Manually
```bash
kill $(cat /home/robot/Deploy/aprovador_fromtis_api/aprovador_combined.pid)
# or
pkill -f aprovador_combined
```

## Advantages of Combined Approach

1. **Efficiency**: Single API call retrieves all operations
2. **Simplicity**: One program to maintain instead of two
3. **Unified Logging**: All approvals logged in one place
4. **Better Statistics**: See both approval types in one summary
5. **Easier Deployment**: Single binary to deploy
6. **Less Resource Usage**: One process instead of two
7. **Simpler Crontab**: One entry instead of two

## Technical Details

### Credentials
- Username: `usr.carmel`
- Password: `OGM6Vyl4Q`
- Endpoint: `https://portalfidc4.singulare.com.br/portal-servicos`

### Target Fund
- CNPJ: `32526025000110`

### Query Interval
- 5 seconds between query cycles

### Wait Time Between Approvals
- 10 seconds (to avoid rate limiting)

### Special Cedentes (Consultoria Only)
These cedentes have `valorReembolso` set to '0':
- 36.947.229/0001-85
- 28.080.769/0001-86
- 53.032.513/0001-40

