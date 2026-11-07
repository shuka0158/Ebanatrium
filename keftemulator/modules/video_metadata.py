"""Video metadata extractor"""
import requests
from ..core import Module

class VideoMetadataExtractor(Module):
    name = "video_metadata"
    title = "Video Metadata Extractor"
    category = "Media Analysis"
    description = "Extract video properties, codec, duration, resolution, and embedded metadata"
    accepts = ("url",)

    def run(self, ent, ctx):
        url = ent.value.strip()

        if not any(ext in url.lower() for ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', 'video']):
            return

        ctx.log(f"extracting video metadata: {url}", "info")

        metadata = {
            "url": url,
            "source": "video_metadata"
        }

        # Try to get video info from URL headers
        try:
            resp = requests.head(url, timeout=10, allow_redirects=True)

            if 'content-length' in resp.headers:
                file_size = int(resp.headers['content-length'])
                metadata["file_size"] = file_size
                metadata["file_size_mb"] = round(file_size / (1024*1024), 2)

            if 'content-type' in resp.headers:
                metadata["content_type"] = resp.headers['content-type']

            if 'last-modified' in resp.headers:
                metadata["last_modified"] = resp.headers['last-modified']
        except:
            pass

        # Try yt-dlp / youtube-dl for video info
        try:
            import subprocess
            result = subprocess.run(
                ['yt-dlp', '-J', url],
                capture_output=True,
                timeout=15,
                text=True
            )
            if result.returncode == 0:
                import json
                video_info = json.loads(result.stdout)

                metadata["title"] = video_info.get('title', 'Unknown')
                metadata["duration"] = video_info.get('duration', 0)
                metadata["uploader"] = video_info.get('uploader', 'Unknown')
                metadata["upload_date"] = video_info.get('upload_date', 'Unknown')
                metadata["views"] = video_info.get('view_count', 0)
                metadata["resolution"] = f"{video_info.get('width', '?')}x{video_info.get('height', '?')}"
                metadata["fps"] = video_info.get('fps', 'Unknown')
                metadata["codec_video"] = video_info.get('vcodec', 'Unknown')
                metadata["codec_audio"] = video_info.get('acodec', 'Unknown')

                ctx.log(f"Title: {metadata['title']}", "info")
                ctx.log(f"Duration: {metadata['duration']}s", "info")
        except:
            pass

        # Try ffprobe
        try:
            import subprocess
            result = subprocess.run(
                ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', url],
                capture_output=True,
                timeout=10,
                text=True
            )
            if result.returncode == 0:
                import json
                probe_info = json.loads(result.stdout)

                if 'format' in probe_info:
                    fmt = probe_info['format']
                    metadata["duration"] = float(fmt.get('duration', 0))
                    metadata["bit_rate"] = fmt.get('bit_rate', 'Unknown')

                if 'streams' in probe_info:
                    for stream in probe_info['streams']:
                        if stream['codec_type'] == 'video':
                            metadata["video_codec"] = stream.get('codec_name', 'Unknown')
                            metadata["resolution"] = f"{stream.get('width', '?')}x{stream.get('height', '?')}"
                        elif stream['codec_type'] == 'audio':
                            metadata["audio_codec"] = stream.get('codec_name', 'Unknown')
                            metadata["sample_rate"] = stream.get('sample_rate', 'Unknown')
        except:
            pass

        ctx.emit("company", f"🎬 Video Info", url, metadata, rel="video_meta")
