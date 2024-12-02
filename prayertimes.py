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
import re
import numpy as np
import math

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
        
        # First try to load the current month's JSON
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
            
            # Enhanced preprocessing
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply multiple threshold methods and combine results
            thresh1 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            _, thresh2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Combine the results
            combined = cv2.bitwise_and(thresh1, thresh2)
            
            # Denoise
            denoised = cv2.fastNlMeansDenoising(combined)
            
            # Scale up the image (2x)
            scaled = cv2.resize(denoised, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            
            # Add border for better recognition
            bordered = cv2.copyMakeBorder(scaled, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
            
            # Save debug image
            debug_image = f'debug_processed_{month.lower()}{str(year)[2:]}.png'
            cv2.imwrite(debug_image, bordered)
            logger.info(f"Saved debug image to {debug_image}")
            
            # Try different OCR configurations
            configs = [
                r'--oem 3 --psm 6 -c tessedit_char_whitelist="0123456789: "',
                r'--oem 3 --psm 4 -c tessedit_char_whitelist="0123456789: "',
                r'--oem 3 --psm 11 -c tessedit_char_whitelist="0123456789: "'
            ]
            
            def is_valid_prayer_times(times):
                if len(times) != 5:
                    return False
                    
                # Basic validation rules for prayer times
                try:
                    fajr = [int(x) for x in times[0].split(':')]
                    dhuhr = [int(x) for x in times[1].split(':')]
                    asr = [int(x) for x in times[2].split(':')]
                    maghrib = [int(x) for x in times[3].split(':')]
                    isha = [int(x) for x in times[4].split(':')]
                    
                    # Fajr should be early morning (between 4:00 and 7:00)
                    if not (4 <= fajr[0] <= 7):
                        return False
                        
                    # Dhuhr should be around noon (between 12:00 and 14:00)
                    if not (12 <= dhuhr[0] <= 14):
                        return False
                        
                    # Asr should be afternoon (between 14:00 and 16:30)
                    if not (14 <= asr[0] <= 16 or (asr[0] == 16 and asr[1] <= 30)):
                        return False
                        
                    # Maghrib should be evening (between 16:00 and 18:00)
                    if not (16 <= maghrib[0] <= 18):
                        return False
                        
                    # Isha should be night (between 19:00 and 21:00)
                    if not (19 <= isha[0] <= 21):
                        return False
                        
                    return True
                except:
                    return False
            
            valid_time_sets = []
            for config in configs:
                text = pytesseract.image_to_string(bordered, config=config)
                logger.info(f"OCR text with config {config}:\n{text}")
                
                # Split text into lines and process each line
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                
                for line in lines:
                    # Extract all time patterns from the line
                    time_patterns = re.findall(r'\d{1,2}:\d{2}', line)
                    
                    # If we found exactly 5 times in this line
                    if len(time_patterns) == 5 and is_valid_prayer_times(time_patterns):
                        valid_time_sets.append(time_patterns)
            
            # Remove duplicates while preserving order
            seen = set()
            times = [x for x in valid_time_sets if not (tuple(x) in seen or seen.add(tuple(x)))]
            
            if not times:
                raise ValueError("No valid prayer times found in the image")
            
            logger.info(f"Extracted valid time sets: {times}")
            
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
            
            # Save the schedule
            with open(json_file, 'w') as f:
                json.dump(schedule_data, f, indent=4, sort_keys=True)
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