#!/usr/bin/env python3
"""Builds the animated SVGs for the profile README.

PROFILE_DATA=dummy (default)  -> polished sample numbers, no network needed
PROFILE_DATA=live             -> real numbers from the GitHub API (needs GITHUB_TOKEN for contributions)

Fonts (Poppins + DejaVu Sans Mono, both open licences) are embedded as base64 so the SVGs render the same inside a README <img>."""
import os, json, math, random, html, base64, datetime, urllib.request, pathlib

USER = os.environ.get("GH_USER", "sidali-kh")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
MODE = os.environ.get("PROFILE_DATA", "dummy").strip().lower()
ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT.parent / "assets"
OUT.mkdir(exist_ok=True)

SANS = "'PF Sans',Poppins,'Segoe UI',system-ui,-apple-system,Arial,sans-serif"
MONO = "'PF Mono','DejaVu Sans Mono',Consolas,'Liberation Mono',Menlo,monospace"
MONO_W = 0.602  # advance width of the mono face, in em
esc = html.escape
num = lambda v: "–" if v is None else f"{v:,}"

def _face(fam, file, weight):
    b = base64.b64encode((ROOT / "fonts" / file).read_bytes()).decode()
    return f"@font-face{{font-family:'{fam}';font-weight:{weight};src:url(data:font/woff;base64,{b}) format('woff')}}"
FONTS_FULL = (_face("PF Sans", "Poppins-Medium.woff", "400 600") + _face("PF Sans", "Poppins-Bold.woff", "700 900")
              + _face("PF Mono", "Mono-Regular.woff", "400 600") + _face("PF Mono", "Mono-Bold.woff", "700 900"))
FONTS_LINK = _face("PF Sans", "Poppins-Bold-links.woff", "700 900")

# ------------------------------------------------------------------ data
def api(url, body=None):
    h = {"User-Agent": "profile-builder", "Accept": "application/vnd.github+json"}
    if TOKEN: h["Authorization"] = f"Bearer {TOKEN}"
    data = json.dumps(body).encode() if body else None
    if body: h["Content-Type"] = "application/json"
    with urllib.request.urlopen(urllib.request.Request(url, data, h), timeout=20) as r:
        return json.load(r)

S = dict(repos=None, stars=None, followers=None, commits=None, prs=None, issues=None, contrib=None)
langs, toprepos, weeks = [], [], []
live = False

def dummy_weeks():
    rnd = random.Random(2026)
    today = datetime.date.today()
    start = today - datetime.timedelta(days=364)
    start -= datetime.timedelta(days=(start.weekday() + 1) % 7)  # back to a Sunday
    wt = [.45, 1.1, 1.25, 1.25, 1.1, .8, .55]                     # Sun..Sat intensity
    ap = [.30, .75, .85, .85, .75, .55, .35]                      # Sun..Sat chance of any activity
    out, d, w = [], start, 0
    while d <= today:
        wk = []
        sprint = 1.3 + 1.4 * math.sin(w / 5.0) ** 2 + (1.2 if 20 <= w <= 28 else 0)
        for i in range(7):
            if d <= today:
                c = max(1, int(rnd.gauss(sprint * wt[i] * 1.6, 2))) if rnd.random() < ap[i] else 0
                if (today - d).days < 11: c = max(c, 1 + rnd.randint(0, 4))   # a live-looking current streak
                wk.append((d.isoformat(), c))
            d += datetime.timedelta(days=1)
        out.append(wk); w += 1
    return out

if MODE == "dummy":
    weeks = dummy_weeks()
    langs = [("JavaScript", 31), ("PHP", 25), ("Python", 19), ("Jupyter Notebook", 13), ("Java", 12)]
    toprepos = [dict(name="ecg-cardio-classifier", language="Jupyter Notebook", stargazers_count=14, description="ECG image classification, deep learning"),
                dict(name="listings-platform", language="JavaScript", stargazers_count=11, description="Next.js + headless WordPress listings"),
                dict(name="Bookstand", language="PHP", stargazers_count=7, description="Online bookstore in PHP and MySQL")]
    S.update(repos=24, stars=42, followers=58, prs=41, issues=17)
    S["contrib"] = sum(c for w in weeks for _, c in w)
    S["commits"] = int(S["contrib"] * .78)
    live = True  # show streak numbers
