# YouTube Audio Downloader with Rate Limiting

Solusi untuk download audio dari YouTube channels dengan anti-ban mechanism menggunakan rate limiting dan sleep intervals.

## 🎯 Features

- **Rate Limiting**: Otomatis throttle download speed untuk avoid detection
- **Sleep Intervals**: Random sleep antara downloads (5-10 detik default)
- **Anti-Ban Mechanism**:
  - Menggunakan yt-dlp dengan sleep interval antar requests
  - Support cookies dari browser untuk better authentication
  - Rate limit per download (500KB/s default)
- **Metadata Tracking**: 1 folder per video dengan complete metadata
- **Audio Format**: Prefer WAV/FLAC, minimum 16kHz sample rate
- **Batch Processing**: Process multiple channels dari file list
- **Resume Capability**: Bisa resume dari channel tertentu jika interrupted
- **Checkpoint Saving**: Auto-save progress setelah setiap channel

## 📋 Requirements

```bash
pip install yt-dlp requests
```

**Optional (untuk audio conversion):**
- ffmpeg (untuk convert ke WAV/FLAC dan audio processing)

## 🚀 Quick Start

### 1. Test dengan Single Video

```bash
python yt_downloader.py
```

### 2. Batch Download dari Channel List

```bash
# Basic: download semua channels dengan default settings
python batch_download_channels.py

# Dengan custom settings:
python batch_download_channels.py \
  --channels-file creative_cc_50_yt_channels.txt \
  --output-dir downloads \
  --sleep-min 5.0 \
  --sleep-max 10.0 \
  --rate-limit 500K

# Limit videos per channel (untuk testing):
python batch_download_channels.py \
  --max-videos-per-channel 5 \
  --max-channels 3

# Resume dari channel ke-10 (jika interrupted):
python batch_download_channels.py --start-from 10
```

## 🔧 Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--channels-file` | `creative_cc_50_yt_channels.txt` | Path ke channel list file |
| `--output-dir` | `downloads` | Base directory untuk output |
| `--sleep-min` | `5.0` | Minimum sleep interval (seconds) |
| `--sleep-max` | `10.0` | Maximum sleep interval (seconds) |
| `--rate-limit` | `500K` | Download rate limit (500KB/s) |
| `--max-videos-per-channel` | All | Limit videos per channel |
| `--max-channels` | All | Limit total channels to process |
| `--cookies-file` | None | Path to browser cookies (helps avoid 403) |
| `--start-from` | 0 | Start from channel number (for resuming) |

## 📁 Output Structure

```
downloads/
├── {channel_name}/
│   ├── {video_id}/
│   │   ├── {video_id}.wav          # Audio file
│   │   ├── {video_id}.json         # Complete metadata
│   │   └── {video_id}.info.json    # yt-dlp info (auto-generated)
│   ├── {video_id_2}/
│   │   ├── ...
batch_results_checkpoint.json   # Progress checkpoint
batch_results_final.json        # Final results summary
```

## 📊 Metadata Format

Each video has a JSON file dengan format:

```json
{
  "video_id": "Jq7llIkbJeA",
  "title": "Video Title",
  "channel_url": "https://www.youtube.com/@channel",
  "channel_name": "channel_name",
  "upload_date": "20231118",
  "uploader": "Channel Name",
  "duration_sec": 512.23,
  "view_count": 1000000,
  "audio_metadata": {
    "codec": "opus",
    "sample_rate": 48000,
    "bit_rate": 160000,
    "channels": 2,
    "format": "wav",
    "file_size": 32123442
  },
  "download_timestamp": "2025-11-18 10:30:00"
}
```

## 🛡️ Anti-Ban Strategy

Untuk avoid 403 ban dari YouTube:

### 1. Rate Limiting (IMPLEMENTED)
- Sleep interval: 5-10 seconds random antara downloads
- Download rate limit: 500KB/s
- Sleep after every request

### 2. Browser Cookies (OPTIONAL)
Export cookies dari browser (Chrome/Firefox) dan gunakan:

```bash
python batch_download_channels.py --cookies-file cookies.txt
```

