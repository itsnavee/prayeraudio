import os
import json
import logging
from datetime import datetime, timedelta
import time
import threading
import sounddevice as sd
import soundfile as sf
import argparse
import pandas as pd
from collections import OrderedDict

# Get absolute path of the project root directory
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define paths for different directories
SCHEDULE_DIR = os.path.join(ROOT_DIR, 'schedule')
SOUNDS_DIR = os.path.join(ROOT_DIR, 'sounds')
LOGS_DIR = os.path.join(ROOT_DIR, 'logs')
CONFIG_DIR = os.path.join(ROOT_DIR, 'utils')

def setup_logging():
    logger = logging.getLogger('PrayerAudio')
    logger.setLevel(logging.INFO)
    
    # Create logs directory if it doesn't exist
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    log_file = os.path.join(LOGS_DIR, 'play.log')
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    fh_formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    fh.setFormatter(fh_formatter)
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(ch_formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

logger = setup_logging()

class Config:
    def __init__(self):
        # Default values with numbered prayer names
        self.global_margin = 0
        self.prayer_margins = {
            '01-Fajr': 0,
            '02-Dhuhr': 0,
            '03-Asr': 0,
            '04-Maghrib': 0,
            '05-Isha': 0
        }
        self.load_config()

    def load_config(self):
        try:
            config_file = os.path.join(CONFIG_DIR, 'config.json')
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.global_margin = config.get('global_margin', 0)
                    
                    # Load prayer margins with validation
                    prayer_margins = config.get('prayer_margins', {})
                    for prayer in ['01-Fajr', '02-Dhuhr', '03-Asr', '04-Maghrib', '05-Isha']:
                        if prayer in prayer_margins:
                            self.prayer_margins[prayer] = prayer_margins[prayer]
                        else:
                            logger.warning(f"Missing margin for {prayer} in config.json")
                    
                    logger.info(f"Loaded config: global margin: {self.global_margin}")
                    logger.info(f"Prayer margins: {json.dumps(self.prayer_margins, indent=2)}")
        except Exception as e:
            logger.warning(f"Failed to load config.json, using defaults: {e}")

class AudioPlayer:
    def __init__(self, dry_run=False):
        logger.info("Initializing AudioPlayer")
        self.dry_run = dry_run
        self.volume = self.load_volume()
        self.skip_prayers = self.load_skip_prayers()
        self.last_play_time = {}  # Track last play time for each prayer
        
    def load_volume(self):
        try:
            volume_file = os.path.join(CONFIG_DIR, 'volume.txt')
            volumes = {}
            with open(volume_file, 'r') as f:
                for line in f:
                    key, value = line.strip().split(':')
                    volumes[key.strip()] = int(value.strip())
            
            # Use dryrun volume if in dry run mode, otherwise use execution volume
            vol = volumes['dryrun' if self.dry_run else 'execution']
            vol = max(0, min(10, vol)) / 10.0
            logger.info(f"Volume loaded: {vol * 10}/10 ({'dry run' if self.dry_run else 'execution'} mode)")
            return vol
        except Exception as e:
            logger.warning(f"Failed to load volume.txt, using default: {e}")
            return 0.9 if not self.dry_run else 0.2  # Lower default volume for dry run

    def load_skip_prayers(self):
        try:
            skip_file = os.path.join(CONFIG_DIR, 'skip.txt')
            if os.path.exists(skip_file):
                with open(skip_file, 'r') as f:
                    skip_numbers = [int(x.strip()) for x in f.read().strip().split(',')]
                prayers = ['01-Fajr', '02-Dhuhr', '03-Asr', '04-Maghrib', '05-Isha']
                skip_prayers = [prayers[i-1] for i in skip_numbers if 1 <= i <= 5]
                logger.info(f"Skipping prayers: {', '.join(skip_prayers)}")
                return skip_prayers
        except Exception as e:
            logger.warning(f"Failed to load skip.txt: {e}")
        return []

    def play_audio(self, prayer_name):
        now = datetime.now()
        # Skip if already played in the last minute
        if prayer_name in self.last_play_time:
            time_since_last_play = (now - self.last_play_time[prayer_name]).total_seconds()
            if time_since_last_play < 60:  # Wait at least 60 seconds before playing again
                logger.info(f"Skipping {prayer_name} - played {time_since_last_play} seconds ago")
                return

        if prayer_name in self.skip_prayers and prayer_name != "Startup Test":
            logger.info(f"Skipping {prayer_name} as per skip.txt")
            return

        logger.info(f"Attempting to play audio for {prayer_name}")
        try:
            audio_file = os.path.join(SOUNDS_DIR, 'beep.mp3' if self.dry_run else 'adhan.mp3')
            if os.path.exists(audio_file):
                logger.info(f"Found audio file: {audio_file}")
                data, samplerate = sf.read(audio_file)
                sd.play(data * self.volume, samplerate)
                sd.wait()
                self.last_play_time[prayer_name] = now  # Update last play time
                logger.info(f"Successfully played audio for {prayer_name}")
                return
            raise FileNotFoundError(f"No {audio_file} file found")
        except Exception as e:
            logger.error(f"Error playing audio for {prayer_name}: {str(e)}")

class PrayerScheduleManager:
    def __init__(self, config):
        logger.info("Initializing PrayerScheduleManager")
        self.schedule = {}
        self.config = config
        
    def parse_excel_to_json(self, month, year):
        logger.info(f"Parsing schedule for {month} {year}")
        excel_file = os.path.join(SCHEDULE_DIR, f'schedule_{month.lower()}{str(year)[2:]}.xlsx')
        json_file = os.path.join(SCHEDULE_DIR, f'schedule_{month.lower()}{str(year)[2:]}.json')
        
        # First try to load the current month's JSON
        if os.path.exists(json_file):
            logger.info(f"Loading existing JSON file: {json_file}")
            with open(json_file, 'r') as f:
                self.schedule = json.load(f, object_pairs_hook=OrderedDict)
            return
        
        logger.info(f"Parsing Excel file: {excel_file}")
        schedule_data = OrderedDict()
        
        try:
            # Read Excel file with header information
            df = pd.read_excel(excel_file, header=[0,1,2])  # Multi-level headers
            logger.info(f"Excel columns found: {list(df.columns)}")
            
            # Process each row
            for index, row in df.iterrows():
                if pd.isna(row.iloc[0]):  # Skip empty rows
                    continue
                    
                day = str(index + 1)  # Use index + 1 as day number since we're reading from the data rows
                
                # Store both azan and jamaat times
                schedule_data[day] = {
                    # Main schedule (jamaat times) - used for prayer alarms
                    "jamaat_times": OrderedDict({
                        '01-Fajr': str(row.iloc[9]),     # Column J (Fajr Jamaat)
                        '02-Dhuhr': str(row.iloc[10]),   # Column K (Dhuhr Jamaat)
                        '03-Asr': str(row.iloc[11]),     # Column L (Asr Jamaat)
                        '04-Maghrib': str(row.iloc[12]), # Column M (Maghrib Jamaat)
                        '05-Isha': str(row.iloc[13])     # Column N (Isha Jamaat)
                    }),
                    # Additional context (azan times and sunrise)
                    "azan_times": OrderedDict({
                        '01-Fajr': str(row.iloc[1]),     # Column B (Fajr Azan)
                        'Sunrise': str(row.iloc[2]),     # Column C (Sunrise)
                        '02-Dhuhr': str(row.iloc[3]),    # Column D (Dhuhr Azan)
                        '03-Asr-Shafi': str(row.iloc[4]),# Column E (Asr Shafi Azan)
                        '03-Asr-Hanafi': str(row.iloc[5]),# Column F (Asr Hanafi Azan)
                        '04-Maghrib': str(row.iloc[6]),  # Column G (Maghrib Azan)
                        '05-Isha': str(row.iloc[7])      # Column H (Isha Azan)
                    })
                }
                logger.info(f"Day {day} jamaat times: {schedule_data[day]['jamaat_times']}")
                logger.info(f"Day {day} azan times: {schedule_data[day]['azan_times']}")
            
            if not schedule_data:
                raise ValueError("No valid schedule data found in Excel file")
            
            # Sort the schedule by converting keys to integers for proper numerical ordering
            sorted_schedule = OrderedDict(sorted(schedule_data.items(), key=lambda x: int(x[0])))
            
            # Create schedule directory if it doesn't exist
            os.makedirs(os.path.dirname(json_file), exist_ok=True)
            
            # Save the schedule with proper indentation for readability
            with open(json_file, 'w') as f:
                json.dump(sorted_schedule, f, indent=2)
            logger.info(f"Saved schedule to {json_file}")
            
            self.schedule = sorted_schedule
            
        except Exception as e:
            logger.error(f"Error parsing Excel file: {str(e)}")
            raise

class PrayerService:
    def __init__(self, dry_run=False):
        logger.info("Initializing PrayerService")
        self.config = Config()
        self.schedule_manager = PrayerScheduleManager(self.config)
        self.audio_player = AudioPlayer(dry_run=dry_run)
        self.running = False
        self.dry_run = dry_run
        
    def start(self):
        logger.info("Starting PrayerService")
        self.running = True
        
        now = datetime.now()
        current_month = now.strftime("%b").lower()
        
        logger.info("Loading/Creating schedule file")
        self.schedule_manager.parse_excel_to_json(current_month, now.year)
        
        logger.info("Playing startup test audio")
        self.audio_player.play_audio("Startup Test")
        
        if self.dry_run:
            logger.info("Dry run mode - Testing with current date schedule")
            current_date = str(now.day)
            if current_date in self.schedule_manager.schedule:
                daily_schedule = self.schedule_manager.schedule[current_date]['jamaat_times']  # Use jamaat_times
                logger.info(f"\nToday's schedule (Day {current_date}):")
                
                for prayer, time_str in daily_schedule.items():
                    prayer_time = datetime.strptime(f"{now.year}-{now.month}-{now.day} {time_str}", 
                                                  "%Y-%m-%d %H:%M:%S")
                    margin = timedelta(minutes=self.config.prayer_margins.get(prayer, 0) or 
                                              self.config.global_margin)
                    adjusted_time = prayer_time - margin
                    
                    logger.info(f"\nTesting {prayer}:")
                    logger.info(f"Scheduled time: {time_str}")
                    logger.info(f"Margin: {margin.total_seconds() / 60} minutes")
                    logger.info(f"Will play at: {adjusted_time.strftime('%H:%M')}")
                    
                    self.audio_player.play_audio(prayer)
            
            logger.info("\nDry run completed")
            return

        while self.running:
            now = datetime.now()
            current_date = str(now.day)
            
            if current_date in self.schedule_manager.schedule:
                daily_schedule = self.schedule_manager.schedule[current_date]['jamaat_times']  # Use jamaat_times
                
                for prayer, time_str in daily_schedule.items():
                    prayer_time = datetime.strptime(f"{now.year}-{now.month}-{now.day} {time_str}", 
                                                  "%Y-%m-%d %H:%M:%S")
                    margin = timedelta(minutes=self.config.prayer_margins.get(prayer, 0) or 
                                              self.config.global_margin)
                    adjusted_time = prayer_time - margin
                    
                    if abs(now - adjusted_time) < timedelta(seconds=30):
                        logger.info(f"Triggering {prayer} prayer audio at scheduled time: {time_str}")
                        self.audio_player.play_audio(prayer)
            
            time.sleep(1)
            
    def stop(self):
        logger.info("Stopping PrayerService")
        self.running = False

def main():
    parser = argparse.ArgumentParser(description='Prayer Audio Player')
    parser.add_argument('--dryrun', action='store_true', help='Test functionality with beep sound')
    args = parser.parse_args()

    logger.info("Starting Prayer Audio Player")
    service = PrayerService(dry_run=args.dryrun)
    
    try:
        if args.dryrun:
            logger.info("Running in dry run mode")
        service.start()
        
        if not args.dryrun:
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        service.stop()
        logger.info("Service stopped successfully")

if __name__ == "__main__":
    main()

