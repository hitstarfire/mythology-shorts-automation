# Hindi Mythology Shorts Automation (₹0 starter)

This starter creates **one 60-second Hindi mythology Short per scheduled run**, twice daily, using:
- GitHub Actions (scheduled workflow)
- `edge-tts` Hindi neural voice (no API key; availability/rate limits are not guaranteed)
- FFmpeg + Pillow to create an original animated typography background and burn-in captions
- GitHub Actions artifacts for review

## Important limitations
- This first zero-cost version uses a curated bank of original Hindi scripts in `scripts/topics.json`; it does not invent fresh AI scripts each run.
- It creates stylized text-based visuals, not AI-generated mythological character images.
- No music is added, avoiding music copyright risk.
- It does **not** publish to YouTube. You review and upload manually.
- GitHub-hosted Actions free usage is subject to GitHub limits and may change. Scheduled runs can be delayed or disabled by GitHub in some circumstances.
- `edge-tts` is an unofficial client to an online TTS service; service availability and terms can change. Do not use it for sensitive text.

## Schedule
The workflow runs at 07:00 and 14:00 India time (01:30 and 08:30 UTC). Each run generates one Short. You can also start a run manually from the Actions tab.

## Install on GitHub using Android
1. Open your repository in Chrome with **Desktop site** enabled.
2. Upload the files/folders from this ZIP into the repository, keeping the folder structure.
3. Commit the files to the `main` branch.
4. Open **Actions**. If prompted, enable workflows.
5. Select **Build Hindi Mythology Short** and tap **Run workflow**.
6. Open the completed run and download the `short-for-review` artifact.
7. Review the MP4 before uploading it to YouTube.

## Add more scripts
Edit `scripts/topics.json`. Add objects with:
- `title`: short Hindi title
- `hook`: opening line
- `narration`: complete original Hindi narration (aim for 110–130 words for ~60 seconds)
- `visual_label`: short text for the visual card

Do not present invented dialogue or disputed details as scripture. Keep creative retellings clearly framed as कथा/कल्पना.

## Files
- `.github/workflows/build-shorts.yml`: twice-daily schedule and build job
- `requirements.txt`: Python dependencies
- `src/build_short.py`: TTS, original background artwork, captions, MP4 render
- `scripts/topics.json`: rotating script bank
