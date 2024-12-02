# check if external speaker is detected
lsusb

# Reinstall and restart audio services
sudo apt-get purge --auto-remove pulseaudio alsa-base
sudo apt-get install pulseaudio alsa-base alsa-utils
sudo alsa force-reload
pulseaudio -k
pulseaudio --start

# Reboot after (optional)
sudo reboot

# Check available sinks
pactl list sinks short

# Check audio devices 
pacmd list-cards

# List pulse devices
pactl list short sources
pactl list short sinks


# example:
pactl list short sinks

551     alsa_output.pci-0000_00_1f.3.analog-stereo.3    PipeWire        s32le 2ch 48000Hz       SUSPENDED
553     alsa_output.usb-Jieli_Technology_UACDemoV1.0_5035811193505B9F-00.analog-stereo.2        PipeWire        s16le 2ch 48000Hz       SUSPENDED


# Test USB speaker (sink 48)
paplay --device=553 azan.mp3

# Set USB speaker as default
pactl set-default-sink 553
paplay azan.mp3


# env
cd /home/blackzero/scripts/prayertimes
source prayertimes_env/bin/activate

python3 prayertimes.py --dryrun


# copy service file
sudo cp prayer.service /etc/systemd/system/
sudo systemctl enable prayer
sudo systemctl start prayer