**How to export cookies:**
- Chrome: Use extension "Get cookies.txt LOCALLY"
- Firefox: Use extension "cookies.txt"

### 3. Recommended Settings (FREE SOLUTION)

Sesuai feedback dari lead, gunakan free solution dulu:

```bash
# Lambat tapi aman (recommended untuk avoid ban):
python batch_download_channels.py \
  --sleep-min 8.0 \
  --sleep-max 15.0 \
  --rate-limit 300K

# Medium speed (balance antara speed dan safety):
python batch_download_channels.py \
  --sleep-min 5.0 \
  --sleep-max 10.0 \
  --rate-limit 500K

# Faster (higher risk):
python batch_download_channels.py \
  --sleep-min 3.0 \
  --sleep-max 5.0 \
  --rate-limit 1M
```

### 4. If Still Getting 403

Jika masih dapat 403 error:
1. Increase sleep interval: `--sleep-min 10.0 --sleep-max 20.0`
2. Decrease rate limit: `--rate-limit 200K`
3. Use browser cookies: `--cookies-file cookies.txt`
4. Process in smaller batches: `--max-channels 5`
5. Wait dan retry later (YouTube might have temporary rate limit)

## 🔍 Monitoring Progress

Script akan otomatis:
- Log setiap download dengan status
- Save checkpoint setelah setiap channel: `batch_results_checkpoint.json`
- Print statistics di akhir

Untuk monitor real-time:
```bash
# Watch log output
python batch_download_channels.py 2>&1 | tee download.log

# Check progress file
cat batch_results_checkpoint.json | jq '.[] | {name: .channel_url, success: .successful, failed: .failed}'
```

## 📝 Channel List Format

File: `creative_cc_50_yt_channels.txt`

Format: `channel_name,channel_url`

```
leon,https://www.youtube.com/channel/UCLFgJS-f6UKOJ3Xz0K8Kosg
joeman,https://www.youtube.com/@joeman
...
```

## 🐛 Troubleshooting

### Issue: 403 Forbidden errors

**Solutions:**
1. Increase sleep intervals
2. Decrease rate limit
3. Use browser cookies
4. Process fewer channels at once
5. Wait and retry later

### Issue: No audio file downloaded

**Check:**
1. ffmpeg installed? (`which ffmpeg`)
2. Video has audio?
3. Check error in logs

### Issue: Process interrupted

**Resume:**
```bash
# Find last completed channel number (e.g., channel #15)
python batch_download_channels.py --start-from 15
```

## 🎓 Advanced Usage

### Test dengan 1-2 channels first:

```bash
python batch_download_channels.py \
  --max-channels 2 \
  --max-videos-per-channel 3 \
  --sleep-min 5.0 \
  --sleep-max 8.0
```

### Process specific channel range:

```bash
# Channels 10-20
python batch_download_channels.py \
  --start-from 10 \
  --max-channels 10
```

## 📚 References

- yt-dlp: https://github.com/yt-dlp/yt-dlp
- Rate limiting discussion: https://github.com/yt-dlp/yt-dlp/issues/12561
- Project requirements: notion.md

## 💡 Tips dari Lead

Sesuai feedback dari lead:

1. **FREE solution first** - jangan pakai proxy berbayar dulu
2. **Lambatin download rate** - pakai rate limit yang rendah
3. **Sleep interval yang lama** - antara 5-15 seconds
4. **Monitor** - kalau dapat ban, increase sleep dan decrease rate
5. **Test dulu** - test dengan 1-2 channel sebelum run full batch

## ⚠️ Important Notes

- **Jangan pakai proxy berbayar** sebelum approved oleh manager
- **Start dengan conservative settings** (slow download, long sleep)
- **Monitor logs** untuk 403 errors
- **Adjust settings** based on results
- **Save progress regularly** via checkpoint files

## 🎯 Next Steps

Setelah testing berhasil:
1. Report hasil testing ke team
2. Jika masih dapat ban, adjust settings
3. Jika perlu proxy, tunggu approval manager
4. Scale up ke full 50 channels

---

**Created by:** Development Team
**Last updated:** 2025-11-18
