"""Pre-flight for the final demo: must have audio, be under 3:00, 1080p. Usage: check_video.py FILE.mp4"""
import json, subprocess, sys
o = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height", "-of", "json", sys.argv[1]]))
dur = float(o["format"]["duration"]); kinds = [s["codec_type"] for s in o["streams"]]
v = next(s for s in o["streams"] if s["codec_type"] == "video")
vol = subprocess.run(["ffmpeg", "-i", sys.argv[1], "-af", "volumedetect", "-vn", "-f", "null", "-"], capture_output=True, text=True).stderr
mean = [l for l in vol.splitlines() if "mean_volume" in l]
ok = dur < 180 and "audio" in kinds and v["height"] >= 1080 and bool(mean) and "-inf" not in mean[0]
print(f"duration {dur:.1f}s, streams {kinds}, {v['width']}x{v['height']}, {mean[0].strip() if mean else 'no audio'} -> {'READY' if ok else 'NOT READY'}")
sys.exit(0 if ok else 1)
