"""Mux per-segment narration clips onto the captured screen recording.
Each clip sN.mp3 starts at the scene start logged by record_demo.py (timeline.json) plus LEAD seconds,
so voice and captions line up even when page loads shift the scenes. Then runs the pre-flight check.
Usage: mux.py CAPDIR CLIPDIR OUT.mp4 [LEAD]"""
import json, pathlib, subprocess, sys
HERE = pathlib.Path(__file__).resolve().parent
cap, clips, final = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
lead = float(sys.argv[4]) if len(sys.argv) > 4 else 0.6
tl = json.loads((cap / "timeline.json").read_text())
webm = next(cap.glob("*.webm"))
ids = [k for k in tl if k != "end"]
inputs, chains = ["-i", str(webm)], []
for n, sid in enumerate(ids, start=1):
    inputs += ["-i", str(clips / f"{sid}.mp3")]
    ms = int((tl[sid] + lead) * 1000)
    chains.append(f"[{n}:a]aresample=48000,adelay={ms}|{ms}[a{n}]")
mix = "".join(f"[a{n}]" for n in range(1, len(ids) + 1))
fc = ";".join(chains) + f";{mix}amix=inputs={len(ids)}:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[a]"
end = tl["end"] + 0.3
subprocess.check_call(["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
                       "-t", f"{end:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", "-r", "30",
                       "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(final)])
print("scene starts:", {k: tl[k] for k in ids}, "end", end)
sys.exit(subprocess.call([sys.executable, str(HERE / "check_video.py"), str(final)]))
