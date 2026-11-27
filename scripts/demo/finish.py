"""Finish the demo: find the 7 segments in one narration mp3 (the 6 longest pauses), re-record the capture to those
durations, mux, loudnorm, run the pre-flight check. Usage: finish.py NARRATION.mp3 OUTDIR"""
import json, pathlib, re, subprocess, sys
HERE = pathlib.Path(__file__).resolve().parent
mp3, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp3)]))
log = subprocess.run(["ffmpeg", "-i", str(mp3), "-af", "silencedetect=noise=-38dB:d=0.35", "-f", "null", "-"], capture_output=True, text=True).stderr
sil = [(float(a), float(b)) for a, b in zip(re.findall(r"silence_start: ([\d.]+)", log), re.findall(r"silence_end: ([\d.]+)", log))]
sil = [s for s in sil if s[0] > 0.3 and s[1] < total - 0.3]
cuts = sorted(sorted(sil, key=lambda s: s[1] - s[0], reverse=True)[:6])
ids = [s["id"] for s in json.load(open(HERE.parents[1] / "docs" / "DEMO_NARRATION.json"))["segments"]]
edges = [0.0] + [(a + b) / 2 for a, b in cuts] + [total]
dur = {i: round(edges[k + 1] - edges[k], 2) for k, i in enumerate(ids)}
print("segment seconds:", dur, "total", round(total, 1))
(out / "durations.json").write_text(json.dumps(dur))
subprocess.check_call([sys.executable, str(HERE / "record_demo.py"), str(out / "cap"), str(out / "durations.json")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
webm = next((out / "cap").glob("*.webm"))
final = out / "grant-audit-ready-demo.mp4"
subprocess.check_call(["ffmpeg", "-loglevel", "error", "-y", "-i", str(webm), "-i", str(mp3), "-filter_complex", "[1:a]adelay=500|500,loudnorm=I=-16:TP=-1.5:LRA=11[a]",
                       "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "160k", "-shortest", str(final)])
sys.exit(subprocess.call([sys.executable, str(HERE / "check_video.py"), str(final)]))
