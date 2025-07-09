from .api import fetch_recent_track, tracklist, validate_api_key
from static_ffmpeg import run
import subprocess
import os
import json
import glob
from sys import argv, exit, version_info
from .metadata import tag_mp3

def setup_lastmp3_directory():
    #Create the lastmp3 directory structure if it doesn't exist.
    lastmp3_dir = "LastMP3 Downloads"
    
    #lastmp3 directory
    if not os.path.exists(lastmp3_dir):
        os.makedirs(lastmp3_dir)
        print(f"Created directory: {lastmp3_dir}")
    
    #Downloads
    downloads_dir = os.path.join(lastmp3_dir, "Downloads")
    if not os.path.exists(downloads_dir):
        os.makedirs(downloads_dir)
        print(f"Created directory: {downloads_dir}")
    
    return lastmp3_dir, downloads_dir

def load_or_create_config():
    #directory structure
    lastmp3_dir, downloads_dir = setup_lastmp3_directory()
    config_file = os.path.join(lastmp3_dir, "config.json")
    
    # Try to load existing config
    existing_config = {}
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                existing_config = json.load(f)
                print("Found existing configuration file.")
        except (json.JSONDecodeError, KeyError):
            print("Config file is corrupted or invalid. Creating new config.")
            existing_config = {}
    
    #validating api key
    api_key = None
    if 'api_key' in existing_config and existing_config['api_key']:
        print("Validating saved API key...")
        is_valid, message = validate_api_key(existing_config['api_key'])
        if is_valid:
            print("Saved API key is valid")
            api_key = existing_config['api_key']
        else:
            print(f"Saved API key is invalid: {message}")
            print("You'll need to enter a new API key.")
    
    # 
    if not api_key:
        print("\n" + "="*60)
        print("FIRST TIME SETUP - API KEY REQUIRED")
        print("="*60)
        print("To use this tool, you need a Last.fm API key.")
        print("Get your free API key at: https://www.last.fm/api/account/create")
        print("This is a one-time setup - your key will be saved for future use.")
        print("="*60 + "\n")
        
        while True:
            api_key = input("Enter your Last.fm API key: ").strip()
            
            if not api_key:
                print("API key cannot be empty. Please try again.")
                continue
                
            # Validate the API key
            print("Validating API key...")
            is_valid, message = validate_api_key(api_key)
            
            if is_valid:
                print("API key is valid!")
                break
            else:
                print(f"API key validation failed: {message}")
                retry = input("Would you like to try a different API key? (y/n): ").strip().lower()
                if retry != 'y':
                    print("Exiting...")
                    exit(1)
    
    # Handle FFmpeg paths
    ffmpeg_path = None
    ffprobe_path = None
    
    # Try to reuse existing FFmpeg paths if they're valid
    if 'ffmpeg_path' in existing_config and 'ffprobe_path' in existing_config:
        existing_ffmpeg = existing_config['ffmpeg_path']
        existing_ffprobe = existing_config['ffprobe_path']
        if os.path.exists(existing_ffmpeg) and os.path.exists(existing_ffprobe):
            ffmpeg_path = existing_ffmpeg
            ffprobe_path = existing_ffprobe
            print("Using existing FFmpeg paths from config.")
    
    # Get new FFmpeg paths if needed
    if not ffmpeg_path or not ffprobe_path:
        print("Setting up FFmpeg (this might take a moment)...")
        ffmpeg_path, ffprobe_path = run.get_or_fetch_platform_executables_else_raise()
    
    # Save/update config
    config = {
        'api_key': api_key,
        'ffmpeg_path': ffmpeg_path,
        'ffprobe_path': ffprobe_path
    }
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        if existing_config.get('api_key') != api_key:
            print(f"Configuration updated and saved to {config_file}")
        else:
            print(f"Configuration loaded from {config_file}")
            
    except Exception as e:
        print(f"Warning: Could not save config file: {e}")
    
    return api_key, lastmp3_dir, downloads_dir, ffmpeg_path