else:
    try:
        u = api(f"https://api.github.com/users/{USER}")
        S["repos"], S["followers"] = u["public_repos"], u["followers"]
        repos = [r for r in api(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner")]
        S["stars"] = sum(r["stargazers_count"] for r in repos)
        own = [r for r in repos if not r["fork"]]
        acc = {}
        for r in own:
            if r["language"]: acc[r["language"]] = acc.get(r["language"], 0) + max(r["size"], 1)
        tot = sum(acc.values()) or 1
        langs = sorted(((k, v / tot * 100) for k, v in acc.items()), key=lambda x: -x[1])[:5]
        toprepos = sorted(own, key=lambda r: (r["stargazers_count"], r["pushed_at"]), reverse=True)[:3]
    except Exception as e:
        print("REST fetch failed:", e)
    if TOKEN:
        try:
            q = ('{user(login:"%s"){contributionsCollection{totalCommitContributions totalPullRequestContributions '
                 'totalIssueContributions contributionCalendar{totalContributions weeks{contributionDays{contributionCount date}}}}}}' % USER)
            cc = api("https://api.github.com/graphql", {"query": q})["data"]["user"]["contributionsCollection"]
            S["commits"], S["prs"], S["issues"] = cc["totalCommitContributions"], cc["totalPullRequestContributions"], cc["totalIssueContributions"]
            S["contrib"] = cc["contributionCalendar"]["totalContributions"]
            weeks = [[(d["date"], d["contributionCount"]) for d in w["contributionDays"]] for w in cc["contributionCalendar"]["weeks"]]
            live = True
        except Exception as e:
            print("GraphQL fetch failed:", e)
    if not weeks:
        weeks = dummy_weeks()
    if not langs:
        langs = [("JavaScript", 38), ("PHP", 25), ("Python", 18), ("Java", 11), ("CSS", 8)]

flat = [c for w in weeks for _, c in w]
cur = 0
for c in (flat[:-1] if flat and flat[-1] == 0 else flat)[::-1]:
    if c > 0: cur += 1
    else: break
longest = run = 0
for c in flat:
    run = run + 1 if c > 0 else 0; longest = max(longest, run)
active = sum(1 for c in flat if c > 0)
wk_tot = [0] * 7
for w in weeks:
    for dt, c in w: wk_tot[(datetime.date.fromisoformat(dt).weekday() + 1) % 7] += c
LC = {"JavaScript": "#f1e05a", "TypeScript": "#3178c6", "PHP": "#8892bf", "HTML": "#e34c26", "CSS": "#a78bfa",
      "Python": "#3fa0e0", "Blade": "#f7523f", "Dockerfile": "#4a90b8", "Shell": "#89e051", "Jupyter Notebook": "#DA5B0B",
      "Java": "#b07219", "C": "#9aa0a6", "C++": "#f34b7d", "Vue": "#41b883", "SCSS": "#c6538c"}
LANG_FALLBACK = ["#36bcf7", "#f472b6", "#fbbf24", "#34d399", "#a78bfa"]

# ------------------------------------------------------------------ shared pieces
BASE = """:root{--card:#f7f9fd;--bd:#dde3ee;--tx:#111827;--mu:#5b6578;--chip:#fff;--c0:#e6ebf4;--c1:#d9d0fb;--c2:#a99af2;--c3:#4fc3f7;--c4:#10b981;
--k1:#0a8fd1;--k2:#7c5cf0;--k3:#db2777;--k4:#d97706;--k5:#059669;--k6:#ea580c}
@media (prefers-color-scheme:dark){:root{--card:#131724;--bd:#242b3d;--tx:#eef1f8;--mu:#8d96ab;--chip:#1b2132;--c0:#1a2030;--c1:#3b2a7a;--c2:#5b4fd6;--c3:#22b8f0;--c4:#34d399;
--k1:#36bcf7;--k2:#a78bfa;--k3:#f472b6;--k4:#fbbf24;--k5:#34d399;--k6:#fb923c}}
.card{fill:var(--card);stroke:var(--bd)}.ti{font:700 16px %s;fill:var(--tx)}.sb{font:500 12px %s;fill:var(--mu)}
.bi{}@media (prefers-color-scheme:dark){.bi{filter:brightness(1.7) saturate(1.15)}}
.big{font:700 32px %s;fill:var(--tx)}.mono{font:400 12.5px %s;fill:var(--tx)}""" % (SANS, SANS, SANS, MONO)
THEME, THEME_LINK = FONTS_FULL + BASE, FONTS_LINK + BASE

ICONS = json.load(open(ROOT / "icons.json", encoding="utf-8"))
def _lum(h):
    r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4)); return .2126 * r + .7152 * g + .0722 * b
def brand(slug, x, y, size, fill=None):
    ic = ICONS["brand"][slug]
    f = fill or (f"#{ic['c']}" if .12 < _lum(ic["c"]) < .9 else "var(--tx)")
    cls = ' class="bi"' if not fill and f.startswith("#") else ""
    return f'<path{cls} transform="translate({x} {y}) scale({size/24:.4f})" d="{ic["p"]}" fill="{f}"/>'
def octi(name, x, y, size, fill):
    return f'<g transform="translate({x} {y}) scale({size/16:.4f})" fill="{fill}">{ICONS["octicon"][name]}</g>'
def glyph(kind, x, y, size, c):
    """Tiny line icons for tools that have no brand icon (16x16 box)."""
    d = {"db": '<ellipse cx="8" cy="3.8" rx="5.2" ry="2.3"/><path d="M2.8 3.8v8.4c0 1.3 2.3 2.3 5.2 2.3s5.2-1 5.2-2.3V3.8M2.8 8c0 1.3 2.3 2.3 5.2 2.3s5.2-1 5.2-2.3"/>',
         "chart": '<path d="M2 2v12h12M5 10.5l3-3.2 2.2 2 3.3-4.6"/>',
         "net": '<path d="M3 12.5 8 4l5 8.5H3z"/><circle cx="8" cy="4" r="1.6" fill="currentColor"/><circle cx="3" cy="12.5" r="1.6" fill="currentColor"/><circle cx="13" cy="12.5" r="1.6" fill="currentColor"/>'}[kind]
    return (f'<g transform="translate({x} {y}) scale({size/16:.4f})" fill="none" stroke="{c}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" color="{c}">{d}</g>')
LANGSLUG = {"JavaScript": "javascript", "TypeScript": "typescript", "PHP": "php", "HTML": "html5", "CSS": "css3",
            "Python": "python", "Blade": "laravel", "Dockerfile": "docker", "Shell": "gnubash", "Jupyter Notebook": "jupyter",
            "Java": "openjdk", "C": "c", "C++": "cplusplus", "Vue": "vuedotjs", "SCSS": "sass", "Go": "go", "Rust": "rust",
            "Dart": "dart", "Kotlin": "kotlin", "Swift": "swift"}
def lang_icon(name, x, y, size):
    slug = LANGSLUG.get(name)
    return brand(slug, x, y, size) if slug in ICONS["brand"] else octi("code", x, y, size, "var(--mu)")

