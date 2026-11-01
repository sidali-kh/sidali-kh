#!/usr/bin/env python3
"""Builds the animated SVGs for the profile README.
Fetches live numbers from GitHub (REST + GraphQL) when a token is available,
otherwise falls back to sample data so the layout always renders."""
import os, json, math, random, html, urllib.request, pathlib

USER = os.environ.get("GH_USER", "sidali-kh")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
OUT = pathlib.Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(exist_ok=True)
SANS = "Inter,'Segoe UI',system-ui,-apple-system,'Helvetica Neue',Arial,sans-serif"
MONO = "'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"
esc = html.escape

# ------------------------------------------------------------------ data
def api(url, body=None):
    h = {"User-Agent": "profile-builder", "Accept": "application/vnd.github+json"}
    if TOKEN: h["Authorization"] = f"Bearer {TOKEN}"
    data = json.dumps(body).encode() if body else None
    if body: h["Content-Type"] = "application/json"
    with urllib.request.urlopen(urllib.request.Request(url, data, h), timeout=20) as r:
        return json.load(r)

stats = {"repos": None, "stars": None, "followers": None, "contrib": None}
langs, days = [], []
try:
    u = api(f"https://api.github.com/users/{USER}")
    stats["repos"], stats["followers"] = u["public_repos"], u["followers"]
    repos = api(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner")
    stats["stars"] = sum(r["stargazers_count"] for r in repos)
    acc = {}
    for r in repos:
        if not r["fork"] and r["language"]:
            acc[r["language"]] = acc.get(r["language"], 0) + max(r["size"], 1)
    tot = sum(acc.values()) or 1
    langs = sorted(((k, v / tot * 100) for k, v in acc.items()), key=lambda x: -x[1])[:5]
except Exception as e:
    print("REST fetch failed:", e)
if TOKEN:
    try:
        q = '{user(login:"%s"){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionCount}}}}}}' % USER
        cal = api("https://api.github.com/graphql", {"query": q})["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        stats["contrib"] = cal["totalContributions"]
        days = [d["contributionCount"] for w in cal["weeks"] for d in w["contributionDays"]]
    except Exception as e:
        print("GraphQL fetch failed:", e)
WEEKS = 26
if len(days) < WEEKS * 7:  # preview data so the layout still renders
    random.seed(7)
    days = [max(0, int(random.gauss(2, 3))) if random.random() > .35 else 0 for _ in range(WEEKS * 7)]
window = days[-WEEKS * 7:]
if not langs:
    langs = [("JavaScript", 38), ("TypeScript", 24), ("PHP", 18), ("Python", 12), ("CSS", 8)]
LC = {"JavaScript": "#f1e05a", "TypeScript": "#3178c6", "PHP": "#8892bf", "HTML": "#e34c26", "CSS": "#8e6bd8",
      "Python": "#3572A5", "Blade": "#f7523f", "Dockerfile": "#4a90b8", "Shell": "#89e051",
      "Jupyter Notebook": "#DA5B0B", "Java": "#b07219", "C": "#9aa0a6", "C++": "#f34b7d"}
num = lambda v: "–" if v is None else f"{v:,}"

# ------------------------------------------------------------------ helpers
THEME = """:root{--card:#f6f8fc;--bd:#dde3ee;--tx:#111827;--mu:#5b6578;--a:#0a8fd1;--a2:#7c5cf0;--c0:#e6ebf4;--c1:#b9e1f6;--c2:#7ccbef;--c3:#34a9e0;--c4:#0a7fc0;--chip:#fff}
@media (prefers-color-scheme:dark){:root{--card:#141824;--bd:#242b3d;--tx:#eef1f8;--mu:#8d96ab;--a:#36bcf7;--a2:#a78bfa;--c0:#1a2030;--c1:#0f4a68;--c2:#11779f;--c3:#1fa3d6;--c4:#43c6fa;--chip:#1b2132}}
.card{fill:var(--card);stroke:var(--bd)}.ti{font:700 17px %s;fill:var(--tx)}.sb{font:400 13px %s;fill:var(--mu)}
.big{font:800 34px %s;fill:var(--tx)}.mono{font:500 13px %s;fill:var(--tx)}""" % (SANS, SANS, SANS, MONO)

def reveal(inner, delay, rise=14):
    """Fade-and-rise once on load. Visible by default if SMIL is unsupported."""
    d = delay + .7; k = f"0;{delay/d:.4f};1"
    return (f'<g>{inner}<animate attributeName="opacity" values="0;0;1" keyTimes="{k}" dur="{d:.2f}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" values="0 {rise};0 {rise};0 0" keyTimes="{k}" dur="{d:.2f}s" fill="freeze"/></g>')

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
                f'<text x="{x}" y="{y}" clip-path="url(#ty{i})" textLength="{n*cw:.1f}" lengthAdjust="spacing" style="font:500 {fs}px {MONO};fill:{color}">{esc(r)}</text>'
                f'<rect y="{y-fs+2}" width="3" height="{fs+2}" rx="1.5" fill="{color}" opacity="0"><animate attributeName="x" calcMode="discrete" keyTimes="{kt}" values="{cx}" dur="{T}s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" calcMode="discrete" keyTimes="0;{max(s,1e-5):.5f};{s+wd:.5f}" values="0;1;0" dur="{T}s" repeatCount="indefinite"/></rect>')
    return out

# ------------------------------------------------------------------ hero (always dark)
def hero():
    orbit = ""
    for r, dur, rev, dots in [(52, 18, 1, 1), (92, 28, -1, 2), (132, 42, 1, 3)]:
        a, b = (0, 360) if rev > 0 else (360, 0)
        d = "".join(f'<circle cx="{820+r*math.cos(2*math.pi*k/dots+r)}" cy="{170+r*math.sin(2*math.pi*k/dots+r)}" r="4" fill="#9fe0ff"/>' for k in range(dots))
        orbit += (f'<g><circle cx="820" cy="170" r="{r}" fill="none" stroke="#fff" stroke-opacity=".16" stroke-dasharray="3 7"/>{d}'
                  f'<animateTransform attributeName="transform" type="rotate" from="{a} 820 170" to="{b} 820 170" dur="{dur}s" repeatCount="indefinite"/></g>')
    blobs = ""
    for cx, cy, r, col, op, dur, dx, dy in [(220, 330, 170, "#36bcf7", .55, 15, 160, -50), (640, 40, 190, "#7c5cf0", .5, 19, -140, 60), (900, 330, 150, "#14b8a6", .4, 17, -120, -60)]:
        blobs += (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{col}" fill-opacity="{op}"><animateTransform attributeName="transform" type="translate" values="0 0;{dx} {dy};0 0" dur="{dur}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1"/></circle>')
    roles = ["Telecommunications & ICT Engineer", "Full-Stack Web Developer", "Building Modern Web Applications"]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 340" width="1000" height="340" role="img" aria-label="Sidali Khelil Cherfi: {esc(' | '.join(roles))}">
<defs><clipPath id="cl"><rect width="1000" height="340" rx="26"/></clipPath><filter id="bl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="55"/></filter>
<linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#7fd6ff"/><stop offset="1" stop-color="#c4b5fd"/></linearGradient></defs>
<g clip-path="url(#cl)"><rect width="1000" height="340" fill="#0a0d15"/><g filter="url(#bl)">{blobs}</g>{orbit}
<circle cx="820" cy="170" r="8" fill="#fff"><animate attributeName="r" values="7;11;7" dur="3s" repeatCount="indefinite"/></circle>
<rect width="1000" height="340" fill="#0a0d15" fill-opacity=".18"/></g>
<rect x=".5" y=".5" width="999" height="339" rx="25.5" fill="none" stroke="#fff" stroke-opacity=".1"/>
{reveal(f'<text x="56" y="132" style="font:800 78px {SANS};letter-spacing:-2px;fill:#fff">Sidali</text>',.1,18)}
{reveal(f'<text x="56" y="210" style="font:800 78px {SANS};letter-spacing:-2px;fill:url(#g)">Khelil Cherfi</text>',.35,18)}
{reveal(typing(roles,58,276,13.2,22,"#9fe0ff"),.8,0)}
</svg>'''
    (OUT / "hero.svg").write_text(svg, encoding="utf-8")

# ------------------------------------------------------------------ bento
def card(x, y, w, h, body, delay):
    return reveal(f'<g transform="translate({x} {y})"><rect class="card" width="{w}" height="{h}" rx="20"/>{body}</g>', delay)

def bento():
    parts = []
    # A: networks to interfaces
    nodes = [("IP network", 70), ("API", 235), ("Interface", 400)]
    s = '<text class="ti" x="26" y="44">From networks to interfaces</text><text class="sb" x="26" y="68">Telecom engineering, full-stack craft</text>'
    for j in range(2):
        x1, x2 = nodes[j][1] + 22, nodes[j + 1][1] - 22
        s += f'<path id="a{j}" d="M{x1} 128 L{x2} 128" stroke="var(--bd)" stroke-width="2" stroke-dasharray="4 6" fill="none"/>'
        for k in range(2):
            s += f'<circle r="4" fill="var(--a)"><animateMotion dur="1.9s" begin="{k*.95+j*.4}s" repeatCount="indefinite"><mpath href="#a{j}"/></animateMotion></circle>'
    for i, (t, x) in enumerate(nodes):
        s += (f'<circle cx="{x}" cy="128" r="20" fill="none" stroke="var(--a)" stroke-opacity=".6"><animate attributeName="r" values="20;32;32" keyTimes="0;.7;1" dur="2.8s" begin="{i*.6}s" repeatCount="indefinite"/><animate attributeName="stroke-opacity" values=".6;0;0" keyTimes="0;.7;1" dur="2.8s" begin="{i*.6}s" repeatCount="indefinite"/></circle>'
              f'<circle cx="{x}" cy="128" r="14" fill="url(#ng)"/><text class="sb" x="{x}" y="180" text-anchor="middle">{t}</text>')
    parts.append(card(0, 0, 470, 200, s, .9))
    # B: numbers
    items = [("Repositories", stats["repos"]), ("Stars", stats["stars"]), ("Followers", stats["followers"]), ("Contributions", stats["contrib"])]
    s = '<text class="ti" x="24" y="44">On GitHub</text>'
    for i, (l, v) in enumerate(items):
        x = 24 + (i % 2) * 116; y = 98 + (i // 2) * 62
        s += f'<text class="big" x="{x}" y="{y}">{num(v)}</text><text class="sb" x="{x}" y="{y+20}">{l}</text>'
    parts.append(card(486, 0, 254, 200, s, 1.05))
    # C: availability
    s = ('<circle cx="34" cy="40" r="5" fill="#22c55e"/><circle cx="34" cy="40" r="5" fill="none" stroke="#22c55e"><animate attributeName="r" values="5;14" dur="2s" repeatCount="indefinite"/><animate attributeName="stroke-opacity" values=".8;0" dur="2s" repeatCount="indefinite"/></circle>'
         '<text class="ti" x="52" y="46">Open to work</text>'
         '<text class="mono" x="24" y="88">Internship or CDD</text>'
         '<text class="sb" x="24" y="114">Full-Stack development</text><text class="sb" x="24" y="134">IP networks</text><text class="sb" x="24" y="154">AI and DevOps</text>'
         '<text class="sb" x="24" y="184">Médéa, Algeria</text>')
    parts.append(card(756, 0, 244, 200, s, 1.2))
    # D: heatmap
    mx = max(window) or 1
    lvl = lambda c: 0 if c == 0 else min(4, 1 + int(3 * (c - 1) / max(mx - 1, 1) + .0001))
    s = '<text class="ti" x="24" y="40">Activity</text><text class="sb" x="24" y="60">Last 26 weeks</text>'
    gx, gy, cs, gp = 24, 72, 13, 4
    cells = ""
    for i, c in enumerate(window):
        col, row = divmod(i, 7); d = 1.3 + col * .04
        k = f"0;{d/(d+.5):.4f};1"
        cells += f'<rect x="{gx+col*(cs+gp)}" y="{gy+row*(cs+gp)}" width="{cs}" height="{cs}" rx="3.5" fill="var(--c{lvl(c)})"><animate attributeName="opacity" values="0;0;1" keyTimes="{k}" dur="{d+.5:.2f}s" fill="freeze"/></rect>'
    gw = 26 * (cs + gp) - gp; gh = 7 * (cs + gp) - gp
    s += (f'<clipPath id="gc"><rect x="{gx}" y="{gy}" width="{gw}" height="{gh}"/></clipPath>{cells}'
          f'<g clip-path="url(#gc)"><rect y="{gy}" width="70" height="{gh}" fill="url(#sw)"><animateTransform attributeName="transform" type="translate" values="{gx-70} 0;{gx+gw} 0;{gx+gw} 0" keyTimes="0;.55;1" dur="7s" begin="2.5s" repeatCount="indefinite"/></rect></g>'
          f'<text class="big" x="{gx+gw+24}" y="112">{num(stats["contrib"])}</text><text class="sb" x="{gx+gw+24}" y="134">contributions</text><text class="sb" x="{gx+gw+24}" y="152">in the past year</text>')
    parts.append(card(0, 216, 620, 200, s, 1.35))
    # E: languages
    s = '<text class="ti" x="24" y="40">Languages</text>'
    for i, (n, p) in enumerate(langs):
        y = 72 + i * 25; bw = 336; fw = max(4, bw * p / 100); col = LC.get(n, "#8d96ab"); d = 1.6 + i * .12
        k = f"0;{d/(d+.9):.4f};1"
        s += (f'<text class="mono" x="24" y="{y}">{esc(n)}</text><text class="sb" x="360" y="{y}" text-anchor="end">{p:.0f}%</text>'
              f'<rect x="24" y="{y+7}" width="{bw}" height="6" rx="3" fill="var(--c0)"/>'
              f'<rect x="24" y="{y+7}" width="{fw:.0f}" height="6" rx="3" fill="{col}"><animate attributeName="width" values="0;0;{fw:.0f}" keyTimes="{k}" dur="{d+.9:.2f}s" fill="freeze"/></rect>')
    parts.append(card(636, 216, 364, 200, s, 1.5))
    # F: stack marquee
    rows = [["HTML", "CSS", "JavaScript", "TypeScript", "React", "Next.js", "Tailwind", "Node.js", "Express", "PHP", "Laravel", "WordPress"],
            ["MySQL", "PostgreSQL", "MongoDB", "Redis", "Docker", "Kubernetes", "Git", "GitHub", "Postman", "Linux", "MERN", "ML / CNN"]]
    s = '<text class="ti" x="24" y="40">Stack</text><clipPath id="sc"><rect x="0" y="52" width="1000" height="84"/></clipPath><g clip-path="url(#sc)">'
    for r, items in enumerate(rows):
        x = 0; row = ""
        for it in items:
            w = len(it) * 8.2 + 32
            row += f'<rect x="{x:.0f}" y="{54+r*44}" width="{w:.0f}" height="34" rx="17" fill="var(--chip)" stroke="var(--bd)"/><text class="mono" x="{x+w/2:.0f}" y="{54+r*44+22}" text-anchor="middle">{esc(it)}</text>'
            x += w + 12
        a, b = (0, -x) if r == 0 else (-x, 0)
        s += (f'<g><animateTransform attributeName="transform" type="translate" from="{a:.0f} 0" to="{b:.0f} 0" dur="{34+r*6}s" repeatCount="indefinite"/>'
              f'{row}<g transform="translate({x:.0f} 0)">{row}</g><g transform="translate({2*x:.0f} 0)">{row}</g></g>')
    s += '<rect x="0" y="52" width="70" height="84" fill="url(#fl)"/><rect x="930" y="52" width="70" height="84" fill="url(#fr)"/></g>'
    parts.append(card(0, 432, 1000, 150, s, 1.65))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 582" width="1000" height="582" role="img" aria-label="Profile overview: skills, GitHub activity, languages and availability">
<style>{THEME}</style>
<defs><linearGradient id="ng" x1="0" y1="0" x2="1" y2="1"><stop offset="0" style="stop-color:var(--a)"/><stop offset="1" style="stop-color:var(--a2)"/></linearGradient>
<linearGradient id="sw" x1="0" x2="1"><stop offset="0" style="stop-color:var(--a);stop-opacity:0"/><stop offset=".5" style="stop-color:var(--a);stop-opacity:.4"/><stop offset="1" style="stop-color:var(--a);stop-opacity:0"/></linearGradient>
<linearGradient id="fl" x1="0" x2="1"><stop offset="0" style="stop-color:var(--card)"/><stop offset="1" style="stop-color:var(--card);stop-opacity:0"/></linearGradient>
<linearGradient id="fr" x1="0" x2="1"><stop offset="0" style="stop-color:var(--card);stop-opacity:0"/><stop offset="1" style="stop-color:var(--card)"/></linearGradient></defs>
{''.join(parts)}</svg>'''
    (OUT / "bento.svg").write_text(svg, encoding="utf-8")

hero(); bento(); print("assets written; token:", bool(TOKEN), "| stats:", stats)
