# Google Drive Sync Setup with Rclone

Complete guide to automatically sync your capture collection to Google Drive using rclone.

## ✅ Quick Working Example

After proper setup, this command successfully syncs your collection:
```bash
# Create directory structure (one-time setup)
rclone mkdir googlepiz:DataCollector
rclone mkdir googlepiz:DataCollector/collection

# Copy collection to Google Drive
rclone copy /home/arif/Projects/DataCollector/collection googlepiz:DataCollector/collection -v --update
```

**Example successful sync output:**
```
Transferred: 105.964M / 105.964 MBytes, 100%, 1.549 MBytes/s
Transferred: 35 / 35, 100%
Elapsed time: 1m10.9s
```

## Table of Contents
1. [Installation](#installation)
2. [Google Drive Setup](#google-drive-setup)
3. [Rclone Configuration](#rclone-configuration)
4. [Sync Commands](#sync-commands)
5. [Automation](#automation)
6. [Monitoring & Troubleshooting](#monitoring--troubleshooting)

---

## Installation

### Ubuntu/Debian
```bash
# Method 1: APT (may be older version)
sudo apt update
sudo apt install rclone

# Method 2: Official installer (recommended - latest version)
curl https://rclone.org/install.sh | sudo bash
```

### Manual Installation
```bash
# Download latest version
cd /tmp
wget https://github.com/rclone/rclone/releases/download/v1.65.0/rclone-v1.65.0-linux-amd64.zip
unzip rclone-v1.65.0-linux-amd64.zip
sudo cp rclone-v1.65.0-linux-amd64/rclone /usr/local/bin/
sudo chmod 755 /usr/local/bin/rclone

# Verify installation
rclone version
```

---

## Google Drive Setup

### 1. Create Google Cloud Project (if needed)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: `DataCollector-Sync`
3. Enable Google Drive API:
   - Navigate to "APIs & Services" → "Library"
   - Search for "Google Drive API"
   - Click "Enable"

### 2. Create OAuth Credentials
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Choose "Desktop application"
4. Name: `DataCollector-Rclone`
5. Download the JSON file (keep it secure)

### 3. Alternative: Use Rclone's Built-in OAuth
- Rclone can use its own OAuth credentials (easier setup)
- Limited to 100 requests/100 seconds per user

---

## Rclone Configuration

### Interactive Setup
```bash
# Start configuration wizard
rclone config

# Follow these steps:
# n) New remote
# name> gdrive
# Storage> drive (Google Drive)
# client_id> [leave blank or paste your OAuth client ID]
# client_secret> [leave blank or paste your OAuth secret]
# scope> 1 (Full access)
# root_folder_id> [leave blank]
# service_account_file> [leave blank]
# Edit advanced config> n
# Use auto config> y (if you have a browser)
```

### Headless Server Setup
If running on a headless server:

```bash
# On your local machine with browser:
rclone authorize "drive"

# Copy the resulting token to your server
# Then continue config on server:
rclone config
# ... follow setup above but paste token when prompted
```

### Verify Configuration
```bash
# Test connection
rclone listremotes

# List Google Drive contents
rclone ls gdrive:

# Check quota
rclone about gdrive:
```

---

## Sync Commands

### Basic Sync Operations

#### 1. One-time Sync (Upload Everything)
```bash
# Sync collection folder to Google Drive
rclone sync /home/arif/Projects/DataCollector/collection gdrive:DataCollector/collection -v

# Options explanation:
# sync: Mirror source to destination (deletes files not in source)
# -v: Verbose output
# gdrive: Your configured remote name
# DataCollector/collection: Path in Google Drive
```

#### 2. Safe Copy (No Deletion)
```bash
# Upload: Copy local files to Google Drive
rclone copy /home/arif/Projects/DataCollector/collection gdrive:DataCollector/collection -v --update

# Download: Copy files from Google Drive to local
rclone copy gdrive:DataCollector/collection /home/arif/Projects/DataCollector/collection -v --update
```

#### 3. Incremental Sync (Recommended)
```bash
# Only sync changed/new files
rclone sync /home/arif/Projects/DataCollector/collection gdrive:DataCollector/collection \
  --update \
  --use-checksum \
  --transfers 4 \
  --checkers 8 \
  --contimeout 60s \
  --timeout 300s \
  --retries 3 \
  --low-level-retries 10 \
  --stats 30s \
  -v
```

### Download from Google Drive

If you have files on Google Drive (uploaded from another PC) that you want to download:

#### Download All Files
```bash
# Download all files from Google Drive to local collection
rclone copy gdrive:DataCollector/collection /home/arif/Projects/DataCollector/collection -v --update

# List what's available on Google Drive first
rclone ls gdrive:DataCollector/collection

# Check what will be downloaded (dry run)
rclone copy gdrive:DataCollector/collection /home/arif/Projects/DataCollector/collection -v --update --dry-run
```

#### Selective Downloads
```bash
# Download only video files
rclone copy gdrive:DataCollector/collection /home/arif/Projects/DataCollector/collection -v --include "*.mp4"

# Download files from specific date
rclone copy gdrive:DataCollector/collection/2025-08-13-15-30 /home/arif/Projects/DataCollector/collection/2025-08-13-15-30 -v

# Download recent files only
rclone copy gdrive:DataCollector/collection /home/arif/Projects/DataCollector/collection -v --max-age 7d
```

#### Bidirectional Sync (Two-Way)
```bash
# Step 1: Download new files from Google Drive
rclone copy gdrive:DataCollector/collection /home/arif/Projects/DataCollector/collection -v --update

# Step 2: Upload new local files to Google Drive  
rclone copy /home/arif/Projects/DataCollector/collection gdrive:DataCollector/collection -v --update
```

### Advanced Options

#### Upload Speed Control
```bash
# Limit bandwidth (useful for background sync)
rclone sync collection gdrive:DataCollector/collection \
  --bwlimit 10M \
  --transfers 2

# Schedule bandwidth (full speed off-peak)
rclone sync collection gdrive:DataCollector/collection \
  --bwlimit "08:00,512k 19:00,10M 23:00,off"
```

#### File Filtering
```bash
# Only sync video files
rclone sync collection gdrive:DataCollector/collection \
  --include "*.mp4" -v

# Exclude temporary files
rclone sync collection gdrive:DataCollector/collection \
  --exclude "*.tmp" \
  --exclude "*.log" -v

# Size filters (skip large files on slow connections)
rclone sync collection gdrive:DataCollector/collection \
  --max-size 100M -v
```

---

## Automation

### 1. Create Sync Script

```bash
# Create sync script
cat > /home/arif/Projects/DataCollector/sync_to_drive.sh << 'EOF'
#!/bin/bash

# DataCollector Google Drive Sync Script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COLLECTION_DIR="$SCRIPT_DIR/collection"
LOG_FILE="$SCRIPT_DIR/sync.log"
LOCK_FILE="/tmp/datacollector_sync.lock"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if already running
if [ -f "$LOCK_FILE" ]; then
    log "ERROR: Sync already running (lock file exists)"
    exit 1
fi

# Create lock file
echo $$ > "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

log "Starting Google Drive sync..."

# Check if collection directory exists
if [ ! -d "$COLLECTION_DIR" ]; then
    log "ERROR: Collection directory not found: $COLLECTION_DIR"
    exit 1
fi

# Check if rclone is configured
if ! rclone listremotes | grep -q "gdrive:"; then
    log "ERROR: Google Drive remote 'gdrive' not configured"
    exit 1
fi

# Perform sync
log "Syncing $COLLECTION_DIR to Google Drive..."

rclone sync "$COLLECTION_DIR" gdrive:DataCollector/collection \
    --update \
    --use-checksum \
    --transfers 4 \
    --checkers 8 \
    --contimeout 60s \
    --timeout 300s \
    --retries 3 \
    --low-level-retries 10 \
    --stats 30s \
    --log-file "$LOG_FILE" \
    --log-level INFO

SYNC_EXIT_CODE=$?

if [ $SYNC_EXIT_CODE -eq 0 ]; then
    log "SUCCESS: Sync completed successfully"
    
    # Optional: Get storage stats
    STATS=$(rclone about gdrive: 2>/dev/null | grep -E "(Total|Used|Free)")
    log "Google Drive Storage: $STATS"
else
    log "ERROR: Sync failed with exit code $SYNC_EXIT_CODE"
fi

log "Sync script finished"
exit $SYNC_EXIT_CODE
EOF

# Make script executable
chmod +x /home/arif/Projects/DataCollector/sync_to_drive.sh
```

### 2. Test the Script
```bash
# Test sync script
cd /home/arif/Projects/DataCollector
./sync_to_drive.sh

# Check logs
tail -f sync.log
```

### 3. Automated Scheduling

#### Option A: Easy Crontab Setup (Recommended)
Use the automated setup script for quick crontab configuration:

```bash
# Run the interactive crontab setup
./setup_crontab.sh

# This script will:
# - Test your rclone configuration
# - Create an optimized sync script (sync_cron.sh)
# - Set up crontab with your chosen frequency
# - Create monitoring tools
```

**Available sync frequencies:**
- Every 5 minutes: `*/5 * * * *`
- Every 10 minutes: `*/10 * * * *`
- Every 15 minutes: `*/15 * * * *` (recommended)
- Every 30 minutes: `*/30 * * * *`
- Every hour: `0 * * * *`
- Custom schedule

**Management commands after setup:**
```bash
# Check sync status
./check_cron_sync.sh

# View current crontab
crontab -l

# Manual sync test
./sync_cron.sh

# View sync logs
tail -f sync_cron.log

# Edit schedule
crontab -e

# Remove/disable DataCollector sync job
crontab -l | grep -v "DataCollector\|sync_cron.sh" | crontab -

# Re-enable sync (example: every 15 minutes)
(crontab -l; echo "*/15 * * * * /home/arif/Projects/DataCollector/sync_cron.sh >/dev/null 2>&1") | crontab -
```

#### Option B: Manual Crontab Setup
```bash
# Edit crontab manually
crontab -e

# Add these lines:
# Sync every 2 hours during active hours
0 8,10,12,14,16,18,20,22 * * * /home/arif/Projects/DataCollector/sync_to_drive.sh >/dev/null 2>&1

# Or sync every 30 minutes
*/30 * * * * /home/arif/Projects/DataCollector/sync_to_drive.sh >/dev/null 2>&1

# View scheduled jobs
crontab -l
```

#### Option B: Systemd Timer (Modern)
```bash
# Create systemd service
sudo tee /etc/systemd/system/datacollector-sync.service > /dev/null << EOF
[Unit]
Description=DataCollector Google Drive Sync
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=$USER
WorkingDirectory=/home/arif/Projects/DataCollector
ExecStart=/home/arif/Projects/DataCollector/sync_to_drive.sh
StandardOutput=journal
StandardError=journal
EOF

# Create systemd timer
sudo tee /etc/systemd/system/datacollector-sync.timer > /dev/null << EOF
[Unit]
Description=DataCollector Google Drive Sync Timer
Requires=datacollector-sync.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=2h
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Enable and start timer
sudo systemctl daemon-reload
sudo systemctl enable datacollector-sync.timer
sudo systemctl start datacollector-sync.timer

# Check timer status
sudo systemctl status datacollector-sync.timer
sudo systemctl list-timers | grep datacollector
```

### 4. Real-time Sync with inotify
For immediate sync when files are created:

```bash
# Install inotify-tools
sudo apt install inotify-tools

# Create real-time sync script
cat > /home/arif/Projects/DataCollector/realtime_sync.sh << 'EOF'
#!/bin/bash

COLLECTION_DIR="/home/arif/Projects/DataCollector/collection"
SYNC_SCRIPT="/home/arif/Projects/DataCollector/sync_to_drive.sh"

echo "Starting real-time sync monitor for $COLLECTION_DIR"

inotifywait -m -r -e create,modify,move,delete "$COLLECTION_DIR" |
while read path action file; do
    echo "[$(date)] Detected $action on $file in $path"
    
    # Wait a bit for file operations to complete
    sleep 5
    
    # Trigger sync
    "$SYNC_SCRIPT" &
done
EOF

chmod +x /home/arif/Projects/DataCollector/realtime_sync.sh
```

---

## Monitoring & Troubleshooting

### Check Sync Status
```bash
# View recent sync logs
tail -n 50 /home/arif/Projects/DataCollector/sync.log

# Check Google Drive storage
rclone about gdrive:

# List recent uploads
rclone ls gdrive:DataCollector/collection --max-age 24h

# Check for sync conflicts
rclone check /home/arif/Projects/DataCollector/collection gdrive:DataCollector/collection
```

### Common Issues & Solutions

#### 1. Authentication Errors
```bash
# Refresh token
rclone config reconnect gdrive:

# Re-authorize
rclone config
```

#### 2. "File not found" / Root Folder ID Issues
If you get `Error 404: File not found: ., notFound`, the remote might have an invalid `root_folder_id`:

```bash
# Check current configuration
rclone config show googlepiz

# If you see root_folder_id = collector or similar invalid ID:
# Backup current config
cp ~/.config/rclone/rclone.conf ~/.config/rclone/rclone.conf.backup

# Remove the problematic root_folder_id line
sed -i '/^root_folder_id = /d' ~/.config/rclone/rclone.conf

# Test connection
rclone lsd googlepiz: --max-depth 1

# If still having issues, reconnect
rclone config reconnect googlepiz:
```

#### 2. Quota Exceeded
```bash
# Check storage usage
rclone about gdrive:

# Clean up old files (be careful!)
rclone delete gdrive:DataCollector/collection --min-age 30d --dry-run
```

#### 3. Network Issues
```bash
# Test with increased retries
rclone sync collection gdrive:DataCollector/collection \
  --retries 10 \
  --low-level-retries 20 \
  --timeout 600s
```

#### 4. Bandwidth Issues
```bash
# Sync with bandwidth limit
rclone sync collection gdrive:DataCollector/collection \
  --bwlimit 1M \
  --transfers 1
```

### Monitoring Script
```bash
# Create monitoring script
cat > /home/arif/Projects/DataCollector/sync_status.sh << 'EOF'
#!/bin/bash

echo "=== DataCollector Sync Status ==="
echo "Date: $(date)"
echo

# Check last sync
if [ -f "sync.log" ]; then
    echo "Last sync log entries:"
    tail -n 10 sync.log
    echo
fi

# Check local collection size
if [ -d "collection" ]; then
    LOCAL_SIZE=$(du -sh collection | cut -f1)
    LOCAL_FILES=$(find collection -type f | wc -l)
    echo "Local collection: $LOCAL_SIZE ($LOCAL_FILES files)"
fi

# Check Google Drive
if rclone listremotes | grep -q "gdrive:"; then
    echo "Google Drive status:"
    rclone about gdrive: 2>/dev/null || echo "Failed to get Google Drive stats"
    
    REMOTE_FILES=$(rclone size gdrive:DataCollector/collection 2>/dev/null | grep "Total objects:" | awk '{print $3}' || echo "Unknown")
    echo "Remote files: $REMOTE_FILES"
else
    echo "Google Drive remote not configured"
fi

echo
echo "=== End Status ==="
EOF

chmod +x sync_status.sh
```

### Performance Optimization

#### For Large Collections
```bash
# Use multiple transfers and checksums
rclone sync collection gdrive:DataCollector/collection \
  --fast-list \
  --transfers 8 \
  --checkers 16 \
  --use-checksum \
  --buffer-size 32M \
  --drive-chunk-size 64M
```

#### For Slow Connections
```bash
# Conservative settings
rclone sync collection gdrive:DataCollector/collection \
  --transfers 2 \
  --checkers 4 \
  --bwlimit 2M \
  --timeout 600s \
  --retries 5
```

---

## Usage Summary

**Quick Setup:**
```bash
# 1. Install rclone
curl https://rclone.org/install.sh | sudo bash

# 2. Configure Google Drive
rclone config

# 3. Test sync
rclone copy collection googlepiz:DataCollector/collection -v --update

# 4. Set up automated crontab sync
./setup_crontab.sh
```

**Daily Commands:**
```bash
# Check sync status (crontab)
./check_cron_sync.sh

# Manual sync
./sync_cron.sh

# View sync logs
tail -f sync_cron.log

# Edit cron schedule
crontab -e
```

Your capture sessions will now automatically backup to Google Drive!