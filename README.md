# Prayer Times Audio Player

Automated system for playing Adhan (prayer call) at scheduled times. Reads prayer schedules from Excel files and manages audio playback with configurable margins and settings.

## Project Structure
```
├── schedule/           # Directory for schedule files
│   └── schedule_[month][year].{xlsx,json}
├── sounds/            # Audio files directory
│   ├── adhan.mp3     # Main prayer call audio
│   └── beep.mp3      # Test audio file
├── logs/             # Log files directory
│   └── play.log      # Activity log
├── utils/            # Configuration files
│   ├── config.json   # Margin settings
│   ├── volume.txt    # Volume settings
│   └── skip.txt      # Prayer skip settings
└── prayertimes.py    # Main application file
```

## Dependencies

### Python Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- sounddevice
- soundfile
- pandas
- Other dependencies as listed in requirements.txt

## Configuration

### Margin Settings (utils/config.json)
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

### Volume Settings (utils/volume.txt)
Control volume levels for normal and test modes:
```
execution:8    # Normal mode volume (0-10)
dryrun:2      # Test mode volume (0-10)
```

### Skip Settings (utils/skip.txt)
Skip specific prayers using numbers 1-5:
```
1,5    # Skip Fajr(1) and Isha(5)
```

Prayer numbers:
1. 01-Fajr
2. 02-Dhuhr
3. 03-Asr
4. 04-Maghrib
5. 05-Isha

## Schedule Files

### Excel Format (schedule_[month][year].xlsx)
- Contains both Azan and Jamaat times
- Uses multi-level headers
- Columns:
  - Azan Times: Fajr, Sunrise, Dhuhr, Asr (Shafi/Hanafi), Maghrib, Isha
  - Jamaat Times: Fajr, Dhuhr, Asr, Maghrib, Isha

### JSON Format (schedule_[month][year].json)
- Automatically generated from Excel file
- Contains both azan and jamaat times
- Used for faster subsequent reads

## Features

### Audio Playback
- Configurable volume levels for normal and test modes
- Prevents duplicate playback within 60 seconds
- Supports prayer-specific skip settings
- Uses different audio files for test and normal modes

### Schedule Management
- Automatic conversion of Excel schedules to JSON
- Support for both Azan and Jamaat times
- Organized by day with proper numerical ordering
- Automatic current month schedule loading

### Logging
- Detailed logging in logs/play.log
- Console and file logging
- Includes timestamps and prayer names
- Logs successful plays and errors

## Usage

### Test Mode
```bash
python prayertimes.py --dryrun
```
Features:
- Uses beep.mp3 instead of adhan.mp3
- Lower volume by default
- Tests schedule parsing
- Verifies audio system

### Normal Operation
```bash
python prayertimes.py
```

## Development

The application is structured into several classes:
- `Config`: Handles configuration loading and management
- `AudioPlayer`: Manages audio playback and volume control
- `PrayerScheduleManager`: Handles schedule file parsing and management
- `PrayerService`: Main service coordinating all components

Each component is designed to be modular and maintainable, with proper error handling and logging throughout the application.