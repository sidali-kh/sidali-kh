#!/usr/bin/env python3
"""Builds the animated SVGs for the profile README.

Data: live GitHub numbers (REST + GraphQL) when GITHUB_TOKEN is available,
otherwise clearly-marked DEMO data so the layout always looks complete."""
import os, json, math, random, html, base64, datetime, urllib.request, pathlib

HERE = pathlib.Path(__file__).resolve().parent
USER = os.environ.get("GH_USER", "sidali-kh")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
OUT = HERE.parent / "assets"; OUT.mkdir(exist_ok=True)
MONO = "'JetBrains Mono','SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"
SANS = MONO  # one typeface for the whole profile
esc = html.escape
cut = lambda t, n: t if len(t) <= n else t[:n - 1].rstrip() + "…"
SHORT = {"Jupyter Notebook": "Jupyter"}
num = lambda v: "–" if v is None else f"{v:,}"
ICONS = json.loads((HERE / "icons.json").read_text(encoding="utf-8"))

# ------------------------------------------------------------------ data
def api(url, body=None):
    h = {"User-Agent": "profile-builder", "Accept": "application/vnd.github+json"}
    if TOKEN: h["Authorization"] = f"Bearer {TOKEN}"
    data = json.dumps(body).encode() if body else None
    if body: h["Content-Type"] = "application/json"
    with urllib.request.urlopen(urllib.request.Request(url, data, h), timeout=20) as r:
        return json.load(r)

live = False
S, langs, toprepos, weeks = {}, [], [], []
if TOKEN:
    try:
        u = api(f"https://api.github.com/users/{USER}")
        repos = api(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner")
        own = [r for r in repos if not r["fork"]]
        acc = {}
        for r in own:
            if r["language"]: acc[r["language"]] = acc.get(r["language"], 0) + max(r["size"], 1)
        tot = sum(acc.values()) or 1
        langs = sorted(((k, v / tot * 100) for k, v in acc.items()), key=lambda x: -x[1])[:5]
        toprepos = sorted(own, key=lambda r: (r["stargazers_count"], r["pushed_at"]), reverse=True)[:3]
        q = ('{user(login:"%s"){contributionsCollection{totalCommitContributions totalPullRequestContributions totalIssueContributions '
             'contributionCalendar{totalContributions weeks{contributionDays{contributionCount date}}}}}}' % USER)
        cc = api("https://api.github.com/graphql", {"query": q})["data"]["user"]["contributionsCollection"]
        S = dict(repos=u["public_repos"], stars=sum(r["stargazers_count"] for r in repos), followers=u["followers"],
                 commits=cc["totalCommitContributions"], prs=cc["totalPullRequestContributions"],
                 issues=cc["totalIssueContributions"], contrib=cc["contributionCalendar"]["totalContributions"])
        weeks = [[(d["date"], d["contributionCount"]) for d in w["contributionDays"]] for w in cc["contributionCalendar"]["weeks"]]
        live = True
    except Exception as e:
        print("Live fetch failed, using demo data:", e)

if not live:  # ---------- DEMO DATA (placeholder numbers, replaced automatically by the workflow)
    S = dict(repos=24, stars=87, followers=56, commits=612, prs=38, issues=21, contrib=1248)
    langs = [("TypeScript", 32), ("JavaScript", 25), ("PHP", 17), ("Jupyter Notebook", 16), ("CSS", 10)]
    toprepos = [dict(name="realestate-platform", description="Next.js + headless WordPress", language="TypeScript", stargazers_count=34),
                dict(name="ecg-cardio-ai", description="Deep learning on ECG images", language="Jupyter Notebook", stargazers_count=28),
                dict(name="mern-commerce", description="MERN store with auth and roles", language="JavaScript", stargazers_count=19)]
    random.seed(11)
    today = datetime.date.today(); start = today - datetime.timedelta(days=364)
    start -= datetime.timedelta(days=(start.weekday() + 1) % 7)
    d, weeks, n = start, [], 0
    total_days = (today - start).days + 1
    while d <= today:
        wk = []
        for _ in range(7):
            if d <= today:
                n += 1; wd = (d.weekday() + 1) % 7
                busy = .78 if 1 <= wd <= 4 else .35
                c = max(1, int(random.gauss(4, 3))) if random.random() < busy else 0
                if total_days - n < 14: c = max(c, random.randint(1, 5))
                wk.append((d.isoformat(), c))
            d += datetime.timedelta(days=1)
        weeks.append(wk)
flat = [c for w in weeks for _, c in w]
if live:
    cur = 0
    for c in (flat[:-1] if flat and flat[-1] == 0 else flat)[::-1]:
        if c > 0: cur += 1
        else: break
    longest = run = 0
    for c in flat:
        run = run + 1 if c > 0 else 0; longest = max(longest, run)
    active = sum(1 for c in flat if c > 0)
else:
    cur, longest, active = 14, 47, 186
wk_tot = [0] * 7
for w in weeks:
    for dt, c in w: wk_tot[(datetime.date.fromisoformat(dt).weekday() + 1) % 7] += c
LC = {"JavaScript": "#f1e05a", "TypeScript": "#3178c6", "PHP": "#8892bf", "HTML": "#e34c26", "CSS": "#a78bfa",
      "Python": "#3fa0e0", "Blade": "#f7523f", "Dockerfile": "#4a90b8", "Shell": "#89e051", "Jupyter Notebook": "#f37626",
      "Java": "#b07219", "C": "#9aa0a6", "C++": "#f34b7d", "Vue": "#41b883", "SCSS": "#c6538c"}
LANG_FALLBACK = ["#36bcf7", "#f472b6", "#fbbf24", "#34d399", "#a78bfa"]

# ------------------------------------------------------------------ fonts (embedded so they work inside README images)
def fontcss():
    css = ""
    for fam, f in [("JetBrains Mono", "jetbrains-mono")]:
        for w in (500, 700):
            b = base64.b64encode((HERE / "fonts" / f"{f}-latin-{w}-normal.woff2").read_bytes()).decode()
            css += f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:normal;src:url(data:font/woff2;base64,{b}) format('woff2')}}"
    return css
