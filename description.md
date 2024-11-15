# Prayer Audio Player Requirements

# files needed

- schedule_[month][year].png (e.g., schedule_nov24.png)
- config.json (for margins)
- volume.txt (0-10 for volume level)
- skip.txt (optional, comma-separated numbers 1-5 to skip prayers)
- adhan.mp3 (main audio file)
- beep.mp3 (for testing)

## Audio Playback
- Play audio files in MP3 and M4A formats
- Play audio 5 times daily at specific prayer times
- Support test playback on program startup
- Support configurable volume control (0-10 scale)
- Volume settings stored in volume.txt file
- Skip missed prayer times (no delayed playback)

## Schedule Management
- Read prayer times from PDF file named `schedule_[month][year].pdf` (e.g., schedule_nov24.pdf)
- Parse 5 prayer times (Fajr, Dhuhr, Asr, Maghrib, Isha) under "Jamaat Times" section
- Convert PDF to JSON format (schedule_[month].json) for faster subsequent reads
- Only parse PDF if corresponding JSON file doesn't exist

## Time Adjustments
- Support global margin setting (play X minutes before scheduled time)
- Support per-prayer margin settings
- Skip playback if scheduled time is missed

## System Integration
- Run continuously in background
- Start with system boot
- Support volume persistence between restarts

## Logging
- Log file: play.log
- Log format: YYYY-MM-DD HH:MM:SS - PrayerName - status
- Log successful plays and errors

## File Structure
```
├── schedule_nov24.pdf     # Monthly prayer schedule
├── schedule_nov24.json    # Parsed schedule data
├── volume.txt            # Volume setting (0-10)
├── play.log             # Activity log
└── adhan.[mp3/m4a]      # Audio file
```