def defs():
    g = "".join(f'<radialGradient id="g{i}" cx=".08" cy="0" r="1.1"><stop offset="0" style="stop-color:var(--k{i});stop-opacity:.22"/><stop offset="1" style="stop-color:var(--k{i});stop-opacity:0"/></radialGradient>' for i in range(1, 7))
    return (f'<defs>{g}<linearGradient id="sw" x1="0" x2="1"><stop offset="0" style="stop-color:var(--k1);stop-opacity:0"/><stop offset=".5" style="stop-color:var(--k1);stop-opacity:.45"/><stop offset="1" style="stop-color:var(--k1);stop-opacity:0"/></linearGradient>'
            '<linearGradient id="ng" x1="0" y1="0" x2="1" y2="1"><stop offset="0" style="stop-color:var(--k1)"/><stop offset="1" style="stop-color:var(--k3)"/></linearGradient>'
            '<linearGradient id="fl" x1="0" x2="1"><stop offset="0" style="stop-color:var(--card)"/><stop offset="1" style="stop-color:var(--card);stop-opacity:0"/></linearGradient>'
            '<linearGradient id="fr" x1="0" x2="1"><stop offset="0" style="stop-color:var(--card);stop-opacity:0"/><stop offset="1" style="stop-color:var(--card)"/></linearGradient>'
            '<linearGradient id="ecg" x1="0" x2="1"><stop offset="0" style="stop-color:var(--k3)"/><stop offset="1" style="stop-color:var(--k4)"/></linearGradient>'
            '<linearGradient id="ls" x1="0" x2="1"><stop offset="0" style="stop-color:var(--k2)"/><stop offset="1" style="stop-color:var(--k1)"/></linearGradient>'
            '<linearGradient id="jl" x1="0" x2="1"><stop offset="0" style="stop-color:var(--k1)"/><stop offset=".5" style="stop-color:var(--k2)"/><stop offset="1" style="stop-color:var(--k3)"/></linearGradient></defs>')

def wrap(name, w, h, label, body):
    (OUT / name).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(label)}"><style>{THEME}</style>{defs()}{body}</svg>', encoding="utf-8")

def reveal(inner, delay, rise=14):
    d = delay + .7; k = f"0;{delay/d:.4f};1"
    return (f'<g>{inner}<animate attributeName="opacity" values="0;0;1" keyTimes="{k}" dur="{d:.2f}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" values="0 {rise};0 {rise};0 0" keyTimes="{k}" dur="{d:.2f}s" fill="freeze"/></g>')

def card(x, y, w, h, body, delay, k=1):
    return reveal(f'<g transform="translate({x} {y})"><rect class="card" width="{w}" height="{h}" rx="20"/><rect width="{w}" height="{h}" rx="20" fill="url(#g{k})"/>{body}</g>', delay)

def title(t, k, sub=None):
    s = f'<rect x="24" y="29" width="8" height="8" rx="2.5" fill="var(--k{k})"/><text class="ti" x="40" y="40">{esc(t)}</text>'
    return s + (f'<text class="sb" x="24" y="62">{esc(sub)}</text>' if sub else "")

def pill_w(t): return len(t) * 7.4 + 22
def pill(x, y, t, k):
    w = pill_w(t)
    return (f'<rect x="{x}" y="{y}" width="{w:.0f}" height="26" rx="13" fill="var(--k{k})" fill-opacity=".16" stroke="var(--k{k})" stroke-opacity=".55"/>'
            f'<text x="{x+w/2:.0f}" y="{y+17}" text-anchor="middle" style="font:700 11.5px {MONO};fill:var(--k{k})">{esc(t)}</text>'), w

def pill_flow(items, x0, y0, xmax, gap=8, rowh=32):
    """Place pills left to right, wrapping at xmax. items = [(text, k)]."""
    out, x, y = "", x0, y0
    for t, k in items:
        w = pill_w(t)
        if x + w > xmax: x, y = x0, y + rowh
        p, _ = pill(x, y, t, k); out += p; x += w + gap
    return out

def growbar(x, base, w, hmax, h, fill, delay, rx=6):
    d = delay + .9; k = f"0;{delay/d:.4f};1"
    return (f'<rect x="{x}" y="{base-h:.1f}" width="{w}" height="{h:.1f}" rx="{rx}" fill="{fill}">'
            f'<animate attributeName="height" values="0;0;{h:.1f}" keyTimes="{k}" dur="{d:.2f}s" fill="freeze"/>'
            f'<animate attributeName="y" values="{base};{base};{base-h:.1f}" keyTimes="{k}" dur="{d:.2f}s" fill="freeze"/></rect>')

def typing(roles, x, y, cw, fs, color, cycle=4.6):
    T = cycle * len(roles); out = ""
    for i, r in enumerate(roles):
        n = len(r); s = i / len(roles); wd = 1 / len(roles)
        ts, vs = [0.0], [0]
        for k in range(1, n + 1): ts.append(s + k / n * .4 * wd); vs.append(k)
        for k in range(n - 1, -1, -1): ts.append(s + .8 * wd + (n - k) / n * .2 * wd); vs.append(k)
        if ts[-1] < 1: ts.append(1.0); vs.append(0)
        for j in range(1, len(ts)):
            if ts[j] <= ts[j - 1]: ts[j] = ts[j - 1] + 1e-6
        ts[-1] = 1.0
        kt = ";".join(f"{t:.5f}" for t in ts)
        w = ";".join(f"{v*cw:.1f}" for v in vs); cx = ";".join(f"{x+v*cw:.1f}" for v in vs)
        out += (f'<clipPath id="ty{i}"><rect x="{x}" y="{y-fs-4}" height="{fs+14}" width="0"><animate attributeName="width" calcMode="discrete" keyTimes="{kt}" values="{w}" dur="{T}s" repeatCount="indefinite"/></rect></clipPath>'
                f'<text x="{x}" y="{y}" clip-path="url(#ty{i})" textLength="{n*cw:.1f}" lengthAdjust="spacing" style="font:400 {fs}px {MONO};fill:{color}">{esc(r)}</text>'
                f'<rect y="{y-fs+2}" width="3" height="{fs+2}" rx="1.5" fill="{color}" opacity="0"><animate attributeName="x" calcMode="discrete" keyTimes="{kt}" values="{cx}" dur="{T}s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" calcMode="discrete" keyTimes="0;{max(s,1e-5):.5f};{s+wd:.5f}" values="0;1;0" dur="{T}s" repeatCount="indefinite"/></rect>')
    return out

