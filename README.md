# Prayer Times Audio Player

Automated system for playing Adhan (prayer call) at scheduled times. Reads prayer schedules from Excel/image files and manages audio playback with configurable margins and settings.

## Environment
- Tested on Ubuntu 24.04 LTS
- Compatible with any system supporting Python and required dependencies
- Recommended: Python 3.8+

## Dependencies

### System Dependencies (Ubuntu)
```bash
sudo apt-get install tesseract-ocr portaudio19-dev libsndfile1
```

### Python Dependencies
```bash
pip install -r requirements.txt
```

## Required Files

### Core Files
1. `schedule_[month][year].xlsx` - Prayer schedule Excel file (e.g., schedule_dec24.xlsx)
   - Alternative: `schedule_[month][year].png` - Prayer schedule image
2. `adhan.mp3` - Short adhan audio ("Allah hu Akbar, Allah hu Akbar")
3. `beep.mp3` - Test audio for dry run mode

### Configuration Files
4. `config.json` - Time margin settings
5. `volume.txt` - Volume control (0-10)
6. `skip.txt` - Optional prayer skip settings (comma-separated numbers 1-5)

## Configuration Details

### Margin Settings (config.json)
Configure how early the adhan should play before scheduled time.

```json
{
    "global_margin": 5,     # Applied to all prayers unless overridden
    "prayer_margins": {
        "01-Fajr": 10,     # 10 minutes before Fajr
        "02-Dhuhr": 5,     # 5 minutes before Dhuhr
        "03-Asr": 5,       # 5 minutes before Asr
        "04-Maghrib": 5,   # 5 minutes before Maghrib
        "05-Isha": 5       # 5 minutes before Isha
    }
}
```

### Skip Settings (skip.txt)
Skip specific prayers using numbers 1-5:
```
1,5    # Skip Fajr(1) and Isha(5)
2,3    # Skip Dhuhr(2) and Asr(3)
```

Prayer numbers:
1. 01-Fajr
2. 02-Dhuhr
3. 03-Asr
4. 04-Maghrib
5. 05-Isha

## Features

### Audio Playback
- Play audio files in MP3 format
- Play audio 5 times daily at specific prayer times
- Support test playback on program startup
- Support configurable volume control (0-10 scale)
- Volume settings stored in volume.txt file
- Skip missed prayer times (no delayed playback)

### Schedule Management
- Read prayer times from Excel file named `schedule_[month][year].xlsx`
- Alternative: Read from image file `schedule_[month][year].png`
- Parse 5 prayer times under "Jamaat Times" section
- Convert to JSON format (schedule_[month].json) for faster subsequent reads
- Only parse source file if corresponding JSON doesn't exist

### Time Adjustments
- Support global margin setting (play X minutes before scheduled time)
- Support per-prayer margin settings
- Skip playback if scheduled time is missed

### System Integration
- Run continuously in background
- Start with system boot
- Support volume persistence between restarts

## Usage

### Testing Mode (Dry Run)
```bash
python3 prayertimes.py --dryrun
```
Dry run features:
- Uses beep.mp3 instead of adhan.mp3
- Tests schedule parsing
- Shows configured margins
- Displays adjusted times
- Verifies audio system
- Tests each prayer time

### Normal Operation
```bash
# Direct run
python3 prayertimes.py

# As service
sudo cp prayer.service /etc/systemd/system/
sudo systemctl enable prayer
sudo systemctl start prayer
```

## Service Setup
Create `/etc/systemd/system/prayer.service`:
```ini
[Unit]
Description=Prayer Times Audio Service
After=sound.target

[Service]
Type=simple
User=yourusername
Environment=PYTHONPATH=/path/to/venv/lib/python3.x/site-packages
WorkingDirectory=/path/to/project
ExecStart=/path/to/venv/bin/python3 prayertimes.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Logging
- Operations log: `play.log`
- Log format: YYYY-MM-DD HH:MM:SS - PrayerName - status
- Log successful plays and errors
- Service logs: `journalctl -u prayer`

## File Structure
```
├── schedule_dec24.xlsx    # Monthly prayer schedule (Excel)
├── schedule_dec24.png     # Alternative: Monthly prayer schedule (Image)
├── schedule_dec24.json    # Parsed schedule data
├── config.json           # Margin settings
├── volume.txt           # Volume setting (0-10)
├── skip.txt            # Optional prayer skip settings
├── play.log           # Activity log
├── adhan.mp3         # Main prayer call audio
└── beep.mp3         # Test audio file
```