# Prayer Times Audio Player

Automated system for playing Adhan (prayer call) at scheduled times. Reads prayer schedules from an image and manages audio playback with configurable margins and settings.

## Environment
- Tested on Ubuntu 24.04 LTS
- Compatible with any system supporting Python and required dependencies
- Recommended: Python 3.8+

## Dependencies
```bash
# System packages (Ubuntu)
sudo apt-get install tesseract-ocr portaudio19-dev libsndfile1

# Python packages
pip install sounddevice soundfile opencv-python pytesseract
```

## Required Files
1. `schedule_[month][year].png` - Prayer schedule image (e.g., schedule_nov24.png)
2. `adhan.mp3` - Short adhan audio ("Allah hu Akbar, Allah hu Akbar")
3. `beep.mp3` - Test audio for dry run mode
4. `config.json` - Time margin settings
5. `volume.txt` - Volume control (0-10)
6. `skip.txt` - Optional prayer skip settings

## Configuration Details

### Margin Settings (config.json)
Configure how early the adhan should play before scheduled time.

```json
{
    "global_margin": 5,     # Applied to all prayers unless overridden
    "prayer_margins": {
        "Fajr": 10,        # 10 minutes before Fajr
        "Dhuhr": 5,        # 5 minutes before Dhuhr
        "Asr": 5,          # 5 minutes before Asr
        "Maghrib": 5,      # 5 minutes before Maghrib
        "Isha": 5          # 5 minutes before Isha
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
1. Fajr
2. Dhuhr
3. Asr
4. Maghrib
5. Isha

## Testing Mode (Dry Run)
```bash
python3 prayertimes.py --dryrun
```
Dry run:
- Uses beep.mp3 instead of adhan.mp3
- Tests schedule parsing
- Shows configured margins
- Displays adjusted times
- Verifies audio system
- Tests each prayer time

## Normal Operation
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
- Service logs: `journalctl -u prayer`

## Schedule Image Requirements
Image must contain prayer times table with columns:
- Fajr
- Dhuhr
- Asr
- Maghrib
- Isha

## Example Schedule Structure
```
Fajr    Dhuhr   Asr     Maghrib Isha
06:30   13:00   15:45   17:02   20:00
06:30   13:00   15:45   17:00   20:00
...
```

## Example Execution with '--dryrun'
```
> python3 prayertimes.py --dryrun
2024-11-15 18:42:59,578 - INFO - Starting Prayer Audio Player
2024-11-15 18:42:59,578 - INFO - Initializing PrayerService
2024-11-15 18:42:59,579 - INFO - Loaded config: global margin: 7, prayer margins: {'Fajr': 30, 'Dhuhr': 0, 'Asr': 0, 'Maghrib': 0, 'Isha': 10}
2024-11-15 18:42:59,579 - INFO - Initializing PrayerScheduleManager
2024-11-15 18:42:59,579 - INFO - Initializing AudioPlayer
2024-11-15 18:42:59,579 - INFO - Volume loaded: 9.0/10
2024-11-15 18:42:59,579 - INFO - Running in dry run mode
2024-11-15 18:42:59,579 - INFO - Starting PrayerService
2024-11-15 18:42:59,579 - INFO - Loading/Creating schedule file
2024-11-15 18:42:59,579 - INFO - Parsing schedule for nov 2024
2024-11-15 18:42:59,579 - INFO - Parsing image file: schedule_nov24.png
2024-11-15 18:43:00,423 - INFO - Day 1 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:45', 'Maghrib': '17:02', 'Isha': '20:00'}
2024-11-15 18:43:00,423 - INFO - Day 2 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:45', 'Maghrib': '17:00', 'Isha': '20:00'}
2024-11-15 18:43:00,423 - INFO - Day 3 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:30', 'Maghrib': '16:58', 'Isha': '20:00'}
2024-11-15 18:43:00,423 - INFO - Day 4 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:30', 'Maghrib': '16:56', 'Isha': '20:00'}
2024-11-15 18:43:00,423 - INFO - Day 5 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:30', 'Maghrib': '16:54', 'Isha': '20:00'}
2024-11-15 18:43:00,423 - INFO - Day 6 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:30', 'Maghrib': '16:52', 'Isha': '20:00'}
2024-11-15 18:43:00,423 - INFO - Day 7 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:30', 'Maghrib': '16:51', 'Isha': '20:00'}
2024-11-15 18:43:00,423 - INFO - Day 8 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:30', 'Maghrib': '16:49', 'Isha': '20:00'}
2024-11-15 18:43:00,423 - INFO - Day 9 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:30', 'Maghrib': '16:47', 'Isha': '20:00'}
2024-11-15 18:43:00,423 - INFO - Day 10 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:30', 'Maghrib': '16:46', 'Isha': '20:00'}
2024-11-15 18:43:00,423 - INFO - Day 11 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:30', 'Maghrib': '16:44', 'Isha': '20:00'}
2024-11-15 18:43:00,423 - INFO - Day 12 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:30', 'Maghrib': '16:42', 'Isha': '20:00'}
2024-11-15 18:43:00,423 - INFO - Day 13 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:30', 'Maghrib': '16:41', 'Isha': '20:00'}
2024-11-15 18:43:00,423 - INFO - Day 14 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:30', 'Maghrib': '16:39', 'Isha': '20:00'}
2024-11-15 18:43:00,423 - INFO - Day 15 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:30', 'Maghrib': '16:38', 'Isha': '20:00'}
2024-11-15 18:43:00,424 - INFO - Day 16 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:30', 'Maghrib': '16:36', 'Isha': '20:00'}
2024-11-15 18:43:00,424 - INFO - Day 17 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:15', 'Maghrib': '16:35', 'Isha': '20:00'}
2024-11-15 18:43:00,424 - INFO - Day 18 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:15', 'Maghrib': '16:34', 'Isha': '20:00'}
2024-11-15 18:43:00,424 - INFO - Day 19 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:15', 'Maghrib': '16:32', 'Isha': '20:00'}
2024-11-15 18:43:00,424 - INFO - Day 20 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:15', 'Maghrib': '16:31', 'Isha': '20:00'}
2024-11-15 18:43:00,424 - INFO - Day 21 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:15', 'Maghrib': '16:30', 'Isha': '20:00'}
2024-11-15 18:43:00,424 - INFO - Day 22 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:15', 'Maghrib': '16:29', 'Isha': '20:00'}
2024-11-15 18:43:00,424 - INFO - Day 23 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:15', 'Maghrib': '16:27', 'Isha': '20:00'}
2024-11-15 18:43:00,424 - INFO - Day 24 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:00', 'Maghrib': '16:26', 'Isha': '20:00'}
2024-11-15 18:43:00,424 - INFO - Day 25 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:00', 'Maghrib': '16:25', 'Isha': '20:00'}
2024-11-15 18:43:00,424 - INFO - Day 26 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:00', 'Maghrib': '16:24', 'Isha': '20:00'}
2024-11-15 18:43:00,424 - INFO - Day 27 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:00', 'Maghrib': '16:23', 'Isha': '20:00'}
2024-11-15 18:43:00,424 - INFO - Day 28 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:00', 'Maghrib': '16:22', 'Isha': '20:00'}
2024-11-15 18:43:00,424 - INFO - Day 29 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:00', 'Maghrib': '16:22', 'Isha': '20:00'}
2024-11-15 18:43:00,424 - INFO - Day 30 times: {'Fajr': '06:30', 'Dhuhr': '13:00', 'Asr': '15:00', 'Maghrib': '16:21', 'Isha': '20:00'}
2024-11-15 18:43:00,424 - INFO - Successfully parsed 30 days
2024-11-15 18:43:00,425 - INFO - Saved schedule to schedule_nov24.json
2024-11-15 18:43:00,425 - INFO - Playing startup test audio
2024-11-15 18:43:00,425 - INFO - Attempting to play audio for Startup Test
2024-11-15 18:43:00,425 - INFO - Found audio file: beep.mp3
2024-11-15 18:43:00,798 - INFO - Successfully played audio for Startup Test
2024-11-15 18:43:00,798 - INFO - Dry run mode - Testing with current date schedule
2024-11-15 18:43:00,798 - INFO -
Today's schedule (Day 15):
2024-11-15 18:43:00,806 - INFO -
Testing Fajr:
2024-11-15 18:43:00,806 - INFO - Scheduled time: 06:30
2024-11-15 18:43:00,806 - INFO - Margin: 30.0 minutes
2024-11-15 18:43:00,806 - INFO - Will play at: 06:00
2024-11-15 18:43:00,806 - INFO - Attempting to play audio for Fajr
2024-11-15 18:43:00,807 - INFO - Found audio file: beep.mp3
2024-11-15 18:43:01,211 - INFO - Successfully played audio for Fajr
2024-11-15 18:43:01,211 - INFO -
Testing Dhuhr:
2024-11-15 18:43:01,211 - INFO - Scheduled time: 13:00
2024-11-15 18:43:01,211 - INFO - Margin: 7.0 minutes
2024-11-15 18:43:01,212 - INFO - Will play at: 12:53
2024-11-15 18:43:01,212 - INFO - Attempting to play audio for Dhuhr
2024-11-15 18:43:01,212 - INFO - Found audio file: beep.mp3
2024-11-15 18:43:01,617 - INFO - Successfully played audio for Dhuhr
2024-11-15 18:43:01,618 - INFO -
Testing Asr:
2024-11-15 18:43:01,618 - INFO - Scheduled time: 15:30
2024-11-15 18:43:01,618 - INFO - Margin: 7.0 minutes
2024-11-15 18:43:01,618 - INFO - Will play at: 15:23
2024-11-15 18:43:01,618 - INFO - Attempting to play audio for Asr
2024-11-15 18:43:01,618 - INFO - Found audio file: beep.mp3
2024-11-15 18:43:02,024 - INFO - Successfully played audio for Asr
2024-11-15 18:43:02,024 - INFO -
Testing Maghrib:
2024-11-15 18:43:02,024 - INFO - Scheduled time: 16:38
2024-11-15 18:43:02,025 - INFO - Margin: 7.0 minutes
2024-11-15 18:43:02,025 - INFO - Will play at: 16:31
2024-11-15 18:43:02,025 - INFO - Attempting to play audio for Maghrib
2024-11-15 18:43:02,025 - INFO - Found audio file: beep.mp3
2024-11-15 18:43:02,430 - INFO - Successfully played audio for Maghrib
2024-11-15 18:43:02,430 - INFO -
Testing Isha:
2024-11-15 18:43:02,430 - INFO - Scheduled time: 20:00
2024-11-15 18:43:02,431 - INFO - Margin: 10.0 minutes
2024-11-15 18:43:02,431 - INFO - Will play at: 19:50
2024-11-15 18:43:02,431 - INFO - Attempting to play audio for Isha
2024-11-15 18:43:02,431 - INFO - Found audio file: beep.mp3
2024-11-15 18:43:02,829 - INFO - Successfully played audio for Isha
2024-11-15 18:43:02,830 - INFO -
Dry run completed
```