import os
from pytube import YouTube

def get_video_info(url):
    try:
        yt = YouTube(url)
        return {
            'title': yt.title,
            'duration': yt.length,
            'thumbnail': yt.thumbnail_url,
            'author': yt.author,
            'views': yt.views,
            'streams': yt.streams.filter(progressive=True, file_extension='mp4')
        }
    except Exception as e:
        return {'error': str(e)}

def download_video(url, itag, download_path='downloads'):
    try:
        yt = YouTube(url)
        stream = yt.streams.get_by_itag(itag)
        
        if not os.path.exists(download_path):
            os.makedirs(download_path)
            
        return stream.download(output_path=download_path)
    except Exception as e:
        return None