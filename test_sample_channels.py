"""
Quick test script untuk verify rate limiting dan download functionality
Tests dengan 2 channels, 2-3 videos per channel
"""

import sys
from yt_downloader import YTDownloader
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_sample_channels():
    """Test dengan sample channels dari list"""

    # Sample channels for testing (first 2 from list)
    test_channels = [
        ("leon", "https://www.youtube.com/channel/UCLFgJS-f6UKOJ3Xz0K8Kosg"),
        ("詩詩fly", "https://www.youtube.com/channel/UC9nijyKbu2cQ0lrK6RyGLsw"),
    ]

    logger.info("="*70)
    logger.info("TESTING WITH SAMPLE CHANNELS")
    logger.info("="*70)
    logger.info(f"Channels to test: {len(test_channels)}")
    logger.info(f"Max videos per channel: 3")
    logger.info(f"Sleep interval: 5-10 seconds")
    logger.info(f"Rate limit: 500K")
    logger.info("="*70 + "\n")

    # Initialize downloader with conservative settings
    downloader = YTDownloader(
        output_base_dir="test_downloads",
        sleep_interval=5.0,      # 5 seconds minimum
        max_sleep_interval=10.0,  # 10 seconds maximum
        rate_limit="500K",        # 500KB/s
        max_retries=3
    )

    all_results = {}

    for idx, (channel_name, channel_url) in enumerate(test_channels, 1):
        logger.info(f"\n{'='*70}")
        logger.info(f"TEST CHANNEL {idx}/{len(test_channels)}: {channel_name}")
        logger.info(f"{'='*70}")

        try:
            # Download max 3 videos per channel for testing
            results = downloader.download_from_channel(
                channel_url=channel_url,
                channel_name=channel_name,
                max_videos=3  # Only 3 videos for quick test
            )

            all_results[channel_name] = {
                "channel_url": channel_url,
                "total_videos": len(results),
                "successful": sum(1 for r in results if r['status'] == 'success'),
                "failed": sum(1 for r in results if r['status'] == 'failed'),
                "videos": results
            }

        except Exception as e:
            logger.error(f"Error testing channel {channel_name}: {e}")
            all_results[channel_name] = {
                "channel_url": channel_url,
                "status": "error",
                "error": str(e)
            }

    # Print test results
    logger.info("\n" + "="*70)
    logger.info("TEST RESULTS")
    logger.info("="*70)

    downloader.print_stats()

    # Print per-channel summary
    logger.info("\nPer-channel summary:")
    for channel_name, results in all_results.items():
        if 'successful' in results:
            logger.info(f"  {channel_name}: {results['successful']}/{results['total_videos']} successful")
        else:
            logger.info(f"  {channel_name}: ERROR - {results.get('error', 'Unknown')}")

    # Check for 403 errors
    has_403 = False
    for channel_name, results in all_results.items():
        if 'videos' in results:
            for video in results['videos']:
                if video['status'] == 'failed' and '403' in str(video.get('error', '')):
                    has_403 = True
                    logger.warning(f"\n⚠️  403 Error detected for: {video.get('video_url', 'unknown')}")

    if has_403:
        logger.warning("\n" + "="*70)
        logger.warning("⚠️  403 ERRORS DETECTED!")
        logger.warning("="*70)
        logger.warning("Recommendations:")
        logger.warning("1. Increase sleep interval: --sleep-min 8.0 --sleep-max 15.0")
        logger.warning("2. Decrease rate limit: --rate-limit 300K")
        logger.warning("3. Use browser cookies: --cookies-file cookies.txt")
        logger.warning("4. Wait a bit and retry")
        logger.warning("="*70)
    else:
        logger.info("\n" + "="*70)
        logger.info("✓ TEST PASSED - No 403 errors detected!")
        logger.info("="*70)
        logger.info("You can now proceed with full batch:")
        logger.info("  python batch_download_channels.py")
        logger.info("="*70)

    return all_results


if __name__ == "__main__":
    try:
        results = test_sample_channels()

        # Save test results
        import json
        with open("test_results.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"\nTest results saved to: test_results.json")
        logger.info(f"Downloaded files in: test_downloads/")

    except KeyboardInterrupt:
        logger.info("\n\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
