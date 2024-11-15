import os
import json
import logging
from datetime import datetime, timedelta
import time
import threading
import sounddevice as sd
import soundfile as sf
import argparse
import cv2
import pytesseract

def setup_logging():
    logger = logging.getLogger('PrayerAudio')
    logger.setLevel(logging.INFO)
    
    fh = logging.FileHandler('play.log')
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
        # Default values
        self.global_margin = 0
        self.prayer_margins = {
            'Fajr': 0, 'Dhuhr': 0, 'Asr': 0, 'Maghrib': 0, 'Isha': 0
        }
        self.load_config()

    def load_config(self):
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    config = json.load(f)
                    self.global_margin = config.get('global_margin', 0)
                    self.prayer_margins = config.get('prayer_margins', self.prayer_margins)
                    logger.info(f"Loaded config: global margin: {self.global_margin}, prayer margins: {self.prayer_margins}")
        except Exception as e:
            logger.warning(f"Failed to load config.json, using defaults: {e}")


class AudioPlayer:
    def __init__(self, dry_run=False):
        logger.info("Initializing AudioPlayer")
        self.volume = self.load_volume()
        self.skip_prayers = self.load_skip_prayers()
        self.dry_run = dry_run
        self.last_play_time = {}  # Track last play time for each prayer

    def load_volume(self):
        try:
            with open('volume.txt', 'r') as f:
                vol = int(f.read().strip())
                vol = max(0, min(10, vol)) / 10.0
                logger.info(f"Volume loaded: {vol * 10}/10")
                return vol
        except Exception as e:
            logger.warning(f"Failed to load volume.txt, using default: {e}")
            return 0.9

    def load_skip_prayers(self):
        try:
            if os.path.exists('skip.txt'):
                with open('skip.txt', 'r') as f:
                    skip_numbers = [int(x.strip()) for x in f.read().strip().split(',')]
                prayers = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']
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
            audio_file = 'beep.mp3' if self.dry_run else 'adhan.mp3'
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
        
    def parse_image_to_json(self, month, year):
        logger.info(f"Parsing schedule for {month} {year}")
        image_file = f'schedule_{month.lower()}{str(year)[2:]}.png'
        json_file = f'schedule_{month.lower()}{str(year)[2:]}.json'
        
        if os.path.exists(json_file):
            logger.info(f"Loading existing JSON file: {json_file}")
            with open(json_file, 'r') as f:
                self.schedule = json.load(f)
            return
        
        logger.info(f"Parsing image file: {image_file}")
        schedule_data = {}
        try:
            img = cv2.imread(image_file)
            if img is None:
                raise FileNotFoundError(f"Could not read image file: {image_file}")
                
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            text = pytesseract.image_to_string(thresh)
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # Group times in sets of 5
            times = []
            current_times = []
            
            for line in lines:
                if ':' in line:  # This is a time
                    current_times.append(line)
                    if len(current_times) == 5:
                        times.append(current_times)
                        current_times = []
            
            # Process each set of 5 times
            for day, prayer_times in enumerate(times, 1):
                if len(prayer_times) == 5:
                    schedule_data[str(day)] = {
                        'Fajr': prayer_times[0],
                        'Dhuhr': prayer_times[1],
                        'Asr': prayer_times[2],
                        'Maghrib': prayer_times[3],
                        'Isha': prayer_times[4]
                    }
                    logger.info(f"Day {day} times: {schedule_data[str(day)]}")
            
            if not schedule_data:
                raise ValueError("No valid schedule data found in image")
                
            logger.info(f"Successfully parsed {len(schedule_data)} days")
            
            # Pretty print JSON
            with open(json_file, 'w') as f:
                json.dump(
                    schedule_data,
                    f,
                    indent=4,
                    sort_keys=True,
                    ensure_ascii=False,
                    separators=(',', ': ')
                )
                logger.info(f"Saved schedule to {json_file}")
            self.schedule = schedule_data
            
        except Exception as e:
            logger.error(f"Error parsing image: {str(e)}")
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
        self.schedule_manager.parse_image_to_json(current_month, now.year)
        
        logger.info("Playing startup test audio")
        self.audio_player.play_audio("Startup Test")
        
        if self.dry_run:
            logger.info("Dry run mode - Testing with current date schedule")
            current_date = str(now.day)
            if current_date in self.schedule_manager.schedule:
                daily_schedule = self.schedule_manager.schedule[current_date]
                logger.info(f"\nToday's schedule (Day {current_date}):")
                
                for prayer, time_str in daily_schedule.items():
                    prayer_time = datetime.strptime(f"{now.year}-{now.month}-{now.day} {time_str}", 
                                                  "%Y-%m-%d %H:%M")
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
                daily_schedule = self.schedule_manager.schedule[current_date]
                
                for prayer, time_str in daily_schedule.items():
                    prayer_time = datetime.strptime(f"{now.year}-{now.month}-{now.day} {time_str}", 
                                                  "%Y-%m-%d %H:%M")
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