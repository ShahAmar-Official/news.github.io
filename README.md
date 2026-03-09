# 📰 News Shorts Automation

<p align="center">
  <a href="https://github.com/ShahAmar-Official/news.github.io/actions/workflows/automation.yml">
    <img src="https://github.com/ShahAmar-Official/news.github.io/actions/workflows/automation.yml/badge.svg" alt="Pipeline Status">
  </a>
  <a href="https://github.com/ShahAmar-Official/news.github.io/actions/workflows/pages.yml">
    <img src="https://github.com/ShahAmar-Official/news.github.io/actions/workflows/pages.yml/badge.svg" alt="Pages Deploy">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT">
  </a>
  <img src="https://img.shields.io/badge/cost-$0.00%2Fvideo-brightgreen" alt="Cost: $0.00/video">
  <img src="https://img.shields.io/badge/python-3.11-blue" alt="Python 3.11">
</p>

<p align="center">
  A fully automated, end-to-end <strong>Breaking News Shorts</strong> creation and upload toolkit
  that runs 24/7 via <strong>GitHub Actions</strong> — no server required, <strong>100% free</strong>.
</p>

> **$0.00 per video** — Uses NewsAPI for breaking headlines, Microsoft Edge neural TTS,
> news-anchor style scripts, free Pexels stock footage, and GitHub Actions free tier.

---

## ✨ Features

- 🔍 **Breaking News Detection** — Automatically discovers top stories from NewsAPI (primary), Google News RSS, Google Trends (US), and Hacker News
- ✍️ **News Anchor Script Generation** — Produces professional news-anchor hooks, factual narration, and CTAs via a smart template engine (no paid AI API needed)
- 🎙️ **Neural Text-to-Speech** — High-quality newscast voice narration using Microsoft Edge TTS (newscast-style voices prioritised) with gTTS fallback
- 🎬 **Automated Video Production** — Assembles portrait (1080 × 1920) videos with Pexels news-relevant stock footage, animated captions, and crossfade transitions
- 🖼️ **News Thumbnail Generation** — Professional breaking-news style thumbnails with BREAKING NEWS banner, dark blue/red palette created with Pillow
- 🚀 **YouTube Upload** — Resumable upload with auto-attached thumbnail and news-optimised metadata (category: News & Politics) via YouTube Data API v3
- 🌐 **Setup Wizard** — GitHub Pages site for one-click OAuth2 configuration and channel linking

---

## 🏗️ Architecture

```
GitHub Actions (cron: every hour)
        │
        ▼
src/pipeline.py  ──────────────────────────────────────────────┐
        │                                                       │
        ├─► src/news_sources.py  (NewsAPI + Google News RSS    │
        │         │               + Google Trends + HN)        │
        │         │ top news story                              │
        ├─► src/scriptwriter.py  (News-anchor template engine) │
        │         │ title, script, scenes, tags, description    │
        ├─► src/tts.py           (Edge TTS / gTTS — free)      │
        │         │ audio MP3 + duration                        │
        ├─► src/video_creator.py (Pexels API + MoviePy)        │
        │         │ 1080×1920 MP4                               │
        ├─► src/thumbnail.py     (Pillow — news channel style)  │
        │         │ 1280×720 JPEG                               │
        └─► src/uploader.py      (YouTube Data API v3)          │
                  │ video ID + URL                              │
                  └───────────────────────────────────────────►─┘
```

---

## 🚀 Quick Start

### 1. Fork this Repository

Click **Fork** at the top right of this page.

### 2. Set Up YouTube OAuth2 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project and enable the **YouTube Data API v3**
3. Create **OAuth 2.0 Client ID** credentials (Desktop app)
4. Download the client secret JSON
5. Run the one-time OAuth flow locally to generate a token JSON:

```bash
pip install google-auth-oauthlib
python - <<'EOF'
from google_auth_oauthlib.flow import InstalledAppFlow
flow = InstalledAppFlow.from_client_secrets_file(
    "client_secret.json",
    scopes=["https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.force-ssl"]
)
creds = flow.run_local_server(port=0)
import json
print(json.dumps({
    "access_token": creds.token,
    "refresh_token": creds.refresh_token,
    "token_uri": creds.token_uri,
}))
EOF
```

