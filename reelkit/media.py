#!/usr/bin/env python3
"""reelkit/media.py — keep binaries OUT of git. Media lives in GitHub Release assets; git only holds
a small manifest (media.json) with sha256 + size per file. Release assets don't count toward repo size.

  python3 reelkit/media.py push <dir> [--release TAG] [--include GLOB ...]   upload new/changed files, write <dir>/media.json
  python3 reelkit/media.py pull <dir>                                        download + verify everything in <dir>/media.json
  python3 reelkit/media.py status <dir>                                      what's missing / changed locally
  python3 reelkit/media.py publish <tag> <file>... [--title T] [--notes-file F]   upload deliverables to a release

Auth: $GH_TOKEN / $GITHUB_TOKEN, else ~/.cache/secrets/gh_token. Repo: $GITHUB_REPOSITORY or the git remote.
Stdlib only, so it runs on a bare runner before anything else is installed.
"""
import argparse, fnmatch, hashlib, json, os, re, subprocess, sys, urllib.request, urllib.error
from pathlib import Path

API = "https://api.github.com"
DEFAULT_GLOBS = ["assets/*", "vo/*", "clips/*", "media/**"]   # out/ = deliverables -> `publish`, not the media store
MEDIA_EXT = {".jpg", ".jpeg", ".png", ".webp", ".mp3", ".wav", ".m4a", ".mp4", ".mov", ".webm", ".gif", ".flac", ".ogg", ".onnx", ".tar", ".gz", ".zip"}


def token(required=True):
    t = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not t:
        p = Path.home() / ".cache/secrets/gh_token"
        t = p.read_text().strip() if p.exists() else None
    if not t and required: sys.exit("no GitHub token: set GH_TOKEN or put it in ~/.cache/secrets/gh_token")
    return t


def repo_slug():
    if os.environ.get("GITHUB_REPOSITORY"): return os.environ["GITHUB_REPOSITORY"]
    url = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True).stdout.strip()
    m = re.search(r"github\.com[:/](.+?)(?:\.git)?$", url)
    if m: return m.group(1)
    slug = (Path(__file__).resolve().parents[1] / ".repo").read_text().strip() if (Path(__file__).resolve().parents[1] / ".repo").exists() else ""
    return slug or sys.exit("cannot determine repo (no origin remote, no .repo file)")


def req(method, url, data=None, headers=None, raw=False):
    tk = token(required=method != "GET")          # public repo: reads work without a token (60 req/h)
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", **({"Authorization": f"Bearer {tk}"} if tk else {})}
    h.update(headers or {})
    body = json.dumps(data).encode() if isinstance(data, (dict, list)) else data
    r = urllib.request.Request(url, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=600) as resp:
            out = resp.read()
            return out if raw else (json.loads(out) if out else {})
    except urllib.error.HTTPError as e:
        if e.code == 404: return None
        sys.exit(f"GitHub API {method} {url} -> {e.code}: {e.read()[:400]!r}")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def flat(rel):            # release asset names are flat
    return rel.replace("/", "__")


def get_release(slug, tag, create=True, title=None, notes=""):
    r = req("GET", f"{API}/repos/{slug}/releases/tags/{tag}")
    if r or not create: return r
    return req("POST", f"{API}/repos/{slug}/releases",
               {"tag_name": tag, "name": title or tag, "body": notes or f"Media store: {tag} (managed by reelkit/media.py)", "prerelease": tag.startswith("media-")})


def assets_of(slug, rel):
    out, page = {}, 1
    while True:
        a = req("GET", f"{API}/repos/{slug}/releases/{rel['id']}/assets?per_page=100&page={page}")
        if not a: break
        out.update({x["name"]: x for x in a}); page += 1
        if len(a) < 100: break
    return out


def upload(slug, rel, path, name, existing):
    if name in existing: req("DELETE", f"{API}/repos/{slug}/releases/assets/{existing[name]['id']}")
    url = rel["upload_url"].split("{")[0] + "?name=" + urllib.request.quote(name)
    with open(path, "rb") as f: data = f.read()
    req("POST", url, data, headers={"Content-Type": "application/octet-stream"})


def collect(d, globs):
    files = []
    for p in sorted(d.rglob("*")):
        if not p.is_file() or p.name == "media.json": continue
        rel = p.relative_to(d).as_posix()
        if rel.startswith(("out/", ".")) or "/__pycache__/" in rel: continue
        if any(fnmatch.fnmatch(rel, g) for g in globs) or (p.suffix.lower() in MEDIA_EXT and not rel.startswith(".")):
            files.append(rel)
    return files


