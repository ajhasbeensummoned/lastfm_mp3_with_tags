from .api import fetch_recent_track, tracklist
from static_ffmpeg import run
import subprocess
import os
import json

def load_or_create_config():
    """Load API key from config file or create new config if it doesn't exist."""
    config_file = "config.json"
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                if 'api_key' in config and config['api_key']:
                    print("API key loaded from config file.")
                    return config['api_key']
        except (json.JSONDecodeError, KeyError):
            print("Config file is corrupted or invalid. Creating new config.")
    
    api_key = input("Please enter your Last.fm API key: ")
    config = {'api_key': api_key}
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"API key saved to {config_file}")
    except Exception as e:
        print(f"Warning: Could not save config file: {e}")
    
    return api_key

username = input("Please enter your last.fm username: ")
api_key = load_or_create_config()

ffmpeg_path, ffprobe_path = run.get_or_fetch_platform_executables_else_raise()
ffmpeg_dir = os.path.dirname(ffmpeg_path)

def downloader(song_name:str, artist_name:str):
    subprocess.run([
    "yt-dlp",
    "--ffmpeg-location", ffmpeg_dir,
    "-x",
    "--audio-format", "mp3",
    "--audio-quality", "0",
    "-o", "Downloads/%(title)s.%(ext)s",
    "ytsearch: song_name artist_name".replace("song_name", song_name).replace("artist_name", artist_name)
    ])

x=fetch_recent_track(username, api_key)
if x != None:
    user_inp=input("Do you just want to download the track or the entire album? ('t' if track, 'a' if album, running anything else will exit the process.) :")
    if user_inp.lower() == "t":
        print(f"Downloading {x[0]} by {x[1]}...")
        downloader(x[0], x[1])
    elif user_inp.lower() == "a":
        y=[]
        print(f"Fetching album tracklist for '{x[2]}' by '{x[1]}'...")
        y = (tracklist(x[1], x[2], api_key))
        for i in y:
            downloader(i, x[1])
    else:
        print("Exiting...")
        exit()