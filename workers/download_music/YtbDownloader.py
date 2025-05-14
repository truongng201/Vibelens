import yt_dlp
import ffmpeg
import os

def download_ytb_mp3(song_title, song_author, song_id):
    # Build search query for YouTube
    search_query = f"ytsearch1:{song_title} {song_author}"

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': False,
            'no_warnings': True,
            'postprocessors': [],
            'cookies': '/usr/src/app/cookies.txt',  # Path to your cookies file, to bypass bot detection
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Step 1: Search and extract info
            info = ydl.extract_info(search_query, download=False)

            # Handle search results (info is a playlist-like dict)
            if 'entries' in info:
                video_info = info['entries'][0]  # First result
            else:
                video_info = info  # Direct video info (fallback)

            video_url = video_info['webpage_url']
            print(f"🔍 Found: {video_info['title']} ({video_url})")

            # Step 2: Download
            info = ydl.extract_info(video_url, download=True)
            downloaded_file = ydl.prepare_filename(info)
            print(f"✅ Downloaded: {downloaded_file}")

        # Step 3: Convert to MP3
        mp3_file = song_id + ".mp3"

        ffmpeg.input(downloaded_file).output(mp3_file, acodec='libmp3lame', audio_bitrate='192k').run(overwrite_output=True)
        print(f"🎧 Converted to MP3: {mp3_file}")

        # Step 4: Cleanup original file
        os.remove(downloaded_file)
        print(f"🧹 Removed original file: {downloaded_file}")
        return mp3_file
    except Exception as e:
        print(f"❌ Error: {e}")
