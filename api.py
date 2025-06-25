import requests

def fetch_recent_track(username, api_key):
    url = f"http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={username}&api_key={api_key}&format=json&limit=1"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        recent_track = data["recenttracks"]["track"][0]
        track_name = recent_track["name"]
        artist_name = recent_track["artist"]["#text"]
        album_name = recent_track["album"]["#text"]
        album_art_images = recent_track.get("image", [])

        album_art_url = None
        for image in album_art_images:
            if image["size"] == "extralarge":
                album_art_url = image["#text"]
                break
        x=[]
        x.append(track_name)
        x.append(artist_name)
        x.append(album_name)
        x.append(album_art_url.replace("300x300", "700x700"))
        return x

    else:
        return f"Failed to fetch recent track. Status code: {response.status_code}"

def tracklist(artist_name, album_name, api_key):
    url = f"https://ws.audioscrobbler.com/2.0/?method=album.getInfo&artist={artist_name}&album={album_name}&api_key={api_key}&format=json"

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if "error" in data:
            print(f"Error: {data['message']}")
            return None
        else:
            album_info = data.get("album", {})
            tracks = album_info.get("tracks", {}).get("track", [])

            tracklist = [track.get("name", "") for track in tracks]
            return tracklist
    elif response.status_code == 404:
        print(f"Album '{album_name}' by '{artist_name}' not found in Last.fm database.")
        return None
    
print(fetch_recent_track("adipaadi", "e994c1872c47cd3eb34d0042c20538ed"))