FONTCSS = fontcss()
_b = base64.b64encode((HERE / "fonts" / "jetbrains-mono-latin-700-normal.woff2").read_bytes()).decode()
FONT_BTN = f"@font-face{{font-family:'JetBrains Mono';font-weight:700;font-style:normal;src:url(data:font/woff2;base64,{_b}) format('woff2')}}"

THEME = """:root{--card:#f7f9fd;--bd:#dde3ee;--tx:#111827;--mu:#5b6578;--chip:#fff;--c0:#e6ebf4;--c1:#d9d0fb;--c2:#a99af2;--c3:#4fc3f7;--c4:#10b981;
--k1:#0a8fd1;--k2:#7c5cf0;--k3:#db2777;--k4:#d97706;--k5:#059669;--k6:#ea580c}
@media (prefers-color-scheme:dark){:root{--card:#131724;--bd:#242b3d;--tx:#eef1f8;--mu:#8d96ab;--chip:#1b2132;--c0:#1a2030;--c1:#3b2a7a;--c2:#5b4fd6;--c3:#22b8f0;--c4:#34d399;
--k1:#36bcf7;--k2:#a78bfa;--k3:#f472b6;--k4:#fbbf24;--k5:#34d399;--k6:#fb923c}}
.card{fill:var(--card);stroke:var(--bd)}.ti{font:700 17px %s;fill:var(--tx)}.sb{font:500 12px %s;fill:var(--mu)}
.big{font:700 34px %s;fill:var(--tx)}.mono{font:500 13px %s;fill:var(--tx)}""" % (SANS, SANS, SANS, MONO)

# ------------------------------------------------------------------ icon + layout helpers
def _lum(h):
    r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4)); return .2126 * r + .7152 * g + .0722 * b
def brand(slug, x, y, size, fill=None):
    ic = ICONS["brand"][slug]
    f = fill or (f"#{ic['c']}" if .22 < _lum(ic["c"]) < .9 else "var(--tx)")
    return f'<path transform="translate({x} {y}) scale({size/24:.4f})" d="{ic["p"]}" fill="{f}"/>'
def octi(name, x, y, size, fill):
    return f'<g transform="translate({x} {y}) scale({size/16:.4f})" fill="{fill}">{ICONS["octicon"][name]}</g>'
LANGSLUG = {"JavaScript": "javascript", "TypeScript": "typescript", "PHP": "php", "HTML": "html5", "CSS": "css3", "Python": "python",
            "Blade": "laravel", "Dockerfile": "docker", "Shell": "gnubash", "Jupyter Notebook": "jupyter", "Java": "openjdk", "C": "c",
            "C++": "cplusplus", "Vue": "vuedotjs", "SCSS": "sass", "Go": "go", "Rust": "rust", "Dart": "dart", "Kotlin": "kotlin", "Swift": "swift"}
def lang_icon(name, x, y, size):
    slug = LANGSLUG.get(name)
    return brand(slug, x, y, size) if slug in ICONS["brand"] else octi("code", x, y, size, "var(--mu)")
def netglyph(x, y, c, s=24):
    return (f'<g transform="translate({x} {y}) scale({s/24:.3f})" stroke="{c}" stroke-width="1.8" fill="none" stroke-linecap="round"><path d="M4 18 L12 6 L20 18 M4 18 H20"/>'
            f'<circle cx="12" cy="6" r="3" fill="{c}"/><circle cx="4" cy="18" r="3" fill="{c}"/><circle cx="20" cy="18" r="3" fill="{c}"/></g>')
def spark(x, y, c, s=24):
    return f'<path transform="translate({x} {y}) scale({s/24:.3f})" d="M12 2l2.2 6.8L21 11l-6.8 2.2L12 20l-2.2-6.8L3 11l6.8-2.2zM19 3l.8 2.2L22 6l-2.2.8L19 9l-.8-2.2L16 6l2.2-.8z" fill="{c}"/>'

def defs():
    g = "".join(f'<radialGradient id="g{i}" cx=".08" cy="0" r="1.1"><stop offset="0" style="stop-color:var(--k{i});stop-opacity:.22"/><stop offset="1" style="stop-color:var(--k{i});stop-opacity:0"/></radialGradient>' for i in range(1, 7))
    return (f'<defs>{g}<linearGradient id="sw" x1="0" x2="1"><stop offset="0" style="stop-color:var(--k1);stop-opacity:0"/><stop offset=".5" style="stop-color:var(--k1);stop-opacity:.45"/><stop offset="1" style="stop-color:var(--k1);stop-opacity:0"/></linearGradient>'
            '<linearGradient id="fl" x1="0" x2="1"><stop offset="0" style="stop-color:var(--card)"/><stop offset="1" style="stop-color:var(--card);stop-opacity:0"/></linearGradient>'
            '<linearGradient id="fr" x1="0" x2="1"><stop offset="0" style="stop-color:var(--card);stop-opacity:0"/><stop offset="1" style="stop-color:var(--card)"/></linearGradient>'
            '<linearGradient id="ecg" x1="0" x2="1"><stop offset="0" style="stop-color:var(--k3)"/><stop offset="1" style="stop-color:var(--k4)"/></linearGradient>'
            '<linearGradient id="jl" x1="0" x2="1"><stop offset="0" style="stop-color:var(--k1)"/><stop offset=".5" style="stop-color:var(--k2)"/><stop offset="1" style="stop-color:var(--k3)"/></linearGradient></defs>')

def wrap(name, w, h, label, body):
    (OUT / name).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(label)}"><style>{FONTCSS}{THEME}</style>{defs()}{body}</svg>', encoding="utf-8")

def reveal(inner, delay, rise=14):
    d = delay + .7; k = f"0;{delay/d:.4f};1"
    return (f'<g>{inner}<animate attributeName="opacity" values="0;0;1" keyTimes="{k}" dur="{d:.2f}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" values="0 {rise};0 {rise};0 0" keyTimes="{k}" dur="{d:.2f}s" fill="freeze"/></g>')

