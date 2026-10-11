#!/usr/bin/env python3
"""Drive cloud renders from any session (stdlib only).
  python3 reelkit/cloud.py render <episode_dir> [more...] [--tag T] [--wait] [--download DIR]
  python3 reelkit/cloud.py status            last 5 render runs
  python3 reelkit/cloud.py fetch <tag> [DIR] download a release's final.mp4/cover.jpg/qa.json
Pushes must be done first (tools/sync.sh) — the runner renders what is on origin/main."""
import argparse, json, sys, time, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from media import req, repo_slug, API, assets_of, get_release

def runs(slug, n=5):
    r = req("GET", f"{API}/repos/{slug}/actions/workflows/render.yml/runs?per_page={n}") or {"workflow_runs": []}
    return r["workflow_runs"]

def render(a):
    slug = repo_slug(); before = {r["id"] for r in runs(slug, 10)}
    eps = " ".join(a.episodes)
    req("POST", f"{API}/repos/{slug}/actions/workflows/render.yml/dispatches",
        {"ref": "main", "inputs": {"episodes": eps, "tag": a.tag or "", "crf": str(a.crf)}})
    run = None
    for _ in range(30):
        time.sleep(4)
        new = [r for r in runs(slug, 10) if r["id"] not in before]
        if new: run = new[0]; break
    if not run: sys.exit("dispatched, but no run appeared yet — check Actions tab")
    print(f"run #{run['run_number']}  {run['html_url']}")
    if not a.wait: return
    t0 = time.time()
    while run["status"] != "completed":
        time.sleep(30)
        run = req("GET", f"{API}/repos/{slug}/actions/runs/{run['id']}")
        jobs = req("GET", f"{API}/repos/{slug}/actions/runs/{run['id']}/jobs")["jobs"]
        steps = [f"{j['name']}: " + next((s['name'] for s in j.get('steps', []) if s['status'] == 'in_progress'), j['status']) for j in jobs]
        print(f"  {int(time.time()-t0)//60:>3}m  {run['status']:<11} " + " | ".join(steps)[:200], flush=True)
    print(f"conclusion: {run['conclusion']}  ({int(time.time()-t0)//60} min)")
    if run["conclusion"] == "success" and a.download:
        for ep in a.episodes:
            tag = a.tag or f"{Path(ep).name}-r{run['run_number']}"
            fetch_tag(slug, tag, Path(a.download) / Path(ep).name)
    sys.exit(0 if run["conclusion"] == "success" else 1)

def fetch_tag(slug, tag, out):
    rel = get_release(slug, tag, create=False)
    if not rel: sys.exit(f"no release {tag}")
    out.mkdir(parents=True, exist_ok=True)
    for name, asset in assets_of(slug, rel).items():
        data = req("GET", asset["url"], headers={"Accept": "application/octet-stream"}, raw=True)
        (out / name).write_bytes(data); print(f"  ↓ {out / name} ({len(data)/1e6:.1f} MB)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("render"); p.add_argument("episodes", nargs="+"); p.add_argument("--tag"); p.add_argument("--crf", default=18)
    p.add_argument("--wait", action="store_true"); p.add_argument("--download")
    sp.add_parser("status")
    p = sp.add_parser("fetch"); p.add_argument("tag"); p.add_argument("dir", nargs="?", default=".")
    a = ap.parse_args()
    if a.cmd == "render": render(a)
    elif a.cmd == "status":
        for r in runs(repo_slug()): print(f"#{r['run_number']} {r['status']:<10} {r['conclusion'] or '':<9} {r['created_at']} {r['display_title']} {r['html_url']}")
    else: fetch_tag(repo_slug(), a.tag, Path(a.dir))
