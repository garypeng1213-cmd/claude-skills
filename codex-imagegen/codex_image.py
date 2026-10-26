#!/usr/bin/env python3
"""Generate ONE image through Codex's built-in image_gen, keeping Codex to a single tool call.

Codex only calls image_gen. This script does everything else: shrinks the reference images,
finds the generated PNG in ~/.codex/generated_images/<session id>/, copies it to --out and
prints what the run cost. Verifying the picture (Read) and deciding on a retry stay with Claude.

    python3 codex_image.py --out assets/hero.png "prompt..."
    python3 codex_image.py --out out.png --ref scene.jpg --ref dog.jpg --prompt-file prompt.txt
"""
import argparse
import glob
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MAX_REFS = 5          # image_gen rejects more than 5 reference images
MAX_EDGE = "1536"     # longest edge of the copies handed to image_gen
CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
# Rule (Gary, 2026-10-12): no image after 5 minutes -> shut codex down completely and start over.
# Measured on 45 successful runs: median 63 s, slowest 185 s; a hung run never finishes on its own.
TIMEOUT = 300         # seconds one attempt may take
STARTUP = 60          # seconds codex gets to open its session; a hung run never opens one
ATTEMPTS = 3          # first try + 2 restarts, then give up and report

ONLY_GENERATE = (
    "Do nothing else: do not read any skill or instruction files, do not run shell commands, "
    "do not view, copy, move or regenerate the image. Leave the file where the tool saves it. "
    "When the tool returns, reply with the single word DONE and stop."
)


def shrink_refs(refs, workdir):
    paths = []
    for n, ref in enumerate(refs, 1):
        src = Path(ref).expanduser().resolve()
        if not src.is_file():
            sys.exit(f"reference image not found: {ref}")
        dst = workdir / f"{n}{src.suffix.lower() or '.png'}"
        shutil.copy2(src, dst)
        # -Z only ever scales down; a failure just leaves the full-size copy in place.
        subprocess.run(["sips", "-Z", MAX_EDGE, str(dst)], capture_output=True)
        paths.append(str(dst))
    return paths


def descendants(pid):
    found = []
    for child in subprocess.run(["pgrep", "-P", str(pid)], capture_output=True, text=True).stdout.split():
        found += [int(child)] + descendants(int(child))
    return found


def session_opened(workdir, since):
    """True once codex has written a session file for this run (it records our unique workdir as cwd)."""
    for f in glob.glob(str(CODEX_HOME / "sessions/*/*/*/rollout-*.jsonl")):
        try:
            if os.path.getmtime(f) >= since - 2 and workdir.name in open(f, encoding="utf-8", errors="ignore").read(400_000):
                return True
        except OSError:
            pass
    return False


def kill_tree(proc):
    """`codex` is a node wrapper around a native binary. Killing only the wrapper leaves the native
    process alive as an orphan, and they pile up run after run, so take down the whole tree."""
    tree = descendants(proc.pid)
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(proc.pid, sig)
        except (ProcessLookupError, PermissionError):
            pass
        for pid in tree:
            try:
                os.kill(pid, sig)
            except (ProcessLookupError, PermissionError):
                pass
        time.sleep(2)
    proc.wait()


def run_codex(cmd, workdir, timeout, startup):
    """Run codex under two limits. Returns (log, why) where why is None, "startup" or "timeout".

    startup: a healthy run opens its session within a second or two; a hung one never does.
    timeout: the whole attempt, session open or not.
    """
    began = time.time()
    with tempfile.TemporaryFile("w+") as sink:          # a file, not a pipe: nothing to drain while we poll
        # stdin must be closed: `codex exec` waits on an inherited stdin for extra prompt text
        # ("Reading additional input from stdin...") and never opens a session if it stays open.
        proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=sink, stderr=subprocess.STDOUT,
                                text=True, start_new_session=True)
        opened, why = False, None
        while proc.poll() is None:
            time.sleep(2)
            elapsed = time.time() - began
            opened = opened or session_opened(workdir, began)
            if elapsed >= timeout:
                why = "timeout"
            elif not opened and elapsed >= startup:
                why = "startup"
            if why:
                kill_tree(proc)
                break
        sink.seek(0)
        return sink.read(), why