def main():
    #get username from command line arguments
    if len(argv) < 2:
        print("Error: Username is required. Use --help for usage information.")
        exit(1)
    
    username = argv[1]
    
    #skip if help or version flags
    if username in ["--help", "-h"]:
        print("""
LastMP3 - Last.fm Music Downloader

Usage: lastmp3 [username]

This script fetches the most recent track played by a Last.fm user and downloads it as an MP3 file.
You will be prompted to enter your Last.fm API key if it is not already saved in config.json.
You can then choose to download either the single track or the entire album.

Examples:
  python -m lastmp3 johndoe          # Download recent track for user 'johndoe'
  python -m lastmp3 --help           # Show this help message
  python -m lastmp3 --version        # Show version information

First time setup:
  1. Get your Last.fm API key from: https://www.last.fm/api/account/create
  2. Run the script with a username
  3. Enter your API key when prompted
  4. Choose to download track (t) or album (a)

Files will be saved to: LastMP3 Downloads/Downloads/
Config saved to: LastMP3 Downloads/config.json
          """)
        exit()
    elif username in ["--version", "-v"]:
        print(f"LastMP3 v1.0.0 - Last.fm Music Downloader")
        exit()
    
    api_key, lastmp3_dir, downloads_dir, ffmpeg_path = load_or_create_config()
    ffmpeg_dir = os.path.dirname(ffmpeg_path)
    
    def downloader(song_name:str, artist_name:str):
        # Use the downloads directory we created
        output_path = os.path.join(downloads_dir, "%(title)s.%(ext)s")
        
        try:
            result = subprocess.run([
            "yt-dlp",
            "--ffmpeg-location", ffmpeg_dir,
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "-o", output_path,
            "ytsearch: song_name artist_name".replace("song_name", song_name).replace("artist_name", artist_name)
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Download failed for '{song_name}' by '{artist_name}'")
                print(f"Error: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("Error: yt-dlp not found. Please install it with: pip install yt-dlp")
            return False
        except Exception as e:
            print(f"Download error: {str(e)}")
            return False
    
        # Look for files in the downloads directory
        files = glob.glob(os.path.join(downloads_dir, "*.mp3"))
        if files:
            latest_file = max(files, key=os.path.getctime)
            print(f"Adding metadata to '{os.path.basename(latest_file)}'...")
            
            try:
                tag_mp3(
                    latest_file,
                    title=song_name,
                    artist=artist_name,
                    album=x[2],
                    album_art_url=x[3])
                print(f"Successfully downloaded and tagged: '{song_name}'")
                return True
            except Exception as e:
                print(f"Downloaded but failed to add metadata: {str(e)}")
                return True
        else:
            print("Warning: No MP3 files found after download.")
            return False

    x=fetch_recent_track(username, api_key)
    if x != None:
        print(f"Found recent track: '{x[0]}' by '{x[1]}' from album '{x[2]}'")
        print("="*60)
        user_inp=input("Choose download option:\n  [t] Download just this track\n  [a] Download the entire album\n  [q] Quit\n\nYour choice: ").strip().lower()
        
        if user_inp == "t":
            print(f"Downloading '{x[0]}' by '{x[1]}'...")
            downloader(x[0], x[1])
            print("Download completed!")
        elif user_inp == "a":
            print(f"Fetching album tracklist for '{x[2]}' by '{x[1]}'...")
            y = (tracklist(x[1], x[2], api_key))
            if y:
                print(f"Found {len(y)} tracks in album. Starting download...")
                for i, track in enumerate(y, 1):
                    print(f"Downloading track {i}/{len(y)}: '{track}'...")
                    downloader(track, x[1])
                print("Album download completed!")
            else:
                print("Could not fetch album tracklist.")
        elif user_inp == "q":
            print("Goodbye!")
            exit()
        else:
            print("Invalid choice. Exiting...")
            exit()
    else:
        print(f"Failed to fetch recent tracks for user '{username}'.")
        print("Please check:")
        print("  1. The username is correct")
        print("  2. The user has scrobbled at least one track")
        print("  3. The user's profile is public")
        print("  4. Your internet connection is working")
        exit(1)

if __name__ == "__main__":
    main()