def cmd_push(a):
    d = Path(a.dir).resolve(); slug = repo_slug()
    man_p = d / "media.json"
    man = json.loads(man_p.read_text()) if man_p.exists() else {}
    tag = a.release or man.get("release") or "media-" + re.sub(r"[^a-z0-9]+", "-", d.name.lower()).strip("-")
    rel = get_release(slug, tag); existing = assets_of(slug, rel)
    files = collect(d, a.include or DEFAULT_GLOBS); new = {}
    for f in files:
        h, sz = sha256(d / f), (d / f).stat().st_size
        old = man.get("files", {}).get(f)
        if old and old["sha256"] == h and flat(f) in existing:
            new[f] = old; continue
        print(f"  ↑ {f} ({sz/1e6:.2f} MB)"); upload(slug, rel, d / f, flat(f), existing)
        # keep provenance (kind/licence/credit/source/…) across re-uploads; provenance.py re-verifies it
        new[f] = {**{k: v for k, v in (old or {}).items() if k not in ("sha256", "size")}, "sha256": h, "size": sz}
    # top-level extras (e.g. "generated": build-time assets) survive a push
    man = {**{k: v for k, v in man.items() if k not in ("release", "repo", "files")}, "release": tag, "repo": slug, "files": new}
    man_p.write_text(json.dumps(man, indent=1, sort_keys=True) + "\n")
    print(f"media.json: {len(new)} files, {sum(v['size'] for v in new.values())/1e6:.1f} MB in release '{tag}'")


def cmd_pull(a):
    d = Path(a.dir).resolve(); man = json.loads((d / "media.json").read_text()); slug = man.get("repo") or repo_slug()
    rel = get_release(slug, man["release"], create=False)
    if not rel: sys.exit(f"release {man['release']} not found")
    existing = assets_of(slug, rel); n = 0
    for f, meta in man["files"].items():
        p = d / f
        if p.exists() and p.stat().st_size == meta["size"] and sha256(p) == meta["sha256"]: continue
        asset = existing.get(flat(f))
        if not asset: sys.exit(f"missing asset {flat(f)} in release {man['release']}")
        p.parent.mkdir(parents=True, exist_ok=True)
        data = req("GET", asset["url"], headers={"Accept": "application/octet-stream"}, raw=True)
        p.write_bytes(data)
        if sha256(p) != meta["sha256"]: sys.exit(f"checksum mismatch: {f}")
        n += 1; print(f"  ↓ {f}")
    print(f"pulled {n} file(s); {len(man['files'])} verified in {d}")


def cmd_status(a):
    d = Path(a.dir).resolve(); man = json.loads((d / "media.json").read_text())
    for f, meta in man["files"].items():
        p = d / f
        st = "missing" if not p.exists() else ("ok" if sha256(p) == meta["sha256"] else "CHANGED")
        if st != "ok": print(f"{st:8s} {f}")
    extra = set(collect(d, DEFAULT_GLOBS)) - set(man["files"])
    for f in sorted(extra): print(f"untracked {f}")
    print(f"{len(man['files'])} files tracked in release {man.get('release')} — status checked")


def cmd_publish(a):
    slug = repo_slug(); notes = Path(a.notes_file).read_text() if a.notes_file else ""
    rel = get_release(slug, a.tag, title=a.title, notes=notes); existing = assets_of(slug, rel)
    if notes: req("PATCH", f"{API}/repos/{slug}/releases/{rel['id']}", {"body": notes[:120000], "name": a.title or a.tag})
    for f in a.files:
        print(f"  ↑ {Path(f).name}"); upload(slug, rel, f, Path(f).name, existing)
    print(f"published to {rel['html_url']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("push"); p.add_argument("dir"); p.add_argument("--release"); p.add_argument("--include", nargs="*")
    p = sp.add_parser("pull"); p.add_argument("dir")
    p = sp.add_parser("status"); p.add_argument("dir")
    p = sp.add_parser("publish"); p.add_argument("tag"); p.add_argument("files", nargs="+"); p.add_argument("--title"); p.add_argument("--notes-file")
    a = ap.parse_args(); {"push": cmd_push, "pull": cmd_pull, "status": cmd_status, "publish": cmd_publish}[a.cmd](a)