def session_pngs(log):
    match = re.search(r"session id: ([0-9a-f-]{36})", log)
    session_id = match.group(1) if match else None
    pngs = sorted(glob.glob(str(CODEX_HOME / f"generated_images/{session_id}/*.png")),
                  key=os.path.getmtime) if session_id else []
    return session_id, pngs


def session_usage(session_id):
    files = glob.glob(str(CODEX_HOME / f"sessions/*/*/*/rollout-*{session_id}.jsonl"))
    turns, last = 0, None
    for line in open(files[0], encoding="utf-8") if files else []:
        try:
            payload = json.loads(line).get("payload")
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("type") == "token_count" and payload.get("info"):
            turns, last = turns + 1, payload
    if not last:
        return "usage: unavailable"
    used = last["info"]["total_token_usage"]
    limits = last.get("rate_limits") or {}
    return (f"usage: turns={turns} input_tokens={used['input_tokens']} "
            f"cached={used['cached_input_tokens']} output_tokens={used['output_tokens']} "
            f"5h_limit_used={(limits.get('primary') or {}).get('used_percent')}% "
            f"weekly_limit_used={(limits.get('secondary') or {}).get('used_percent')}%")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prompt", nargs="?", help="image prompt (or use --prompt-file)")
    ap.add_argument("--prompt-file", help="read the image prompt from this file")
    ap.add_argument("--out", required=True, help="where to save the PNG")
    ap.add_argument("--ref", action="append", default=[], help=f"reference image, repeatable, max {MAX_REFS}")
    # A normal run takes about a minute; codex occasionally hangs before it even opens a session.
    ap.add_argument("--timeout", type=int, default=TIMEOUT, help="seconds one attempt may take before codex is killed")
    ap.add_argument("--startup", type=int, default=STARTUP, help="seconds codex gets to open a session before it is killed")
    ap.add_argument("--attempts", type=int, default=ATTEMPTS, help="how many times to try before giving up")
    args = ap.parse_args()

    prompt = Path(args.prompt_file).read_text(encoding="utf-8") if args.prompt_file else args.prompt
    if not prompt or not prompt.strip():
        sys.exit("no prompt given")
    if len(args.ref) > MAX_REFS:
        sys.exit(f"{len(args.ref)} reference images given; image_gen accepts at most {MAX_REFS}")
    out = Path(args.out).expanduser().resolve()
    if not out.parent.is_dir():
        sys.exit(f"output folder does not exist: {out.parent}")

    workdir = Path(tempfile.mkdtemp(prefix="codex-image-"))
    try:
        refs = shrink_refs(args.ref, workdir)
        how = (f"with referenced_image_paths set to exactly this list in this order: {json.dumps(refs)} "
               "and with the image prompt below" if refs else "with the image prompt below")
        task = (f"Call the built-in image_gen tool exactly once, {how}. {ONLY_GENERATE}"
                f"\n\nIMAGE PROMPT:\n{prompt.strip()}")
        cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "read-only",
               "-c", "model_reasoning_effort=low", "-C", str(workdir), task]
        for attempt in range(1, args.attempts + 1):
            log, why = run_codex(cmd, workdir, args.timeout, args.startup)
            session_id, pngs = session_pngs(log)
            # A run killed at the limit may still have saved its image; use it rather than paying twice.
            if pngs or not why:
                break
            if why == "startup":
                print(f"attempt {attempt}/{args.attempts}: no session after {args.startup}s, codex shut down "
                      "(hung at startup: nothing was generated or charged)", flush=True)
            else:
                print(f"attempt {attempt}/{args.attempts}: no image after {args.timeout}s, codex shut down "
                      "(a session was open, so this attempt may have been charged)", flush=True)
        else:
            sys.exit(f"gave up after {args.attempts} attempts; codex looks unavailable, report this instead of looping")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    if not pngs:
        if "usage limit" in log:
            print("codex usage limit reached:", *[l for l in log.splitlines() if "usage limit" in l][:1], sep="\n")
        else:
            print("no image was generated; last lines of the codex log:", *log.splitlines()[-12:], sep="\n")
        if session_id:
            print(session_usage(session_id))
        sys.exit(1)

    shutil.copy2(pngs[-1], out)
    print(f"saved: {out}")
    if len(pngs) > 1:
        print(f"note: codex generated {len(pngs)} images in this run; kept the newest")
    print(session_usage(session_id))


if __name__ == "__main__":
    main()
