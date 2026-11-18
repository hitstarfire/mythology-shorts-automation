import asyncio
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import edge_tts
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
VOICE = "hi-IN-MadhurNeural"  # Hindi male neural voice
TARGET_SECONDS = 60
W, H = 1080, 1920

def run(cmd):
    subprocess.run(cmd, check=True)

def font_path():
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDevanagariUI-Regular.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return p
    result = subprocess.check_output(["fc-match", "-f", "%{file}", "Noto Sans Devanagari"], text=True).strip()
    if not result or not Path(result).exists():
        raise RuntimeError("Hindi font Noto Sans Devanagari was not found.")
    return result

def wrap_text(text, font, draw, max_width):
    words = text.split()
    lines, line = [], ""
    for word in words:
        trial = (line + " " + word).strip()
        if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

def create_art(title, hook, label, path):
    img = Image.new("RGB", (W, H))
    px = img.load()
    top = (12, 18, 48)
    bottom = (86, 24, 70)
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(top[i] * (1-t) + bottom[i] * t) for i in range(3))
        for x in range(W):
            px[x, y] = c
    d = ImageDraw.Draw(img, "RGBA")
    # Original decorative geometry; no third-party artwork.
    d.ellipse((90, 250, 990, 1150), outline=(255, 190, 90, 90), width=8)
    d.ellipse((160, 320, 920, 1080), outline=(255, 220, 160, 55), width=4)
    for i in range(12):
        x = 120 + i * 76
        d.ellipse((x, 1420 + (i % 2) * 28, x + 8, 1428 + (i % 2) * 28), fill=(255, 210, 130, 150))
    fp = font_path()
    title_font = ImageFont.truetype(fp, 82)
    hook_font = ImageFont.truetype(fp, 54)
    label_font = ImageFont.truetype(fp, 38)
    small_font = ImageFont.truetype(fp, 30)

    d.rounded_rectangle((70, 100, 1010, 250), radius=42, fill=(255, 190, 90, 28), outline=(255, 210, 130, 150), width=3)
    d.text((W//2, 172), "भारतीय पौराणिक कथाएँ", font=label_font, fill=(255, 224, 170), anchor="mm")

    title_lines = wrap_text(title, title_font, d, 880)
    y = 570 - (len(title_lines) * 105)//2
    for line in title_lines:
        d.text((W//2, y), line, font=title_font, fill=(255, 225, 160), anchor="mm", stroke_width=2, stroke_fill=(60, 20, 40))
        y += 112

    d.rounded_rectangle((85, 1170, 995, 1510), radius=45, fill=(5, 10, 30, 150), outline=(255, 210, 140, 110), width=3)
    hook_lines = wrap_text(hook, hook_font, d, 800)
    y = 1240 + max(0, (220 - len(hook_lines)*72)//2)
    for line in hook_lines:
        d.text((W//2, y), line, font=hook_font, fill=(255, 255, 245), anchor="mm")
        y += 76

    d.text((W//2, 1650), label, font=label_font, fill=(255, 215, 145), anchor="mm")
    d.text((W//2, 1780), "कथा • ज्ञान • प्रेरणा", font=small_font, fill=(240, 220, 210), anchor="mm")
    img.save(path, quality=95)

def split_caption(text, count=9):
    words = text.split()
    if not words:
        return []
    # Divide narration into similarly sized caption chunks.
    chunks, current = [], []
    target = max(1, len(words) // count)
    for word in words:
        current.append(word)
        if len(current) >= target and len(chunks) < count - 1:
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    return chunks

def srt_time(seconds):
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def main():
    topics = json.loads((ROOT / "scripts/topics.json").read_text(encoding="utf-8"))
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    slot = 0 if now.hour < 11 else 1
    day_index = now.timetuple().tm_yday - 1
    idx = (day_index * 2 + slot) % len(topics)
    item = topics[idx]

    narration = item["narration"].strip()
    audio = OUT / "narration.mp3"
    background = OUT / "background.png"
    captions = OUT / "captions.srt"
    video = OUT / "mythology-short.mp4"

    async def make_voice():
        communicate = edge_tts.Communicate(narration, VOICE, rate="+0%", volume="+0%")
        await communicate.save(str(audio))
    asyncio.run(make_voice())

    # Get actual speech duration for caption timing.
    probe = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(audio)
    ], text=True).strip()
    speech_seconds = float(probe)
    chunks = split_caption(narration, 9)
    # Keep captions within the speech; leave a little breathing room.
    usable = max(1.0, min(speech_seconds, 57.0))
    with captions.open("w", encoding="utf-8") as f:
        for n, chunk in enumerate(chunks, start=1):
            start = (n - 1) * usable / len(chunks)
            end = n * usable / len(chunks)
            f.write(f"{n}\n{srt_time(start)} --> {srt_time(end)}\n{chunk}\n\n")

    create_art(item["title"], item["hook"], item["visual_label"], background)

    # Use an original typography background with a subtle slow zoom.
    vf = (
        "scale=1080:1920,"
        "zoompan=z='min(zoom+0.00012,1.07)':d=1800:s=1080x1920:fps=30,"
        "subtitles=output/captions.srt:force_style='FontName=Noto Sans Devanagari,FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00101020,BorderStyle=1,Outline=2,Shadow=1,Alignment=2,MarginV=230'"
    )
    run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(background), "-i", str(audio),
        "-vf", vf, "-af", "apad=pad_dur=60,afade=t=out:st=57:d=3",
        "-t", str(TARGET_SECONDS), "-r", "30", "-c:v", "libx264",
        "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac",
        "-b:a", "128k", "-shortest", str(video)
    ])

    metadata = {
        "title": item["title"] + " | Hindi Mythology #shorts",
        "description": item["hook"] + "\n\nयह एक मौलिक, संक्षिप्त कथात्मक प्रस्तुति है। संदर्भ के लिए मूल ग्रंथों का अध्ययन करें।\n#shorts #hindikahani #mythology #sanatandharma",
        "script_title": item["title"],
        "generated_at_ist": now.isoformat(),
        "voice": VOICE,
        "duration_seconds": TARGET_SECONDS,
        "review_required": True
    }
    (OUT / "review.txt").write_text(
        "REVIEW BEFORE PUBLISHING\n\n"
        f"Title: {metadata['title']}\n\n"
        f"Description:\n{metadata['description']}\n\n"
        "Check pronunciation, story accuracy, captions and visual quality before upload.\n",
        encoding="utf-8"
    )
    (OUT / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Built {video} using script index {idx}: {item['title']}")

if __name__ == "__main__":
    main()
