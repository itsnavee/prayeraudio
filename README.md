# Prayer Times Audio Player

Automated system for playing Adhan (prayer call) at scheduled times. Reads prayer schedules from an image and manages audio playback with configurable margins and settings.

## Features
- Schedule parsing from image input
- Configurable time margins (global and per-prayer)
- Volume control
- Skip specific prayers
- Dry run testing mode
- Logging system
- Service automation

## Dependencies
```bash
# System packages
sudo apt-get install tesseract-ocr portaudio19-dev libsndfile1

# Python packages
pip install sounddevice soundfile opencv-python pytesseract
```

## Required Files
- `schedule_[month][year].png` - Prayer schedule image (e.g., schedule_nov24.png)
- `adhan.mp3` - Main audio file
- `beep.mp3` - Test audio file
- `config.json` - Configuration file
- `volume.txt` - Volume level (0-10)
- `skip.txt` - Optional, for skipping prayers

## Configuration
`config.json` example:
```json
{
    "global_margin": 5,
    "prayer_margins": {
        "Fajr": 10,
        "Dhuhr": 5,
        "Asr": 5,
        "Maghrib": 5,
        "Isha": 5
    }
}
```

`skip.txt` example:
```
1,5
```
(Skips Fajr and Isha)

## Usage

```bash
# Test mode
python3 prayertimes.py --dryrun

# Normal operation
python3 prayertimes.py

# Run as service
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

## Logs
- All operations logged to `play.log`
- System service logs: `journalctl -u prayer`

## Schedule Image Format
The schedule image should show prayer times in a table format with columns:
- Fajr
- Dhuhr
- Asr
- Maghrib
- Isha
