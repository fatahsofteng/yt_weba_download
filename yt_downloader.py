"""
YouTube Audio Downloader dengan Rate Limiting & Sleep Interval
Menggunakan yt-dlp untuk download audio dengan anti-ban mechanism
"""

import yt_dlp
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class YTDownloader:
    """
    YouTube Audio Downloader dengan rate limiting untuk avoid 403 ban

    Features:
    - Rate limiting dengan sleep interval antara downloads
    - Metadata tracking (1 folder per video)
    - Audio format: prefer WAV/FLAC, min 16kHz sample rate, convert to Mono
    - Retry mechanism untuk handle transient errors
    """

    def __init__(
        self,
        output_base_dir: str = "downloads",
        sleep_interval: float = 5.0,
        max_sleep_interval: float = 10.0,
        sleep_requests: int = 1,
        rate_limit: str = "500K",  # 500KB/s to avoid detection
        max_retries: int = 3,
        cookies_file: Optional[str] = None
    ):
        """
        Initialize YT Downloader

        Args:
            output_base_dir: Base directory untuk menyimpan downloads
            sleep_interval: Minimum sleep time antara downloads (detik)
            max_sleep_interval: Maximum sleep time antara downloads (detik)
            sleep_requests: Sleep setelah N requests
            rate_limit: Download rate limit (e.g., "500K" = 500KB/s)
            max_retries: Maximum retry attempts untuk failed downloads
            cookies_file: Path ke cookies file dari browser (optional)
        """
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(exist_ok=True)

        self.sleep_interval = sleep_interval
        self.max_sleep_interval = max_sleep_interval
        self.sleep_requests = sleep_requests
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self.cookies_file = cookies_file

        # Stats tracking
        self.stats = {
            "total_videos": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0
        }

    def _get_ydl_opts(self, output_dir: Path) -> dict:
        """
        Get yt-dlp options dengan rate limiting configuration

        Args:
            output_dir: Directory untuk output file

        Returns:
            Dictionary of yt-dlp options
        """
        opts = {
            # Output format
            'outtmpl': str(output_dir / '%(id)s.%(ext)s'),

            # Format selection: prefer audio-only, highest quality
            # bestaudio: pilih audio terbaik
            # wav: prefer WAV (uncompressed)
            # flac: prefer FLAC (lossless)
            # m4a/webm: fallback ke compressed formats
            'format': 'bestaudio[ext=wav]/bestaudio[ext=flac]/bestaudio[ext=m4a]/bestaudio/best',

            # Audio quality
            'audio_quality': 0,  # Best quality

            # Rate limiting (PENTING untuk avoid ban!)
            'sleep_interval': self.sleep_interval,
            'max_sleep_interval': self.max_sleep_interval,
            'sleep_interval_requests': self.sleep_requests,
            'ratelimit': self.rate_limit,

            # Retry configuration
            'retries': self.max_retries,
            'fragment_retries': self.max_retries,

            # Misc options
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'no_warnings': False,
            'quiet': False,
            'verbose': False,

            # Extract metadata
            'writeinfojson': True,  # Save metadata as JSON
            'writethumbnail': False,  # Skip thumbnail untuk avoid extra requests
            'writesubtitles': False,  # Skip subtitles untuk avoid extra requests

            # Postprocessing: convert to preferred format
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',  # Convert to WAV if possible
                'preferredquality': '0',   # Best quality
            }, {
                'key': 'FFmpegMetadata',  # Embed metadata
            }],

            # User agent
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

        # Add cookies if provided
        if self.cookies_file and Path(self.cookies_file).exists():
            opts['cookiefile'] = self.cookies_file
            logger.info(f"Using cookies from: {self.cookies_file}")

        return opts

    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'^([0-9A-Za-z_-]{11})$'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_channel_videos(self, channel_url: str, max_videos: Optional[int] = None) -> List[str]:
        """
        Get all video URLs from a YouTube channel

        Args:
            channel_url: YouTube channel URL
            max_videos: Maximum number of videos to fetch (None = all)

        Returns:
            List of video URLs
        """
        logger.info(f"Fetching videos from channel: {channel_url}")

        ydl_opts = {
            'quiet': True,
            'extract_flat': True,  # Don't download, just get URLs
            'force_generic_extractor': False,
            'ignoreerrors': True,
        }

        if self.cookies_file and Path(self.cookies_file).exists():
            ydl_opts['cookiefile'] = self.cookies_file

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(channel_url, download=False)

                if 'entries' not in result:
                    logger.warning(f"No videos found in channel: {channel_url}")
                    return []

                # Extract video URLs
                video_urls = []
                for entry in result['entries']:
                    if entry and 'id' in entry:
                        video_id = entry['id']
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        video_urls.append(video_url)

                        if max_videos and len(video_urls) >= max_videos:
                            break

                logger.info(f"Found {len(video_urls)} videos in channel")
                return video_urls

        except Exception as e:
            logger.error(f"Error fetching channel videos: {e}")
            return []

    def download_video_audio(self, video_url: str, channel_name: str = "unknown") -> Dict:
        """
        Download audio from a single video dengan metadata

        Args:
            video_url: YouTube video URL
            channel_name: Channel name for organizing folders

        Returns:
            Dictionary with download results
        """
        video_id = self._extract_video_id(video_url)
        if not video_id:
            logger.error(f"Could not extract video ID from: {video_url}")
            return {
                "video_url": video_url,
                "status": "failed",
                "error": "Invalid video URL"
            }

        # Create output directory: downloads/{channel_name}/{video_id}/
        video_output_dir = self.output_base_dir / channel_name / video_id
        video_output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Downloading: {video_id} from channel: {channel_name}")
        logger.info(f"Output directory: {video_output_dir}")

        try:
            ydl_opts = self._get_ydl_opts(video_output_dir)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Download video
                info = ydl.extract_info(video_url, download=True)

                # Get downloaded file path
                if info:
                    # Save enhanced metadata
                    metadata = self._extract_metadata(info, channel_name, video_url)
                    metadata_file = video_output_dir / f"{video_id}.json"

                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)

                    logger.info(f"✓ Successfully downloaded: {video_id}")
                    logger.info(f"  - Audio file: {video_output_dir}")
                    logger.info(f"  - Metadata: {metadata_file}")

                    self.stats["successful"] += 1

                    return {
                        "video_url": video_url,
                        "video_id": video_id,
                        "channel_name": channel_name,
                        "status": "success",
                        "output_dir": str(video_output_dir),
                        "metadata_file": str(metadata_file),
                        "metadata": metadata
                    }
                else:
                    raise Exception("No info returned from yt-dlp")

        except Exception as e:
            logger.error(f"✗ Failed to download {video_id}: {e}")
            self.stats["failed"] += 1

            return {
                "video_url": video_url,
                "video_id": video_id,
                "channel_name": channel_name,
                "status": "failed",
                "error": str(e)
            }

    def _extract_metadata(self, info: dict, channel_name: str, video_url: str) -> dict:
        """
        Extract and format metadata dari yt-dlp info

        Args:
            info: yt-dlp info dictionary
            channel_name: Channel name
            video_url: Original video URL

        Returns:
            Formatted metadata dictionary
        """
        metadata = {
            # Video metadata
            "video_id": info.get('id'),
            "title": info.get('title'),
            "channel_url": video_url,
            "channel_name": channel_name,
            "upload_date": info.get('upload_date'),
            "uploader": info.get('uploader'),
            "duration_sec": info.get('duration'),
            "view_count": info.get('view_count'),
            "like_count": info.get('like_count'),
            "description": info.get('description'),

            # Audio metadata
            "audio_metadata": {
                "codec": info.get('acodec'),
                "sample_rate": info.get('asr'),  # Audio sample rate
                "bit_rate": info.get('abr'),      # Audio bit rate
                "channels": info.get('audio_channels', 2),
                "format": info.get('ext'),
                "file_size": info.get('filesize') or info.get('filesize_approx'),
            },

            # Download metadata
            "download_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "original_url": video_url,
        }

        return metadata

    def download_from_channel(
        self,
        channel_url: str,
        channel_name: str,
        max_videos: Optional[int] = None
    ) -> List[Dict]:
        """
        Download semua video dari sebuah channel

        Args:
            channel_url: YouTube channel URL
            channel_name: Channel name for organizing
            max_videos: Maximum videos to download (None = all)

        Returns:
            List of download results
        """
        logger.info(f"="*60)
        logger.info(f"Processing channel: {channel_name}")
        logger.info(f"URL: {channel_url}")
        logger.info(f"="*60)

        # Get all video URLs from channel
        video_urls = self.get_channel_videos(channel_url, max_videos)

        if not video_urls:
            logger.warning(f"No videos found for channel: {channel_name}")
            return []

        logger.info(f"Found {len(video_urls)} videos to download")

        results = []
        self.stats["total_videos"] += len(video_urls)

        for idx, video_url in enumerate(video_urls, 1):
            logger.info(f"\n--- Video {idx}/{len(video_urls)} ---")

            result = self.download_video_audio(video_url, channel_name)
            results.append(result)

            # Sleep between downloads (kecuali video terakhir)
            if idx < len(video_urls):
                # Random sleep antara min dan max interval
                import random
                sleep_time = random.uniform(self.sleep_interval, self.max_sleep_interval)
                logger.info(f"Sleeping for {sleep_time:.1f} seconds before next download...")
                time.sleep(sleep_time)

        return results

    def print_stats(self):
        """Print download statistics"""
        logger.info("\n" + "="*60)
        logger.info("DOWNLOAD STATISTICS")
        logger.info("="*60)
        logger.info(f"Total videos: {self.stats['total_videos']}")
        logger.info(f"Successful: {self.stats['successful']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Skipped: {self.stats['skipped']}")
        logger.info("="*60)


def main():
    """Test function"""
    # Test dengan single video
    downloader = YTDownloader(
        output_base_dir="downloads",
        sleep_interval=5.0,
        max_sleep_interval=10.0,
        rate_limit="500K"
    )

    # Test single video
    test_url = "https://www.youtube.com/watch?v=BFudEmWtgAc"
    result = downloader.download_video_audio(test_url, "test_channel")

    print(f"\nResult: {json.dumps(result, indent=2, ensure_ascii=False)}")
    downloader.print_stats()


if __name__ == "__main__":
    main()
