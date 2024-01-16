import os
import tkinter as tk
from tkinter import ttk, filedialog
from tkinter.scrolledtext import ScrolledText
import shutil
import re
from pytube import YouTube
import spotipy
import spotipy.oauth2 as oauth2
from youtube_search import YoutubeSearch
import ttkthemes

# Spotify API credentials
SPOTIPY_CLIENT_ID = '...'
SPOTIPY_CLIENT_SECRET = '...'

class SpotifyToMP3Converter:
    def __init__(self, master):
        self.master = master
        self.master.title("Spotify to MP3 Converter")

        # Use themed UI
        self.style = ttkthemes.ThemedStyle(master)
        self.style.set_theme("plastik")

        self.playlist_label = ttk.Label(master, text="Spotify Playlist URL:")
        self.playlist_label.grid(row=0, column=0, pady=5, sticky="w")

        self.playlist_entry = ttk.Entry(master, width=30)
        self.playlist_entry.grid(row=0, column=1, pady=5, sticky="ew")

        self.output_label = ttk.Label(master, text="Output Folder:")
        self.output_label.grid(row=1, column=0, pady=5, sticky="w")

        self.output_entry = ttk.Entry(master, width=30, state="readonly")
        self.output_entry.grid(row=1, column=1, pady=5, sticky="ew")

        self.output_button = ttk.Button(master, text="Browse", command=self.browse_folder)
        self.output_button.grid(row=1, column=2, pady=5, padx=5)

        # Add download status area
        self.status_text = ScrolledText(master, height=8, wrap=tk.WORD, state=tk.DISABLED)
        self.status_text.grid(row=2, column=0, columnspan=3, pady=5)

        self.start_button = ttk.Button(master, text="Start Conversion", command=self.start_conversion)
        self.start_button.grid(row=3, column=0, columnspan=3, pady=10)

        # Spotify API authentication
        auth_manager = oauth2.SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)
        self.spotify = spotipy.Spotify(auth_manager=auth_manager)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        self.output_entry.config(state=tk.NORMAL)
        self.output_entry.delete(0, tk.END)
        self.output_entry.insert(0, folder_selected)
        self.output_entry.config(state="readonly")

    def download_video(self, link, title, output_folder):
        try:
            yt = YouTube(link)
            audio_stream = yt.streams.filter(only_audio=True).first()

            if audio_stream:
                mp3_file = os.path.join(output_folder, f"{title}.mp3")
                audio_stream.download(output_folder, f"{title}.mp3")
                return mp3_file
            else:
                print(f"No available audio stream for {link}")
                return None
        except Exception as e:
            print(f"Error downloading video {link}: {e}")
            return None

    def start_conversion(self):
        playlist_url = self.playlist_entry.get()
        output_folder = self.output_entry.get()

        if not playlist_url or not output_folder:
            self.update_status("Please fill in both fields.")
            return

        youtube_links = self.get_youtube_links(playlist_url)
        mp3_files = []

        for i, link_info in enumerate(youtube_links, start=1):
            link = link_info['link']
            title = link_info['title']

            try:
                self.update_status(f"Downloading {i}/{len(youtube_links)}: {title}")
                mp3_file = self.download_video(link, title, output_folder)
                if mp3_file:
                    mp3_files.append(mp3_file)
            except Exception as e:
                print(f"Error processing {link}: {e}")

        if mp3_files:
            self.update_status(f"Conversion completed. MP3 files saved in '{output_folder}'.")
            print("Conversion completed.")
        else:
            self.update_status("No valid audio files found.")
            print("No valid audio files found.")

    def extract_playlist_id(self, playlist_url):
        match = re.search(r'playlist/(\w+)', playlist_url)
        return match.group(1) if match else None

    def get_youtube_links(self, playlist_url):
        playlist_id = self.extract_playlist_id(playlist_url)

        if not playlist_id:
            self.update_status("Invalid playlist URL.")
            return []

        try:
            playlist = self.spotify.playlist_tracks(playlist_id)
        except Exception as e:
            self.update_status(f"Error retrieving playlist information: {e}")
            return []

        youtube_links = []

        for track in playlist['items']:
            artist = track['track']['artists'][0]['name']
            song_name = track['track']['name']

            try:
                search_results = YoutubeSearch(f'{artist} {song_name} lyrics video', max_results=1).to_dict()
                if search_results:
                    video_url = f"https://www.youtube.com{search_results[0]['url_suffix']}"
                    youtube_links.append({'link': video_url, 'title': f"{artist} - {song_name}"})
            except Exception as e:
                self.update_status(f"Error searching for video: {e}")

        return youtube_links

    def update_status(self, message):
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = SpotifyToMP3Converter(root)
    root.mainloop()
