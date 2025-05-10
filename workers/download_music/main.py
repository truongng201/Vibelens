import yt_dlp
import ffmpeg
import os

# Replace with your actual YouTube URL
video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

try:
    # Step 1: Download best audio only using yt-dlp
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',  # Save in current folder using video title
        'quiet': False,
        'no_warnings': True,
        'postprocessors': [],  # We'll convert manually
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        downloaded_file = ydl.prepare_filename(info)  # e.g., "Rick Astley - Never Gonna Give You Up.webm"
        print(f"\n✅ Downloaded: {downloaded_file}")

    # Step 2: Convert audio to .mp3 using ffmpeg-python
    base, _ = os.path.splitext(downloaded_file)
    mp3_file = base + ".mp3"

    ffmpeg.input(downloaded_file).output(mp3_file, acodec='libmp3lame', audio_bitrate='192k').run(overwrite_output=True)
    print(f"🎧 Converted to MP3: {mp3_file}")

    # Step 3: Optional - remove original file
    os.remove(downloaded_file)
    print(f"🧹 Removed original file: {downloaded_file}")

except Exception as e:
    print(f"❌ Error: {e}")
