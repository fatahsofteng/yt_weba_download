"""
Batch Download Audio from Multiple YouTube Channels
Reads channel list from file and downloads all audio with metadata
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Tuple
import logging

from yt_downloader import YTDownloader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_channel_list(filename: str) -> List[Tuple[str, str]]:
    """
    Read channel list from file
    Expected format: channel_name,channel_url

    Args:
        filename: Path to channel list file

    Returns:
        List of (channel_name, channel_url) tuples
    """
    channels = []
    filepath = Path(filename)

    if not filepath.exists():
        logger.error(f"Channel list file not found: {filename}")
        sys.exit(1)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Parse channel_name,channel_url
                if ',' in line:
                    parts = line.split(',', 1)
                    if len(parts) == 2:
                        channel_name = parts[0].strip()
                        channel_url = parts[1].strip()
                        channels.append((channel_name, channel_url))
                    else:
                        logger.warning(f"Line {line_num}: Invalid format, skipping: {line}")
                else:
                    logger.warning(f"Line {line_num}: Missing comma separator, skipping: {line}")

        logger.info(f"Loaded {len(channels)} channels from {filename}")
        return channels

    except Exception as e:
        logger.error(f"Error reading channel list: {e}")
        sys.exit(1)


def save_batch_results(results: dict, output_file: str = "batch_results.json"):
    """
    Save batch processing results to JSON file

    Args:
        results: Results dictionary
        output_file: Output filename
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"\nResults saved to: {output_file}")
    except Exception as e:
        logger.error(f"Error saving results: {e}")


def main():
    """Main batch processing function"""
    parser = argparse.ArgumentParser(
        description='Batch download audio from YouTube channels with rate limiting'
    )
    parser.add_argument(
        '--channels-file',
        type=str,
        default='creative_cc_50_yt_channels.txt',
        help='Path to channel list file (default: creative_cc_50_yt_channels.txt)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='downloads',
        help='Base output directory (default: downloads)'
    )
    parser.add_argument(
        '--sleep-min',
        type=float,
        default=5.0,
        help='Minimum sleep interval between downloads in seconds (default: 5.0)'
    )
    parser.add_argument(
        '--sleep-max',
        type=float,
        default=10.0,
        help='Maximum sleep interval between downloads in seconds (default: 10.0)'
    )
    parser.add_argument(
        '--rate-limit',
        type=str,
        default='500K',
        help='Download rate limit, e.g., 500K, 1M (default: 500K)'
    )
    parser.add_argument(
        '--max-videos-per-channel',
        type=int,
        default=None,
        help='Maximum videos to download per channel (default: all)'
    )
    parser.add_argument(
        '--max-channels',
        type=int,
        default=None,
        help='Maximum channels to process (default: all)'
    )
    parser.add_argument(
        '--cookies-file',
        type=str,
        default=None,
        help='Path to browser cookies file (optional, helps avoid 403)'
    )
    parser.add_argument(
        '--start-from',
        type=int,
        default=0,
        help='Start from channel number (0-indexed, for resuming)'
    )

    args = parser.parse_args()

    # Read channel list
    channels = read_channel_list(args.channels_file)

    if not channels:
        logger.error("No channels to process!")
        sys.exit(1)

    # Apply max_channels limit
    if args.max_channels:
        channels = channels[:args.max_channels]

    # Apply start_from offset (for resuming)
    if args.start_from > 0:
        logger.info(f"Starting from channel #{args.start_from + 1}")
        channels = channels[args.start_from:]

    # Initialize downloader
    downloader = YTDownloader(
        output_base_dir=args.output_dir,
        sleep_interval=args.sleep_min,
        max_sleep_interval=args.sleep_max,
        rate_limit=args.rate_limit,
        cookies_file=args.cookies_file
    )

    logger.info("\n" + "="*70)
    logger.info("BATCH DOWNLOAD CONFIGURATION")
    logger.info("="*70)
    logger.info(f"Channels to process: {len(channels)}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Sleep interval: {args.sleep_min}-{args.sleep_max} seconds")
    logger.info(f"Rate limit: {args.rate_limit}")
    logger.info(f"Max videos per channel: {args.max_videos_per_channel or 'All'}")
    logger.info(f"Cookies file: {args.cookies_file or 'None'}")
    logger.info("="*70 + "\n")

    # Process all channels
    all_results = {}
    failed_channels = []

    for idx, (channel_name, channel_url) in enumerate(channels, 1):
        logger.info(f"\n{'='*70}")
        logger.info(f"CHANNEL {idx}/{len(channels)}: {channel_name}")
        logger.info(f"{'='*70}")

        try:
            results = downloader.download_from_channel(
                channel_url=channel_url,
                channel_name=channel_name,
                max_videos=args.max_videos_per_channel
            )

            all_results[channel_name] = {
                "channel_url": channel_url,
                "total_videos": len(results),
                "successful": sum(1 for r in results if r['status'] == 'success'),
                "failed": sum(1 for r in results if r['status'] == 'failed'),
                "videos": results
            }

            # Save intermediate results after each channel
            save_batch_results(all_results, f"batch_results_checkpoint.json")

        except Exception as e:
            logger.error(f"Error processing channel {channel_name}: {e}")
            failed_channels.append((channel_name, str(e)))
            all_results[channel_name] = {
                "channel_url": channel_url,
                "status": "error",
                "error": str(e)
            }

    # Save final results
    logger.info("\n" + "="*70)
    logger.info("BATCH PROCESSING COMPLETE")
    logger.info("="*70)

    # Print overall statistics
    downloader.print_stats()

    # Print failed channels
    if failed_channels:
        logger.warning("\nFailed channels:")
        for channel_name, error in failed_channels:
            logger.warning(f"  - {channel_name}: {error}")

    # Save final results
    save_batch_results(all_results, "batch_results_final.json")

    logger.info("\n✓ All done! Check the results in:")
    logger.info(f"  - Downloads: {args.output_dir}/")
    logger.info(f"  - Results: batch_results_final.json")


if __name__ == "__main__":
    main()