# ------------------------------------------------------------------ hero (always dark)
def neural_net(x0=690, gap=80, cy=166):
    """Animated feed-forward network: the ML half of the hero."""
    rnd = random.Random(5)
    counts = [4, 6, 6, 3]; sp = 40
    cols = ["#9fe0ff", "#c4b5fd", "#f9a8d4", "#6ee7b7"]
    pos = [[(x0 + L * gap, cy + (i - (n - 1) / 2) * sp) for i in range(n)] for L, n in enumerate(counts)]
    edges = "".join(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="#fff" stroke-opacity=".11"/>'
                    for L in range(3) for a in pos[L] for b in pos[L + 1])
    sig = ""
    for L in range(3):
        for k in range(5):
            a, b = rnd.choice(pos[L]), rnd.choice(pos[L + 1])
            sig += (f'<circle r="3" fill="{cols[L + 1]}"><animateMotion path="M{a[0]} {a[1]} L{b[0]} {b[1]}" dur="{1.5 + rnd.random():.2f}s" begin="{L*.5 + k*.41:.2f}s" repeatCount="indefinite"/>'
                    f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.15;.8;1" dur="{1.5 + rnd.random():.2f}s" begin="{L*.5 + k*.41:.2f}s" repeatCount="indefinite"/></circle>')
    nodes = ""
    for L, layer in enumerate(pos):
        for i, (x, y) in enumerate(layer):
            nodes += (f'<circle cx="{x}" cy="{y:.0f}" r="7" fill="{cols[L]}" fill-opacity=".3" stroke="{cols[L]}" stroke-opacity=".9">'
                      f'<animate attributeName="fill-opacity" values=".25;.95;.25" dur="2.6s" begin="{L*.45 + (i*.17)%.7:.2f}s" repeatCount="indefinite"/></circle>')
    labels = "".join(f'<text x="{x0+L*gap}" y="{cy+135}" text-anchor="middle" style="font:400 10.5px {MONO};fill:#fff;fill-opacity:.45">{t}</text>'
                     for L, t in enumerate(["input", "hidden", "hidden", "output"]))
    return edges + sig + nodes + labels

def hero():
    blobs = ""
    for cx, cy, r, col, op, dur, dx, dy in [(200, 340, 170, "#36bcf7", .55, 15, 160, -50), (620, 30, 180, "#7c5cf0", .55, 19, -140, 60),
                                            (930, 340, 150, "#14b8a6", .45, 17, -120, -60), (430, 360, 120, "#f472b6", .5, 13, 120, -70),
                                            (980, 20, 110, "#fbbf24", .35, 16, -90, 70)]:
        blobs += (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{col}" fill-opacity="{op}"><animateTransform attributeName="transform" type="translate" values="0 0;{dx} {dy};0 0" dur="{dur}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1"/></circle>')
    roles = ["Full-Stack Web Developer", "Machine Learning Enthusiast", "Telecommunications & ICT Engineer"]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 340" width="1000" height="340" role="img" aria-label="Sidali Khelil Cherfi: {esc(' | '.join(roles))}">
<style>{FONTS_FULL}</style>
<defs><clipPath id="cl"><rect width="1000" height="340" rx="26"/></clipPath><filter id="bl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="55"/></filter>
<linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#7fd6ff"/><stop offset=".55" stop-color="#c4b5fd"/><stop offset="1" stop-color="#f9a8d4"/></linearGradient></defs>
<g clip-path="url(#cl)"><rect width="1000" height="340" fill="#0a0d15"/><g filter="url(#bl)">{blobs}</g>
<rect width="1000" height="340" fill="#0a0d15" fill-opacity=".35"/>{neural_net()}</g>
<rect x=".5" y=".5" width="999" height="339" rx="25.5" fill="none" stroke="#fff" stroke-opacity=".12"/>
{reveal(f'<text x="56" y="136" style="font:700 68px {SANS};letter-spacing:-1.5px;fill:#fff">Sidali</text>',.1,18)}
{reveal(f'<text x="56" y="210" style="font:700 68px {SANS};letter-spacing:-1.5px;fill:url(#g)">Khelil Cherfi</text>',.35,18)}
{reveal(typing(roles,58,274,22*MONO_W,22,"#9fe0ff"),.8,0)}
</svg>'''
    (OUT / "hero.svg").write_text(svg, encoding="utf-8")

# ------------------------------------------------------------------ overview
def overview():
    P = []
    # data -> model -> api -> interface
    nodes = [("Data", 62), ("Model", 178), ("API", 294), ("Interface", 410)]
    colors = ["var(--k5)", "var(--k2)", "var(--k1)", "var(--k3)"]
    s = title("From data to interface", 1, "ML models, REST APIs, modern UIs")
    for j in range(3):
        x1, x2 = nodes[j][1] + 22, nodes[j + 1][1] - 22
        s += f'<path id="a{j}" d="M{x1} 128 L{x2} 128" stroke="var(--bd)" stroke-width="2" stroke-dasharray="4 6" fill="none"/>'
        for k, col in enumerate([colors[j], colors[j + 1]]):
            s += f'<circle r="4" fill="{col}"><animateMotion dur="1.9s" begin="{k*.95+j*.4}s" repeatCount="indefinite"><mpath href="#a{j}"/></animateMotion></circle>'
    for i, (t, x) in enumerate(nodes):
        c = colors[i]
        s += (f'<circle cx="{x}" cy="128" r="18" fill="none" stroke="{c}" stroke-opacity=".7"><animate attributeName="r" values="18;30;30" keyTimes="0;.7;1" dur="2.8s" begin="{i*.6}s" repeatCount="indefinite"/><animate attributeName="stroke-opacity" values=".7;0;0" keyTimes="0;.7;1" dur="2.8s" begin="{i*.6}s" repeatCount="indefinite"/></circle>'
              f'<circle cx="{x}" cy="128" r="13" fill="{c}"/><text class="sb" x="{x}" y="178" text-anchor="middle">{t}</text>')
    P.append(card(0, 0, 470, 200, s, .9, 1))
    # open to work
    s = ('<circle cx="34" cy="38" r="5" fill="#22c55e"/><circle cx="34" cy="38" r="5" fill="none" stroke="#22c55e"><animate attributeName="r" values="5;14" dur="2s" repeatCount="indefinite"/><animate attributeName="stroke-opacity" values=".8;0" dur="2s" repeatCount="indefinite"/></circle>'
         '<text class="ti" x="52" y="44">Open to work</text><text class="mono" x="24" y="84">Internship or CDD</text>')
    s += pill_flow([("Full-Stack", 1), ("ML", 2), ("AI", 3)], 24, 98, 240) + pill_flow([("IP networks", 3), ("DevOps", 4)], 24, 132, 240)
    s += '<text class="sb" x="24" y="186">Médéa, Algeria</text>'
    P.append(card(486, 0, 254, 200, s, 1.05, 5))
    # languages spoken
    s = title("Languages I speak", 4)
    for i, (n, lv, pct, k) in enumerate([("Arabic", "Native", 100, 5), ("French", "B1 (TCF)", 50, 3), ("English", "B2 (IELTS)", 66, 1)]):
        y = 80 + i * 38; d = 1.3 + i * .15; kt = f"0;{d/(d+.9):.4f};1"; fw = 196 * pct / 100
        s += (f'<text class="mono" x="24" y="{y}">{n}</text><text class="sb" x="220" y="{y}" text-anchor="end">{lv}</text>'
              f'<rect x="24" y="{y+9}" width="196" height="6" rx="3" fill="var(--c0)"/><rect x="24" y="{y+9}" width="{fw:.0f}" height="6" rx="3" fill="var(--k{k})"><animate attributeName="width" values="0;0;{fw:.0f}" keyTimes="{kt}" dur="{d+.9:.2f}s" fill="freeze"/></rect>')
    P.append(card(756, 0, 244, 200, s, 1.2, 4))
    # statistics strip
    tiles = [("Repositories", S["repos"], 1, "repo"), ("Stars earned", S["stars"], 4, "star"), ("Followers", S["followers"], 3, "people"),
             ("Commits this year", S["commits"], 5, "git-commit"), ("Pull requests", S["prs"], 2, "git-pull-request"), ("Issues", S["issues"], 6, "issue-opened")]
    s = title("Statistics", 1)
    for i, (l, v, k, ic) in enumerate(tiles):
        x = 24 + i * 160; d = 1.5 + i * .1; kt = f"0;{d/(d+.8):.4f};1"
        s += (f'<text x="{x}" y="92" style="font:700 32px {SANS};fill:var(--k{k})">{num(v)}</text>{octi(ic, x, 103, 14, f"var(--k{k})")}<text class="sb" x="{x+20}" y="115">{l}</text>'
              f'<rect x="{x}" y="126" width="100" height="4" rx="2" fill="var(--c0)"/><rect x="{x}" y="126" width="48" height="4" rx="2" fill="var(--k{k})"><animate attributeName="width" values="0;0;48" keyTimes="{kt}" dur="{d+.8:.2f}s" fill="freeze"/></rect>')
    P.append(card(0, 216, 1000, 146, s, 1.4, 2))
    wrap("overview.svg", 1000, 362, "Overview: from data to interface, availability, languages and GitHub statistics", "".join(P))

# ------------------------------------------------------------------ activity
def activity():
    P = []
    win = weeks[-26:]
    mx = max([c for w in win for _, c in w] + [1])
    lvl = lambda c: 0 if c == 0 else min(4, 1 + int(3 * (c - 1) / max(mx - 1, 1) + .0001))
    gx, gy, cs, gp = 24, 78, 13, 4
    cells = ""
    for col, w in enumerate(win):
        for row, (_, c) in enumerate(w):
            d = .9 + col * .04; kt = f"0;{d/(d+.5):.4f};1"
            cells += f'<rect x="{gx+col*(cs+gp)}" y="{gy+row*(cs+gp)}" width="{cs}" height="{cs}" rx="3.5" fill="var(--c{lvl(c)})"><animate attributeName="opacity" values="0;0;1" keyTimes="{kt}" dur="{d+.5:.2f}s" fill="freeze"/></rect>'
    gw = 26 * (cs + gp) - gp; gh = 7 * (cs + gp) - gp
    s = title("Activity", 2, "Contributions over the last 26 weeks")
    s += (f'<clipPath id="gc"><rect x="{gx}" y="{gy}" width="{gw}" height="{gh}"/></clipPath>{cells}'
          f'<g clip-path="url(#gc)"><rect y="{gy}" width="70" height="{gh}" fill="url(#sw)"><animateTransform attributeName="transform" type="translate" values="{gx-70} 0;{gx+gw} 0;{gx+gw} 0" keyTimes="0;.55;1" dur="7s" begin="2.5s" repeatCount="indefinite"/></rect></g>'
          f'<text x="{gx+gw+24}" y="122" style="font:700 30px {SANS};fill:var(--k5)">{num(S["contrib"])}</text><text class="sb" x="{gx+gw+24}" y="144">in the past year</text>')
    lg = "".join(f'<rect x="{gx+gw+24+i*16}" y="168" width="12" height="12" rx="3.5" fill="var(--c{i})"/>' for i in range(5))
    P.append(card(0, 0, 600, 200, s + lg, .3, 2))
    # donut
    s = title("Top languages", 3)
    cx, cy, r, sw = 92, 116, 50, 20; C = 2 * math.pi * r; tot = sum(p for _, p in langs); off = 0; leg = ""
    for i, (n, p) in enumerate(langs):
        col = LC.get(n, LANG_FALLBACK[i % 5]); ln = C * p / tot; d = .7 + i * .15; kt = f"0;{d/(d+.9):.4f};1"
        s += (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-dasharray="{max(ln-2,1):.2f} {C-max(ln-2,1):.2f}" stroke-dashoffset="{-off:.2f}" transform="rotate(-90 {cx} {cy})">'
              f'<animate attributeName="stroke-dasharray" values="0 {C:.2f};0 {C:.2f};{max(ln-2,1):.2f} {C-max(ln-2,1):.2f}" keyTimes="{kt}" dur="{d+.9:.2f}s" fill="freeze"/></circle>')
        off += ln; y = 80 + i * 26
        leg += f'{lang_icon(n, 176, y-13, 16)}<text class="mono" x="200" y="{y}">{esc(n if n != "Jupyter Notebook" else "Jupyter")}</text><text class="sb" x="360" y="{y}" text-anchor="end">{p/tot*100:.0f}%</text>'
    P.append(card(616, 0, 384, 200, s + leg, .45, 3))
    # streak
    s = title("Streak", 4)
    rr = 40; Cc = 2 * math.pi * rr; frac = min(1, cur / max(longest, 1)) if live else .6
    s += (f'<circle cx="84" cy="102" r="{rr}" fill="none" stroke="var(--c0)" stroke-width="9"/>'
          f'<circle cx="84" cy="102" r="{rr}" fill="none" stroke="var(--k4)" stroke-width="9" stroke-linecap="round" transform="rotate(-90 84 102)"><animate attributeName="stroke-dasharray" values="0 {Cc:.1f};0 {Cc:.1f};{Cc*frac:.1f} {Cc:.1f}" keyTimes="0;.2;1" dur="2.2s" fill="freeze"/></circle>'
          f'<text x="84" y="108" text-anchor="middle" style="font:700 24px {SANS};fill:var(--tx)">{num(cur) if live else "–"}</text><text class="sb" x="84" y="124" text-anchor="middle">current</text>'
          f'<text class="sb" x="170" y="82">Longest streak</text><text x="170" y="108" style="font:700 22px {SANS};fill:var(--k4)">{num(longest) if live else "–"}</text>'
          f'<text class="sb" x="170" y="132">Active days</text><text x="170" y="158" style="font:700 22px {SANS};fill:var(--k5)">{num(active) if live else "–"}</text>')
    P.append(card(0, 216, 300, 170, s, .6, 4))
    # weekday rhythm
    s = title("Weekly rhythm", 5); base = 140; mxw = max(wk_tot) or 1
    for i, v in enumerate(wk_tot):
        x = 24 + i * 42; h = max(4, 78 * v / mxw)
        s += growbar(x, base, 28, 78, h, f"var(--k{[1,2,3,4,5,6,1][i]})", .8 + i * .08) + f'<text class="sb" x="{x+14}" y="158" text-anchor="middle">{"SMTWTFS"[i]}</text>'
    P.append(card(316, 216, 330, 170, s, .75, 5))
    # top repositories
    s = title("Top repositories", 6)
    for i, r in enumerate(toprepos):
        y = 72 + i * 34
        n = str(r["stargazers_count"]); sx = 314 - len(n) * 8 - 16
        s += (f'{lang_icon(r["language"], 22, y-13, 16) if r["language"] else octi("repo", 22, y-13, 16, "var(--mu)")}<text class="mono" x="44" y="{y}">{esc(r["name"][:24])}</text>'
              f'{octi("star", sx, y-11, 12, "var(--k4)")}<text class="sb" x="314" y="{y}" text-anchor="end">{n}</text>'
              f'<text class="sb" x="44" y="{y+16}">{esc((r["description"] or "No description yet")[:42])}</text>')
    P.append(card(662, 216, 338, 170, s, .9, 6))
    wrap("activity.svg", 1000, 386, "GitHub activity: heatmap, languages, streak, weekly rhythm and top repositories", "".join(P))

# ------------------------------------------------------------------ work
def work():
    P = []
    # focus areas
    s = title("Focus areas", 1)
    net = lambda x, y, c: (f'<g transform="translate({x} {y})" stroke="{c}" stroke-width="1.8" fill="none" stroke-linecap="round"><path d="M4 18 L12 6 L20 18 M4 18 H20"/>'
                           f'<circle cx="12" cy="6" r="3" fill="{c}"/><circle cx="4" cy="18" r="3" fill="{c}"/><circle cx="20" cy="18" r="3" fill="{c}"/></g>')
    spark = lambda x, y, c: f'<path transform="translate({x} {y})" d="M12 2l2.2 6.8L21 11l-6.8 2.2L12 20l-2.2-6.8L3 11l6.8-2.2zM19 3l.8 2.2L22 6l-2.2.8L19 9l-.8-2.2L16 6l2.2-.8z" fill="{c}"/>'
    areas = [("Full-Stack web", "Next.js, MERN, Laravel", 1), ("Machine learning", "CNN, RNN, ViT", 2), ("DevOps", "Docker, Kubernetes", 5), ("IP networks", "Routing, VLAN, VoIP", 3)]
    for i, (t, sub, k) in enumerate(areas):
        x = 24 + (i % 2) * 222; y = 74 + (i // 2) * 56
        ico = [brand("react", x + 12, y + 11, 24), spark(x + 12, y + 11, "var(--k2)"), brand("kubernetes", x + 12, y + 11, 24), net(x + 12, y + 11, "var(--k3)")][i]
        s += (f'<rect x="{x}" y="{y}" width="210" height="46" rx="14" fill="var(--k{k})" fill-opacity=".14" stroke="var(--k{k})" stroke-opacity=".5"/>{ico}'
              f'<text x="{x+46}" y="{y+20}" style="font:700 12.5px {SANS};fill:var(--tx)">{t}</text><text x="{x+46}" y="{y+36}" style="font:500 11px {SANS};fill:var(--mu)">{sub}</text>')
    P.append(card(0, 0, 490, 200, s, .3, 1))
    # final-year project
    beat = "h22 l5,-6 l5,6 h10 l4,5 l7,-44 l7,56 l5,-17 h10 l6,-9 l6,9 h24"
    s = title("Final-year project", 3, "Cardiovascular disease detection from ECG images")
    s += (f'<path d="M24 124 {beat*4}" pathLength="1000" fill="none" stroke="var(--bd)" stroke-width="3" stroke-linejoin="round"/>'
          f'<path d="M24 124 {beat*4}" pathLength="1000" fill="none" stroke="url(#ecg)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1000" stroke-dashoffset="1000">'
          '<animate attributeName="stroke-dashoffset" values="1000;0;0;-1000" keyTimes="0;.55;.8;1" dur="5s" repeatCount="indefinite"/></path>')
    s += pill_flow([("Deep learning", 5), ("Image classification", 1), ("ECG", 3)], 24, 158, 470)
    P.append(card(506, 0, 494, 200, s, .45, 3))
    # real estate platform
    y2 = 216
    s = title("Real estate platform", 1, "Internship project, containerised with Docker")
    bx, by = 24, 82
    s += (f'<rect x="{bx}" y="{by}" width="200" height="86" rx="10" fill="var(--chip)" stroke="var(--bd)"/>'
          f'<circle cx="{bx+12}" cy="{by+11}" r="3" fill="var(--k3)"/><circle cx="{bx+24}" cy="{by+11}" r="3" fill="var(--k4)"/><circle cx="{bx+36}" cy="{by+11}" r="3" fill="var(--k5)"/>'
          f'<rect x="{bx+50}" y="{by+6}" width="138" height="10" rx="5" fill="var(--c0)"/>')
    for i in range(3):
        tx = bx + 12 + i * 61; d = 1.0 + i * .35; kt = f"0;{d/(d+.6):.4f};1"
        s += (f'<g><rect x="{tx}" y="{by+26}" width="53" height="52" rx="7" fill="var(--k{[1,2,5][i]})" fill-opacity=".18"/><rect x="{tx+6}" y="{by+56}" width="30" height="5" rx="2.5" fill="var(--k{[1,2,5][i]})" fill-opacity=".7"/>'
              f'<rect x="{tx+6}" y="{by+66}" width="20" height="4" rx="2" fill="var(--mu)" fill-opacity=".5"/><animate attributeName="opacity" values="0;0;1" keyTimes="{kt}" dur="{d+.6:.2f}s" fill="freeze"/></g>')
    s += pill_flow([("Next.js", 1), ("Headless WP", 2), ("MySQL", 3), ("Redis", 6), ("Docker", 5)], 246, 88, 470, rowh=34)
    P.append(card(0, y2, 490, 186, s, .6, 1))
    # ML toolkit
    s = title("Machine learning toolkit", 2, "Models I have studied and trained")
    cx0, cy0, cw_, ch_ = 24, 84, 180, 84
    curve = f"M{cx0} {cy0+4} C{cx0+25} {cy0+6} {cx0+30} {cy0+58} {cx0+62} {cy0+64} S{cx0+120} {cy0+72} {cx0+cw_} {cy0+76}"
    noisy = f"M{cx0} {cy0} C{cx0+20} {cy0+14} {cx0+28} {cy0+44} {cx0+52} {cy0+50} S{cx0+110} {cy0+62} {cx0+cw_} {cy0+70}"
    s += (f'<path d="M{cx0} {cy0-4} V{cy0+ch_} H{cx0+cw_}" fill="none" stroke="var(--bd)" stroke-width="1.5" stroke-linecap="round"/>'
          f'<path d="{noisy}" fill="none" stroke="var(--k3)" stroke-width="2" stroke-linecap="round" stroke-opacity=".75" pathLength="1000" stroke-dasharray="1000" stroke-dashoffset="1000"><animate attributeName="stroke-dashoffset" values="1000;0;0;-1000" keyTimes="0;.5;.85;1" dur="5.5s" repeatCount="indefinite"/></path>'
          f'<path d="{curve}" fill="none" stroke="url(#ls)" stroke-width="2.5" stroke-linecap="round" pathLength="1000" stroke-dasharray="1000" stroke-dashoffset="1000"><animate attributeName="stroke-dashoffset" values="1000;0;0;-1000" keyTimes="0;.55;.85;1" dur="5.5s" begin=".2s" repeatCount="indefinite"/></path>'
          f'<text x="{cx0+cw_}" y="{cy0+ch_+14}" text-anchor="end" style="font:400 10.5px {MONO};fill:var(--mu)">epochs</text>'
          f'<text x="{cx0+8}" y="{cy0+ch_+14}" style="font:400 10.5px {MONO};fill:var(--mu)">loss</text>')
    s += pill_flow([("Linear Reg.", 1), ("Logistic Reg.", 5), ("Decision Tree", 4), ("Random Forest", 5), ("K-means", 6), ("CNN", 2), ("RNN", 3), ("ViT", 1)], 226, 82, 472, rowh=32)
    P.append(card(506, y2, 494, 186, s, .75, 2))
    # journey
    y3 = y2 + 186 + 16
    s = title("Journey", 2)
    steps = [("2023", "Network intern", "Algérie Télécom", 1, "briefcase"), ("2024", "Telecom intern", "ATM Mobilis", 2, "briefcase"),
             ("2025", "Web developer intern", "SARL Baladiyatech", 3, "code"), ("June 2025", "Graduated, engineer", "ENSTTIC, Oran", 5, "mortar-board")]
    s += ('<path d="M120 112 H880" stroke="var(--c0)" stroke-width="4" stroke-linecap="round"/>'
          '<path d="M120 112 H880" stroke="url(#jl)" stroke-width="4" stroke-linecap="round" pathLength="1000" stroke-dasharray="1000" stroke-dashoffset="1000"><animate attributeName="stroke-dashoffset" values="1000;1000;0" keyTimes="0;.15;1" dur="2.6s" fill="freeze"/></path>')
    for i, (yr, role, org, k, ic) in enumerate(steps):
        x = 120 + i * 253.3
        s += (f'<circle cx="{x:.0f}" cy="112" r="17" fill="var(--k{k})"/>{octi(ic, x-9, 103, 18, "var(--card)")}<circle cx="{x:.0f}" cy="112" r="17" fill="none" stroke="var(--k{k})"><animate attributeName="r" values="17;32" dur="2.6s" begin="{i*.5}s" repeatCount="indefinite"/><animate attributeName="stroke-opacity" values=".8;0" dur="2.6s" begin="{i*.5}s" repeatCount="indefinite"/></circle>'
              f'<text x="{x:.0f}" y="78" text-anchor="middle" style="font:700 20px {SANS};fill:var(--k{k})">{yr}</text>'
              f'<text x="{x:.0f}" y="158" text-anchor="middle" style="font:700 14px {SANS};fill:var(--tx)">{role}</text><text class="sb" x="{x:.0f}" y="178" text-anchor="middle">{org}</text>')
    P.append(card(0, y3, 1000, 196, s, .9, 2))
    wrap("work.svg", 1000, y3 + 196, "Focus areas, final-year ECG project, real estate platform, machine learning toolkit and career journey", "".join(P))

# ------------------------------------------------------------------ stack
def stack():
    rows = [("Web", [("HTML", "html5"), ("CSS", "css3"), ("JavaScript", "javascript"), ("React", "react"), ("Next.js", "nextdotjs"), ("Node.js", "nodedotjs"),
                     ("Express", "express"), ("PHP", "php"), ("Laravel", "laravel"), ("Inertia.js", "o:code"), ("WordPress", "wordpress")]),
            ("ML + data", [("Python", "python"), ("Jupyter", "jupyter"), ("Kaggle", "g:chart"), ("MATLAB", "g:chart"), ("CNN · RNN · ViT", "o:cpu"), ("MySQL", "mysql"),
                           ("PostgreSQL", "postgresql"), ("MongoDB", "mongodb"), ("Redis", "redis"), ("Cassandra", "g:db"), ("Neo4j", "g:db")]),
            ("DevOps + net", [("Docker", "docker"), ("Kubernetes", "kubernetes"), ("Git", "git"), ("GitHub", "github"), ("Postman", "postman"),
                              ("Wireshark", "g:net"), ("GNS3", "g:net"), ("Packet Tracer", "g:net"), ("OSPF · VLAN · TCP/IP", "g:net")])]
    top, rh = 56, 44
    H = top + len(rows) * rh + 4
    s = title("Stack", 6) + f'<clipPath id="sc"><rect x="0" y="{top-2}" width="1000" height="{H-top}"/></clipPath><g clip-path="url(#sc)">'
    cw = 12.5 * MONO_W
    for r, (_, items) in enumerate(rows):
        x = 0; row = ""; y = top + r * rh
        for it, slug in items:
            w = len(it) * cw + 58
            if slug.startswith("o:"): ico = octi(slug[2:], x + 14, y + 9, 16, "var(--k1)")
            elif slug.startswith("g:"): ico = glyph(slug[2:], x + 14, y + 9, 16, "var(--k2)")
            else: ico = brand(slug, x + 14, y + 8, 18)
            row += (f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="34" rx="17" fill="var(--chip)" stroke="var(--bd)"/>{ico}'
                    f'<text class="mono" x="{x+40:.0f}" y="{y+22}">{esc(it)}</text>')
            x += w + 12
        a2, b2 = (0, -x) if r % 2 == 0 else (-x, 0)
        s += (f'<g><animateTransform attributeName="transform" type="translate" from="{a2:.0f} 0" to="{b2:.0f} 0" dur="{38+r*7}s" repeatCount="indefinite"/>'
              f'{row}<g transform="translate({x:.0f} 0)">{row}</g><g transform="translate({2*x:.0f} 0)">{row}</g></g>')
    s += f'<rect x="0" y="{top-2}" width="70" height="{H-top}" fill="url(#fl)"/><rect x="930" y="{top-2}" width="70" height="{H-top}" fill="url(#fr)"/></g>'
    wrap("stack.svg", 1000, H, "Technologies: HTML, CSS, JavaScript, React, Next.js, Node.js, Express, PHP, Laravel, Python, Jupyter, MySQL, PostgreSQL, MongoDB, Redis, Docker, Kubernetes, Git, GitHub, Postman, Wireshark", card(0, 0, 1000, H, s, .3, 6))

def links():
    for name, label, slug in [("github", "GitHub", "github"), ("linkedin", "LinkedIn", "linkedin"), ("email", "Email", "gmail")]:
        body = (f'<clipPath id="lc"><rect width="168" height="52" rx="26"/></clipPath><rect class="card" x=".5" y=".5" width="167" height="51" rx="25.5"/>'
                f'<g clip-path="url(#lc)"><rect y="0" width="60" height="52" fill="url(#sw)"><animateTransform attributeName="transform" type="translate" values="-60 0;168 0;168 0" keyTimes="0;.4;1" dur="4s" begin="{len(name)%3}s" repeatCount="indefinite"/></rect></g>'
                f'{brand(slug, 22, 14, 24)}<text x="58" y="31" style="font:700 15px {SANS};fill:var(--tx)">{label}</text>')
        (OUT / f"link-{name}.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 168 52" width="168" height="52" role="img" aria-label="{label}"><style>{THEME_LINK}</style>{defs()}{body}</svg>', encoding="utf-8")

hero(); overview(); activity(); work(); stack(); links()
print("assets written | mode:", MODE, "| token:", bool(TOKEN), "| live data:", live, "| stats:", S, "| streak:", cur, longest, active)