def card(x, y, w, h, body, delay, k=1):
    return reveal(f'<g transform="translate({x} {y})"><rect class="card" width="{w}" height="{h}" rx="20"/><rect width="{w}" height="{h}" rx="20" fill="url(#g{k})"/>{body}</g>', delay)

def title(t, k, sub=None):
    s = f'<rect x="24" y="29" width="8" height="8" rx="2.5" fill="var(--k{k})"/><text class="ti" x="40" y="39">{esc(t)}</text>'
    return s + (f'<text class="sb" x="24" y="60">{esc(sub)}</text>' if sub else "")

def pill(x, y, t, k, slug=None, size=12):
    cw = size * .6; w = len(t) * cw + 22 + (size + 6 if slug else 0)
    ico = ""
    if slug:
        ico = octi(slug[2:], x + 10, y + (26 - size) / 2, size, f"var(--k{k})") if slug.startswith("o:") else brand(slug, x + 10, y + (26 - size) / 2, size)
    tx = x + 11 + (size + 6 if slug else 0)
    return (f'<rect x="{x}" y="{y}" width="{w:.0f}" height="26" rx="13" fill="var(--k{k})" fill-opacity=".14" stroke="var(--k{k})" stroke-opacity=".5"/>{ico}'
            f'<text x="{tx:.0f}" y="{y+17}" style="font:500 {size}px {MONO};fill:var(--tx)">{esc(t)}</text>'), w

def flow_pills(items, x0, y0, maxw, k, size=12, gap=6):
    out, x, y = "", x0, y0
    for it in items:
        t, slug = it if isinstance(it, tuple) else (it, None)
        p, w = pill(x, y, t, k, slug, size)
        if x + w > x0 + maxw and x > x0: x = x0; y += 26 + gap; p, w = pill(x, y, t, k, slug, size)
        out += p; x += w + gap
    return out, y + 26 - y0

def growbar(x, base, w, h, fill, delay, rx=6):
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
                f'<text x="{x}" y="{y}" clip-path="url(#ty{i})" textLength="{n*cw:.1f}" lengthAdjust="spacing" style="font:500 {fs}px {MONO};fill:{color}">{esc(r)}</text>'
                f'<rect y="{y-fs+2}" width="3" height="{fs+2}" rx="1.5" fill="{color}" opacity="0"><animate attributeName="x" calcMode="discrete" keyTimes="{kt}" values="{cx}" dur="{T}s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" calcMode="discrete" keyTimes="0;{max(s,1e-5):.5f};{s+wd:.5f}" values="0;1;0" dur="{T}s" repeatCount="indefinite"/></rect>')
    return out