### 3. Get a Pexels API Key

Sign up at [pexels.com/api](https://www.pexels.com/api/) (free tier available).

### 4. Get a NewsAPI Key

Sign up at [newsapi.org](https://newsapi.org/) (free developer tier available).
This is the **primary news source** for the channel.

### 5. Add Secrets to GitHub

In your forked repository go to **Settings → Secrets and variables → Actions**
and add the following secrets:

| Secret name              | Value                                           | Required? |
|--------------------------|-------------------------------------------------|-----------|
| `YOUTUBE_CLIENT_SECRET`  | Full JSON string of the OAuth2 client secret    | ✅ Yes    |
| `YOUTUBE_TOKEN`          | JSON string with `access_token`, `refresh_token`| ✅ Yes    |
| `PEXELS_API_KEY`         | Your Pexels API key (free)                      | ✅ Yes    |
| `NEWSAPI_KEY`            | Your NewsAPI.org API key                        | ✅ Yes    |

> **Note:** `NEWSAPI_KEY` is **required** for this news channel — it is the
> primary source of breaking news stories. The channel will fall back to
> Google News RSS and other free sources if absent, but full functionality
> requires a valid NewsAPI key.

### 6. Enable GitHub Actions

Go to the **Actions** tab in your repository and click **"I understand my
workflows, go ahead and enable them"** if prompted.

The workflow will run automatically every hour, or you can trigger it
manually via **Actions → News Shorts Automation → Run workflow**.

---

## 📖 How it Works

| Step | Module | Description |
|------|--------|-------------|
| 1 | `src/news_sources.py` | Fetches breaking headlines from NewsAPI (primary — multiple categories), Google News RSS (free, no key), Google Trends (US), and Hacker News. Scores stories with 3x weight on NewsAPI and Google News RSS results. |
| 2 | `src/scriptwriter.py` | Generates professional news-anchor scripts using a template engine with breaking-news hooks, factual body templates, news CTA variations, scene descriptions, tags, and descriptions. Fully deterministic — no paid API key needed. |
| 3 | `src/tts.py` | Converts the narration to an MP3 file using Microsoft Edge's free neural TTS (newscast-style voices prioritised) with gTTS as fallback. |
| 4 | `src/video_creator.py` | Queries Pexels for portrait video clips per scene, assembles them with MoviePy, adds animated captions, overlays audio, and exports to MP4. |
| 5 | `src/thumbnail.py` | Creates a news-channel style 1280 × 720 JPEG thumbnail with BREAKING NEWS banner, dark blue/red gradient, and a topic emoji using Pillow. |
| 6 | `src/uploader.py` | Uploads the video via the YouTube Data API v3 resumable upload endpoint (category: News & Politics), then attaches the thumbnail. |

---

## ⚙️ Customisation

Edit `config.py` to change:

| Setting | Default | Description |
|---------|---------|-------------|
| `NEWS_CATEGORIES` | `["general", "business", "technology", "science", "health", "entertainment", "sports"]` | NewsAPI categories to fetch headlines from |
| `VIDEO_FPS` | `30` | Output frame rate |
| `SUBTITLE_FONT_SIZE` | `88` | Caption font size (px) |
| `SUBTITLE_STROKE_WIDTH` | `6` | Caption text outline thickness |
| `SUBTITLE_MAX_WORDS` | `4` | Max words per caption burst |
| `VIDEO_BITRATE` | `16000k` | Video encoding bitrate (higher = better quality) |
| `VIDEO_PRESET` | `slow` | FFmpeg encoding preset (`slow` = higher quality) |
| `AUDIO_BITRATE` | `320k` | Audio encoding bitrate |
| `VIDEO_TRANSITION_DURATION` | `0.35` | Crossfade duration between scenes (seconds) |
| `BG_MUSIC_VOLUME` | `0.08` | Background music volume (0.0 = off). Place an MP3 at the path set by `BG_MUSIC_PATH` to enable. |
| `BG_MUSIC_PATH` | `"assets/bg_music.mp3"` | Path to the background music MP3 file (relative to repo root). |
| `TTS_VOICE` | `"en-US-GuyNeural"` | Microsoft Edge neural voice for TTS (newscast style) |
| `TTS_LANGUAGE` | `"en"` | Fallback gTTS language code (`en`, `es`, `fr`, `de`, `hi`, etc.) |
| `YOUTUBE_CATEGORY_ID` | `"25"` | YouTube category (25 = News & Politics) |
| `PRIVACY_STATUS` | `"public"` | Upload privacy (`public`, `unlisted`, `private`) |
| `MAX_VIDEOS_PER_RUN` | `1` | Videos per pipeline run |

---

## 💰 Cost Breakdown (per video)

| Service | Usage | Cost |
|---------|-------|------|
| Template engine | Script generation | **Free** |
| Edge TTS / gTTS | Voice narration | **Free** |
| Pexels API | Stock footage | **Free** |
| NewsAPI | Breaking headlines | **Free** (developer tier) |
| Google News RSS | Backup headlines | **Free** |
| Google Trends | Trending topics | **Free** |
| Hacker News | Tech news signal | **Free** |
| GitHub Actions | ~10 min / run | **Free** (2,000 min/month included) |
| **Total** | | **$0.00 / video** |

---

## 🤝 Contributing

Contributions are welcome! Please read the [Contributing Guidelines](CONTRIBUTING.md)
and the [Code of Conduct](CODE_OF_CONDUCT.md) before submitting a pull request.

---

## 🛠️ Troubleshooting

### `invalid_scope: Bad Request` / `401 Unauthorized` on upload

**Cause**: The `YOUTUBE_TOKEN` secret is outdated, was issued without the required OAuth scopes, or the refresh token has been revoked.

**Fix**: Regenerate the token by running the OAuth2 flow locally with the correct scopes:

```bash
pip install google-auth-oauthlib
python - <<'EOF'
from google_auth_oauthlib.flow import InstalledAppFlow
import json

flow = InstalledAppFlow.from_client_secrets_file(
    "client_secret.json",
    scopes=[
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.force-ssl",
    ]
)
creds = flow.run_local_server(port=0)
token_json = json.dumps({
    "access_token": creds.token,
    "refresh_token": creds.refresh_token,
    "token_uri": creds.token_uri,
})
print(token_json)
EOF
```

Then update the `YOUTUBE_TOKEN` GitHub Secret with the printed JSON.

> **The `youtube.force-ssl` scope is required** for thumbnail uploads and certain API features.  Tokens generated without it will result in `invalid_scope` errors.

---

### `file_cache is only supported with oauth2client<4.0.0` warning

Informational only — not an error. The pipeline suppresses the discovery cache to avoid this. No action needed.

---

### `Thumbnail failed (HTTP 403)`

Enable **custom thumbnails** on your YouTube channel:
1. Go to [YouTube Studio → Settings → Channel → Feature eligibility](https://studio.youtube.com/)
2. Custom thumbnails require phone number verification on the account.

---

### `NEWSAPI_KEY is not set` warning

This is logged as an error because `NEWSAPI_KEY` is **required** for the news channel. The pipeline will fall back to Google News RSS and Google Trends, but you should set the `NEWSAPI_KEY` secret for full functionality.

---

### Required GitHub Secrets

| Secret | Format | Required? |
|--------|--------|-----------|
| `YOUTUBE_CLIENT_SECRET` | Full OAuth2 client secret JSON (from Google Cloud Console) | ✅ Yes |
| `YOUTUBE_TOKEN` | JSON with `access_token`, `refresh_token`, `token_uri` | ✅ Yes |
| `PEXELS_API_KEY` | Plain API key string | ✅ Yes (for stock footage) |
| `NEWSAPI_KEY` | Plain API key string | ✅ Yes (primary news source) |

---

## ⚠️ Disclaimer

This tool is intended for educational and creative purposes. Ensure your use
of the YouTube API complies with [YouTube's Terms of Service](https://www.youtube.com/t/terms)
and the [YouTube API Services Terms of Service](https://developers.google.com/youtube/terms/api-services-terms-of-service).
You are solely responsible for the content uploaded by this automation.
Always review the content before publishing publicly if possible.

---

## 📄 License

This project is licensed under the **MIT License**.
See [LICENSE](LICENSE) for details.