# ------------------------------------------------------------------ hero (always dark)
def hero():
    """Right side: one request travelling through the stack I work on:
    ECG signal -> ML model -> API -> UI, looping every 8 seconds."""
    T = 8
    AC = ["#7fd6ff", "#c4b5fd", "#6ee7b7", "#f9a8d4"]
    def kv(kt, vals): return f'keyTimes="{";".join(f"{t:.4f}" for t in kt)}" values="{";".join(str(v) for v in vals)}"'
    def act(i, base, hi, attr):
        st, e = i / 4, (i + 1) / 4
        if i == 0: kt, v = [0, e, e + .03, 1], [hi, hi, base, base]
        elif i == 3: kt, v = [0, st, st + .03, 1], [base, base, hi, hi]
        else: kt, v = [0, st, st + .03, e, e + .03, 1], [base, base, hi, hi, base, base]
        return f'<animate attributeName="{attr}" {kv(kt, v)} dur="{T}s" repeatCount="indefinite"/>'
    def vis(t0, t1=None):
        if t1 is None: kt, v = [0, t0, 1], [0, 1, 1]
        else: kt, v = [0, t0, t1, 1], [0, 1, 0, 0]
        return f'<animate attributeName="opacity" calcMode="discrete" {kv(kt, v)} dur="{T}s" repeatCount="indefinite"/>'
    lab = lambda t, i: f'<text x="12" y="20" style="font:700 10px {MONO};letter-spacing:1px;fill:{AC[i]}">{t}</text>'
    foot = lambda t: f'<text x="12" y="101" style="font:500 10px {MONO};fill:#94a3b8">{t}</text>'
    def shell(x, y, i, inner):
        return (f'<g transform="translate({x} {y})"><rect width="160" height="110" rx="14" fill="{AC[i]}" fill-opacity="0">{act(i, 0, .14, "fill-opacity")}</rect>'
                f'<rect width="160" height="110" rx="14" fill="#fff" fill-opacity=".05" stroke="{AC[i]}" stroke-opacity=".25">{act(i, .25, 1, "stroke-opacity")}</rect>{inner}</g>')
    # 01 signal: scrolling ECG
    beat = "h10 l3,-4 l3,4 h5 l2,3 l4,-26 l4,34 l3,-10 h5 l3,-5 l3,5 h12"
    A = (lab("01 SIGNAL", 0) + f'<clipPath id="ca"><rect x="8" y="28" width="144" height="60"/></clipPath><g clip-path="url(#ca)"><g>'
         f'<path d="M0 62 {beat*9}" fill="none" stroke="{AC[0]}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
         '<animateTransform attributeName="transform" type="translate" from="0 0" to="-57 0" dur="1.4s" repeatCount="indefinite"/></g></g>' + foot("ECG input"))
    # 02 model: tiny network
    xs = [34, 80, 126]; ys = [[48, 64, 80], [42, 56, 70, 84], [56, 72]]; ln = nd = ""
    for l in range(2):
        for y1 in ys[l]:
            for y2 in ys[l + 1]:
                ln += f'<line x1="{xs[l]}" y1="{y1}" x2="{xs[l+1]}" y2="{y2}" stroke="{AC[1]}" stroke-opacity=".28"/>'
    for l in range(3):
        for y in ys[l]: nd += f'<circle cx="{xs[l]}" cy="{y}" r="4.5" fill="{AC[1]}" opacity=".4">{act(1, .4, 1, "opacity")}</circle>'
    B = lab("02 MODEL", 1) + ln + nd + foot("CNN predict(ecg)")
    # 03 api: request / response
    st = 2 / 4
    C = (lab("03 API", 2) + f'<text x="12" y="46" opacity="0" style="font:500 10px {MONO};fill:#e2e8f0">POST /predict{vis(st+.01)}</text>'
         f'<text x="12" y="62" opacity="0" style="font:500 10px {MONO};fill:#94a3b8">{{ ecg: [0.12, ...] }}{vis(st+.05)}</text>'
         f'<text x="12" y="80" opacity="0" style="font:700 10px {MONO};fill:{AC[2]}">200 OK  34ms{vis(st+.11)}</text>' + foot("Node / Laravel"))
    # 04 ui: browser result
    st = 3 / 4
    dots = "".join(f'<circle cx="{124+k*10}" cy="16" r="2.5" fill="{c}"/>' for k, c in enumerate(["#f87171", "#fbbf24", "#34d399"]))
    D = (lab("04 UI", 3) + dots + f'<text x="12" y="46" opacity="0" style="font:700 11px {MONO};fill:#fff">Normal rhythm{vis(st+.02)}</text>'
         '<rect x="12" y="55" width="136" height="6" rx="3" fill="#fff" fill-opacity=".12"/>'
         f'<rect x="12" y="55" width="0" height="6" rx="3" fill="{AC[3]}"><animate attributeName="width" {kv([0, st+.02, st+.12, 1], [0, 0, 132, 132])} dur="{T}s" repeatCount="indefinite"/></rect>'
         f'<text x="12" y="86" opacity="0" style="font:700 18px {MONO};fill:{AC[3]}">97%{vis(st+.1)}</text>' + foot("Next.js interface"))
    cards = shell(590, 40, 0, A) + shell(800, 40, 1, B) + shell(800, 190, 2, C) + shell(590, 190, 3, D)
    paths = ["M750 95 L800 95", "M880 150 L880 190", "M800 245 L750 245", "M670 190 L670 150"]
    flow = ""
    for i, d in enumerate(paths):
        ts, te = i / 4 + .12, (i + 1) / 4 - (.001 if i == 3 else 0)
        flow += (f'<path id="hp{i}" d="{d}" stroke="#fff" stroke-opacity=".25" stroke-width="1.5" stroke-dasharray="3 5" fill="none"><animate attributeName="stroke-dashoffset" from="16" to="0" dur="1s" repeatCount="indefinite"/></path>'
                 f'<circle r="4.5" fill="{AC[i]}" opacity="0">{vis(ts, te)}<animateMotion dur="{T}s" repeatCount="indefinite" calcMode="linear" keyPoints="0;0;1;1" keyTimes="0;{ts:.4f};{te:.4f};1"><mpath href="#hp{i}"/></animateMotion></circle>')
    blobs = ""
    for cx, cy, r, col, op, dur, dx, dy in [(200, 340, 170, "#36bcf7", .55, 15, 160, -50), (620, 30, 180, "#7c5cf0", .55, 19, -140, 60),
                                            (930, 340, 150, "#14b8a6", .45, 17, -120, -60), (430, 360, 120, "#f472b6", .5, 13, 120, -70),
                                            (980, 20, 110, "#fbbf24", .35, 16, -90, 70)]:
        blobs += (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{col}" fill-opacity="{op}"><animateTransform attributeName="transform" type="translate" values="0 0;{dx} {dy};0 0" dur="{dur}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1"/></circle>')
    roles = ["Full-Stack Web Developer", "Machine Learning Enthusiast", "Telecommunications & ICT Engineer"]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 340" width="1000" height="340" role="img" aria-label="Sidali Khelil Cherfi: {esc(' | '.join(roles))}. Animation: an ECG signal flows through a machine learning model and an API into a web interface."><style>{FONTCSS}</style>
<defs><clipPath id="cl"><rect width="1000" height="340" rx="26"/></clipPath><filter id="bl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="55"/></filter>
<linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#7fd6ff"/><stop offset=".55" stop-color="#c4b5fd"/><stop offset="1" stop-color="#f9a8d4"/></linearGradient></defs>
<g clip-path="url(#cl)"><rect width="1000" height="340" fill="#0a0d15"/><g filter="url(#bl)">{blobs}</g><rect width="1000" height="340" fill="#0a0d15" fill-opacity=".35"/>{flow}{cards}</g>
<rect x=".5" y=".5" width="999" height="339" rx="25.5" fill="none" stroke="#fff" stroke-opacity=".12"/>
{reveal(f'<text x="54" y="124" style="font:700 64px {MONO};letter-spacing:-3px;fill:#fff">Sidali</text>',.1,18)}
{reveal(f'<text x="54" y="194" style="font:700 64px {MONO};letter-spacing:-3px;fill:url(#g)">Khelil Cherfi</text>',.35,18)}
{reveal(typing(roles,58,262,13.2,22,"#9fe0ff"),.8,0)}
</svg>'''
    (OUT / "hero.svg").write_text(svg, encoding="utf-8")

# ------------------------------------------------------------------ overview
def overview():
    P = []
    nodes = [("IP network", 70), ("API", 235), ("Interface", 400)]
    s = title("From networks to interfaces", 1, "Telecom engineering, full-stack craft")
    for j in range(2):
        x1, x2 = nodes[j][1] + 22, nodes[j + 1][1] - 22
        s += f'<path id="a{j}" d="M{x1} 128 L{x2} 128" stroke="var(--bd)" stroke-width="2" stroke-dasharray="4 6" fill="none"/>'
        for k, col in enumerate(["var(--k1)", "var(--k3)"]):
            s += f'<circle r="4.5" fill="{col}"><animateMotion dur="1.9s" begin="{k*.95+j*.4}s" repeatCount="indefinite"><mpath href="#a{j}"/></animateMotion></circle>'
    for i, (t, x) in enumerate(nodes):
        c = ["var(--k1)", "var(--k2)", "var(--k3)"][i]
        s += (f'<circle cx="{x}" cy="128" r="20" fill="none" stroke="{c}" stroke-opacity=".7"><animate attributeName="r" values="20;32;32" keyTimes="0;.7;1" dur="2.8s" begin="{i*.6}s" repeatCount="indefinite"/><animate attributeName="stroke-opacity" values=".7;0;0" keyTimes="0;.7;1" dur="2.8s" begin="{i*.6}s" repeatCount="indefinite"/></circle>'
              f'<circle cx="{x}" cy="128" r="14" fill="{c}"/><text class="sb" x="{x}" y="180" text-anchor="middle">{t}</text>')
    P.append(card(0, 0, 470, 200, s, .9, 1))
    s = ('<circle cx="34" cy="38" r="5" fill="#22c55e"/><circle cx="34" cy="38" r="5" fill="none" stroke="#22c55e"><animate attributeName="r" values="5;14" dur="2s" repeatCount="indefinite"/><animate attributeName="stroke-opacity" values=".8;0" dur="2s" repeatCount="indefinite"/></circle>'
         '<text class="ti" x="52" y="44">Open to work</text><text class="mono" x="24" y="84">Internship or CDD</text>')
    p, _ = flow_pills(["Full-Stack", "AI", "IP networks", "DevOps"], 24, 98, 206, 3)
    s += p + '<text class="sb" x="24" y="186">Médéa, Algeria</text>'
    P.append(card(486, 0, 254, 200, s, 1.05, 5))
    s = title("Languages I speak", 4)
    for i, (n, lv, pct, k) in enumerate([("Arabic", "Native", 100, 5), ("French", "B1 (TCF)", 50, 3), ("English", "B2 (IELTS)", 66, 1)]):
        y = 78 + i * 38; d = 1.3 + i * .15; kt = f"0;{d/(d+.9):.4f};1"; fw = 196 * pct / 100
        s += (f'<text class="mono" x="24" y="{y}">{n}</text><text class="sb" x="220" y="{y}" text-anchor="end">{lv}</text>'
              f'<rect x="24" y="{y+9}" width="196" height="6" rx="3" fill="var(--c0)"/><rect x="24" y="{y+9}" width="{fw:.0f}" height="6" rx="3" fill="var(--k{k})"><animate attributeName="width" values="0;0;{fw:.0f}" keyTimes="{kt}" dur="{d+.9:.2f}s" fill="freeze"/></rect>')
    P.append(card(756, 0, 244, 200, s, 1.2, 4))
    tiles = [("Repositories", S["repos"], 1, "repo"), ("Stars earned", S["stars"], 4, "star"), ("Followers", S["followers"], 3, "people"),
             ("Commits this year", S["commits"], 5, "git-commit"), ("Pull requests", S["prs"], 2, "git-pull-request"), ("Issues", S["issues"], 6, "issue-opened")]
    s = title("Statistics", 1)
    for i, (l, v, k, ic) in enumerate(tiles):
        x = 24 + i * 160; d = 1.5 + i * .1; kt = f"0;{d/(d+.8):.4f};1"
        s += (f'<text x="{x}" y="92" style="font:700 34px {SANS};fill:var(--k{k})">{num(v)}</text>{octi(ic, x, 102, 14, f"var(--k{k})")}<text class="sb" x="{x+20}" y="114">{l}</text>'
              f'<rect x="{x}" y="124" width="100" height="4" rx="2" fill="var(--c0)"/><rect x="{x}" y="124" width="48" height="4" rx="2" fill="var(--k{k})"><animate attributeName="width" values="0;0;48" keyTimes="{kt}" dur="{d+.8:.2f}s" fill="freeze"/></rect>')
    P.append(card(0, 216, 1000, 146, s, 1.4, 2))
    wrap("overview.svg", 1000, 362, "Overview: skills, availability, languages and GitHub statistics", "".join(P))

# ------------------------------------------------------------------ skills (from the CV)
def skills():
    cats = [
        ("Web development", 1, "globe", [("MERN", "o:stack"), ("Next.js", "nextdotjs"), ("Laravel", "laravel"), ("Inertia.js", "inertia"), ("WordPress", "wordpress"),
                                         ("MySQL", "mysql"), ("PostgreSQL", "postgresql"), ("MongoDB", "mongodb"), ("Redis", "redis"), ("Cassandra", "apachecassandra"), ("Neo4j", "neo4j")]),
        ("Machine learning", 2, "cpu", ["Linear regression", "Logistic regression", "Decision tree", "Random forest", "K-means", "CNN", "RNN", "ViTs"]),
        ("DevOps", 5, "workflow", [("Docker", "docker"), ("Kubernetes", "kubernetes"), ("Git", "git"), ("GitHub", "github")]),
        ("Computer networks", 3, "server", ["OSI model", "TCP/IP", "IPv4/IPv6", "Static routing", "RIP", "OSPF", "EIGRP", "VLAN", "ACL", "STP", "DNS", "DHCP", "VoIP", "SIP", "TCP/IP sockets", "UDP"]),
        ("Telecommunications", 4, "pulse", ["Digital communications", "Signal processing", "GSM (2G)", "UMTS (3G)", "LTE (4G)", "FTTH", "MSAN", "NGN"]),
        ("Tools and software", 6, "terminal", [("Wireshark", "wireshark"), "GNS3", ("Cisco Packet Tracer", "cisco"), ("VirtualBox", "virtualbox"), ("VMware ESXi", "vmware"), "Openfiler",
                                              "MATLAB", "Simulink", "CST", ("VS Code", "visualstudiocode"), ("Postman", "postman"), "SQL Workbench", ("Jupyter Notebook", "jupyter"), ("Kaggle", "kaggle"), ("Docker Desktop", "docker")]),
    ]
    cw = (1000 - 32) / 3; lay = []
    for name, k, ic, items in cats:
        p, h = flow_pills(items, 24, 62, cw - 48, k, size=11, gap=6); lay.append((name, k, ic, p, h))
    rows = [lay[:3], lay[3:]]; body = ""; y = 0; delay = .3
    for r in rows:
        H = max(h for *_, h in r) + 62 + 22
        for i, (name, k, ic, p, h) in enumerate(r):
            s = f'<rect x="24" y="29" width="8" height="8" rx="2.5" fill="var(--k{k})"/><text class="ti" x="40" y="39">{name}</text>{octi(ic, cw-24-16, 25, 16, f"var(--k{k})")}{p}'
            body += card(i * (cw + 16), y, cw, H, s, delay + i * .12, k)
        y += H + 16; delay += .3
    wrap("skills.svg", 1000, int(y - 16), "Skills from my CV: web development, machine learning, DevOps, networks, telecommunications, tools", body)

# ------------------------------------------------------------------ activity
def activity():
    P = []
    win = weeks[-26:]
    mx = max([c for w in win for _, c in w] + [1])
    lvl = lambda c: 0 if c == 0 else min(4, 1 + int(3 * (c - 1) / max(mx - 1, 1) + .0001))
    gx, gy, cs, gp = 24, 76, 13, 4
    cells = ""
    for col, w in enumerate(win):
        for row, (_, c) in enumerate(w):
            d = .9 + col * .04; kt = f"0;{d/(d+.5):.4f};1"
            cells += f'<rect x="{gx+col*(cs+gp)}" y="{gy+row*(cs+gp)}" width="{cs}" height="{cs}" rx="3.5" fill="var(--c{lvl(c)})"><animate attributeName="opacity" values="0;0;1" keyTimes="{kt}" dur="{d+.5:.2f}s" fill="freeze"/></rect>'
    gw = 26 * (cs + gp) - gp; gh = 7 * (cs + gp) - gp
    s = title("Activity", 2, "Contributions over the last 26 weeks")
    s += (f'<clipPath id="gc"><rect x="{gx}" y="{gy}" width="{gw}" height="{gh}"/></clipPath>{cells}'
          f'<g clip-path="url(#gc)"><rect y="{gy}" width="70" height="{gh}" fill="url(#sw)"><animateTransform attributeName="transform" type="translate" values="{gx-70} 0;{gx+gw} 0;{gx+gw} 0" keyTimes="0;.55;1" dur="7s" begin="2.5s" repeatCount="indefinite"/></rect></g>'
          f'<text x="{gx+gw+24}" y="120" style="font:700 32px {SANS};fill:var(--k5)">{num(S["contrib"])}</text><text class="sb" x="{gx+gw+24}" y="142">past 12 months</text>')
    lg = "".join(f'<rect x="{gx+gw+24+i*16}" y="166" width="12" height="12" rx="3.5" fill="var(--c{i})"/>' for i in range(5))
    P.append(card(0, 0, 600, 200, s + lg, .3, 2))
    s = title("Top languages", 3)
    cx, cy, r, sw = 92, 114, 50, 20; C = 2 * math.pi * r; tot = sum(p for _, p in langs); off = 0; leg = ""
    for i, (n, p) in enumerate(langs):
        col = LC.get(n, LANG_FALLBACK[i % 5]); ln = C * p / tot; d = .7 + i * .15; kt = f"0;{d/(d+.9):.4f};1"
        s += (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-dasharray="{max(ln-2,1):.2f} {C-max(ln-2,1):.2f}" stroke-dashoffset="{-off:.2f}" transform="rotate(-90 {cx} {cy})">'
              f'<animate attributeName="stroke-dasharray" values="0 {C:.2f};0 {C:.2f};{max(ln-2,1):.2f} {C-max(ln-2,1):.2f}" keyTimes="{kt}" dur="{d+.9:.2f}s" fill="freeze"/></circle>')
        off += ln; y = 76 + i * 26
        leg += f'{lang_icon(n, 176, y-14, 16)}<text class="mono" x="200" y="{y}">{esc(cut(SHORT.get(n, n), 15))}</text><text class="sb" x="360" y="{y}" text-anchor="end">{p/tot*100:.0f}%</text>'
    P.append(card(616, 0, 384, 200, s + leg, .45, 3))
    s = title("Streak", 4)
    rr = 40; Cc = 2 * math.pi * rr; frac = min(1, cur / max(longest, 1))
    s += (f'<circle cx="84" cy="102" r="{rr}" fill="none" stroke="var(--c0)" stroke-width="9"/>'
          f'<circle cx="84" cy="102" r="{rr}" fill="none" stroke="var(--k4)" stroke-width="9" stroke-linecap="round" stroke-dasharray="{Cc*frac:.1f} {Cc:.1f}" transform="rotate(-90 84 102)"><animate attributeName="stroke-dasharray" values="0 {Cc:.1f};0 {Cc:.1f};{Cc*frac:.1f} {Cc:.1f}" keyTimes="0;.2;1" dur="2.2s" fill="freeze"/></circle>'
          f'<text x="84" y="108" text-anchor="middle" style="font:700 26px {SANS};fill:var(--tx)">{num(cur)}</text><text class="sb" x="84" y="123" text-anchor="middle">current</text>'
          f'<text class="sb" x="170" y="82">Longest streak</text><text x="170" y="108" style="font:700 24px {SANS};fill:var(--k4)">{num(longest)}</text>'
          f'<text class="sb" x="170" y="132">Active days</text><text x="170" y="158" style="font:700 24px {SANS};fill:var(--k5)">{num(active)}</text>')
    P.append(card(0, 216, 300, 170, s, .6, 4))
    s = title("Weekly rhythm", 5); base = 140; mxw = max(wk_tot) or 1
    for i, v in enumerate(wk_tot):
        x = 24 + i * 42; h = max(4, 78 * v / mxw)
        s += growbar(x, base, 28, h, f"var(--k{[1,2,3,4,5,6,1][i]})", .8 + i * .08) + f'<text class="sb" x="{x+14}" y="158" text-anchor="middle">{"SMTWTFS"[i]}</text>'
    P.append(card(316, 216, 330, 170, s, .75, 5))
    s = title("Top repositories", 6)
    for i, r in enumerate(toprepos):
        y = 70 + i * 38; desc = cut(r["description"] or "No description yet", 34); st = str(r["stargazers_count"])
        s += (f'{lang_icon(r["language"], 22, y-14, 16) if r["language"] else octi("repo", 22, y-14, 16, "var(--mu)")}<text class="mono" x="44" y="{y}">{esc(cut(r["name"], 22))}</text>'
              f'{octi("star", 314-len(st)*8-18, y-12, 13, "var(--k4)")}<text class="sb" x="314" y="{y}" text-anchor="end">{st}</text><text class="sb" x="44" y="{y+16}">{esc(desc)}</text>')
    P.append(card(662, 216, 338, 170, s, .9, 6))
    wrap("activity.svg", 1000, 386, "GitHub activity: heatmap, languages, streak, weekly rhythm and top repositories", "".join(P))

# ------------------------------------------------------------------ work
def work():
    P = []
    s = title("Focus areas", 1)
    for i, (t, sub, k) in enumerate([("Full-Stack web", "Next.js, MERN, Laravel", 1), ("Machine learning", "CNN, RNN, ViTs", 2), ("IP networking", "OSPF, EIGRP, VLAN", 3), ("DevOps", "Docker, Kubernetes", 5)]):
        x = 24 + (i % 2) * 222; y = 62 + (i // 2) * 62
        ico = [brand("react", x + 12, y + 14, 24), spark(x + 12, y + 14, "var(--k2)"), netglyph(x + 12, y + 14, "var(--k3)"), brand("kubernetes", x + 12, y + 14, 24)][i]
        s += (f'<rect x="{x}" y="{y}" width="210" height="52" rx="14" fill="var(--k{k})" fill-opacity=".14" stroke="var(--k{k})" stroke-opacity=".5"/>{ico}'
              f'<text class="mono" x="{x+46}" y="{y+23}" style="font-weight:700">{t}</text><text class="sb" x="{x+46}" y="{y+41}" style="font-size:11px">{sub}</text>')
    P.append(card(0, 0, 490, 190, s, .3, 1))
    # neural network
    s = title("Machine learning", 2, "Classic ML, CNNs, RNNs and Vision Transformers")
    layers = [4, 5, 5, 3]; xs = [70, 190, 310, 430]; top, bot = 84, 172
    pos = [[(xs[l], top + (bot - top) * (j + .5) / n) for j in range(n)] for l, n in enumerate(layers)]
    lines = ""; sig = ""; random.seed(5)
    for l in range(3):
        for a in pos[l]:
            for b in pos[l + 1]:
                lines += f'<line x1="{a[0]}" y1="{a[1]:.1f}" x2="{b[0]}" y2="{b[1]:.1f}" stroke="var(--mu)" stroke-opacity=".2"/>'
        for q in range(4):
            a = random.choice(pos[l]); b = random.choice(pos[l + 1]); dly = (l * .6 + q * .45) % 2.4
            sig += (f'<line x1="{a[0]}" y1="{a[1]:.1f}" x2="{b[0]}" y2="{b[1]:.1f}" stroke="var(--k{[1,3,4][l]})" stroke-width="2" stroke-linecap="round" stroke-dasharray="8 120">'
                    f'<animate attributeName="stroke-dashoffset" values="0;-128" dur="1.6s" begin="{dly:.2f}s" repeatCount="indefinite"/></line>')
    dots = ""
    for l, layer in enumerate(pos):
        for j, (x, y) in enumerate(layer):
            c = f"var(--k{[1,2,3,5][l]})"
            dots += (f'<circle cx="{x}" cy="{y:.1f}" r="7" fill="{c}"><animate attributeName="opacity" values=".45;1;.45" dur="2.4s" begin="{l*.5+j*.07:.2f}s" repeatCount="indefinite"/></circle>')
    for l, lb in enumerate(["input", "hidden", "hidden", "output"]):
        dots += f'<text class="sb" x="{xs[l]}" y="184" text-anchor="middle" style="font-size:11px">{lb}</text>'
    P.append(card(506, 0, 494, 190, s + lines + sig + dots, .45, 2))
    # real-estate platform
    s = title("Real estate listing platform", 6, "Developed and deployed at SARL Baladiyatech")
    p, _ = flow_pills([("Next.js", "nextdotjs"), ("Headless WordPress", "wordpress"), ("MySQL", "mysql"), ("Redis", "redis"), ("Docker", "docker")], 24, 86, 300, 6, size=11)
    s += p
    bld = ""
    for i, (bh, k) in enumerate([(46, 1), (74, 2), (58, 3), (84, 1), (52, 4), (68, 2)]):
        bx2 = 352 + i * 22
        bld += growbar(bx2, 170, 18, bh, f"var(--k{k})", .9 + i * .12, rx=3)
        for wy in range(0, int(bh) - 14, 14):
            for wx in (4, 10):
                bld += f'<rect x="{bx2+wx}" y="{170-bh+7+wy}" width="4" height="6" rx="1" fill="var(--card)" fill-opacity=".85"><animate attributeName="opacity" values="1;.25;1" dur="{2+((i+wy+wx)%5)*.6}s" begin="{(i*7+wy)%5}s" repeatCount="indefinite"/></rect>'
    P.append(card(0, 206, 492, 190, s + bld + '<rect x="340" y="170" width="146" height="2" rx="1" fill="var(--bd)"/>', .6, 6))
    # ECG project
    beat = "h22 l5,-6 l5,6 h10 l4,5 l7,-44 l7,56 l5,-17 h10 l6,-9 l6,9 h24"
    s = title("Final-year project", 3, "Cardiovascular disease prediction from ECG images")
    s += (f'<path d="M24 124 {beat*4}" pathLength="1000" fill="none" stroke="var(--bd)" stroke-width="3" stroke-linejoin="round"/>'
          f'<path d="M24 124 {beat*4}" pathLength="1000" fill="none" stroke="url(#ecg)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1000" stroke-dashoffset="1000">'
          '<animate attributeName="stroke-dashoffset" values="1000;0;0;-1000" keyTimes="0;.55;.8;1" dur="5s" repeatCount="indefinite"/></path>')
    x = 24
    for t, k in [("Deep learning", 5), ("CNN", 1), ("RNN", 2), ("ViT", 3)]:
        p, w = pill(x, 150, t, k); s += p; x += w + 8
    P.append(card(508, 206, 492, 190, s, .75, 3))
    # journey
    s = title("Journey", 2)
    steps = [("Dec 2020", "Engineering studies", "ENSTTIC, Oran", 1, "mortar-board"), ("Aug–Sep 2023", "Network intern", "Algérie Télécom", 2, "briefcase"),
             ("Jul 2024", "Telecom intern", "ATM Mobilis", 3, "briefcase"), ("Mar–Apr 2025", "Web developer intern", "SARL Baladiyatech", 4, "code"),
             ("June 2025", "Graduated engineer", "Telecom and digital tech", 5, "mortar-board")]
    s += ('<path d="M100 108 H900" stroke="var(--c0)" stroke-width="4" stroke-linecap="round"/>'
          '<path d="M100 108 H900" stroke="url(#jl)" stroke-width="4" stroke-linecap="round" pathLength="1000" stroke-dasharray="1000" stroke-dashoffset="1000"><animate attributeName="stroke-dashoffset" values="1000;1000;0" keyTimes="0;.15;1" dur="2.6s" fill="freeze"/></path>')
    for i, (yr, role, org, k, ic) in enumerate(steps):
        x = 100 + i * 200
        s += (f'<circle cx="{x}" cy="108" r="17" fill="var(--k{k})"/>{octi(ic, x-9, 99, 18, "var(--card)")}<circle cx="{x}" cy="108" r="17" fill="none" stroke="var(--k{k})"><animate attributeName="r" values="17;32" dur="2.6s" begin="{i*.5}s" repeatCount="indefinite"/><animate attributeName="stroke-opacity" values=".8;0" dur="2.6s" begin="{i*.5}s" repeatCount="indefinite"/></circle>'
              f'<text x="{x}" y="74" text-anchor="middle" style="font:700 18px {SANS};fill:var(--k{k})">{yr}</text>'
              f'<text x="{x}" y="152" text-anchor="middle" style="font:700 14px {SANS};fill:var(--tx)">{role}</text><text class="sb" x="{x}" y="172" text-anchor="middle" style="font-size:11.5px">{org}</text>')
    P.append(card(0, 412, 1000, 200, s, .9, 2))
    wrap("work.svg", 1000, 612, "Focus areas, machine learning, projects and journey", "".join(P))

# ------------------------------------------------------------------ stack + links
def stack():
    rows = [[("HTML", "html5"), ("CSS", "css3"), ("JavaScript", "javascript"), ("TypeScript", "typescript"), ("React", "react"), ("Next.js", "nextdotjs"),
             ("Tailwind", "tailwindcss"), ("Node.js", "nodedotjs"), ("Express", "express")],
            [("PHP", "php"), ("Laravel", "laravel"), ("Inertia.js", "inertia"), ("WordPress", "wordpress"), ("MySQL", "mysql"), ("PostgreSQL", "postgresql"),
             ("MongoDB", "mongodb"), ("Redis", "redis"), ("Cassandra", "apachecassandra"), ("Neo4j", "neo4j")],
            [("Docker", "docker"), ("Kubernetes", "kubernetes"), ("Git", "git"), ("GitHub", "github"), ("Postman", "postman"), ("VS Code", "visualstudiocode"),
             ("Linux", "linux"), ("Jupyter", "jupyter"), ("Kaggle", "kaggle"), ("Wireshark", "wireshark"), ("Cisco", "cisco"), ("VirtualBox", "virtualbox"), ("VMware", "vmware")]]
    s = title("Stack", 6) + '<clipPath id="sc"><rect x="0" y="52" width="1000" height="130"/></clipPath><g clip-path="url(#sc)">'
    for r, items in enumerate(rows):
        x = 0; row = ""; y = 54 + r * 44
        for it, slug in items:
            w = len(it) * 8 + 58
            row += (f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="34" rx="17" fill="var(--chip)" stroke="var(--bd)"/>{brand(slug, x+14, y+8, 18)}'
                    f'<text class="mono" x="{x+40:.0f}" y="{y+22}">{esc(it)}</text>')
            x += w + 12
        a2, b2 = (0, -x) if r % 2 == 0 else (-x, 0)
        s += (f'<g><animateTransform attributeName="transform" type="translate" from="{a2:.0f} 0" to="{b2:.0f} 0" dur="{34+r*5}s" repeatCount="indefinite"/>'
              f'{row}<g transform="translate({x:.0f} 0)">{row}</g></g>')
    s += '<rect x="0" y="52" width="70" height="130" fill="url(#fl)"/><rect x="930" y="52" width="70" height="130" fill="url(#fr)"/></g>'
    wrap("stack.svg", 1000, 196, "Technologies I use", card(0, 0, 1000, 196, s, .3, 6))

def links():
    for name, label, slug in [("github", "GitHub", "github"), ("linkedin", "LinkedIn", "linkedin"), ("email", "Email", "gmail")]:
        body = (f'<clipPath id="lc"><rect width="168" height="52" rx="26"/></clipPath><rect class="card" x=".5" y=".5" width="167" height="51" rx="25.5"/>'
                f'<g clip-path="url(#lc)"><rect y="0" width="60" height="52" fill="url(#sw)"><animateTransform attributeName="transform" type="translate" values="-60 0;168 0;168 0" keyTimes="0;.4;1" dur="4s" begin="{len(name)%3}s" repeatCount="indefinite"/></rect></g>'
                f'{brand(slug, 22, 14, 24)}<text x="58" y="32" style="font:700 16px {SANS};fill:var(--tx)">{label}</text>')
        (OUT / f"link-{name}.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 168 52" width="168" height="52" role="img" aria-label="{label}"><style>{FONT_BTN}{THEME}</style>{defs()}{body}</svg>', encoding="utf-8")

hero(); overview(); skills(); activity(); work(); stack(); links()
print("assets written | live data:", live)
