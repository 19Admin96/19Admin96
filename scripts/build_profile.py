#!/usr/bin/env python3
"""Global Green profile for 19Admin96: builds every SVG of the README into dist/.

Static cards (hero, about, stack, project, buttons) + live cards (stats, activity)
from the GitHub GraphQL API. Runs in GitHub Actions, no pip dependencies.
Needs scripts/icons.json (exported from the simple-icons npm package by the workflow).
Local test:  python3 scripts/build_profile.py --demo
"""
import datetime as dt
import json
import math
import os
import random
import sys
import urllib.request

LOGIN = os.environ.get('GH_LOGIN', '19Admin96')
OUT = os.environ.get('OUT_DIR', 'dist')
HERE = os.path.dirname(os.path.abspath(__file__))
ICONS = json.load(open(os.path.join(HERE, 'icons.json'), encoding='utf-8'))

# ── palette ────────────────────────────────────────────────────────────
I = '#10b981'; V = '#22c55e'; P = '#a3e635'; CY = '#2dd4bf'; TXT = '#f2fdf6'; MUT = '#86a394'; BG = '#040b07'
MONO = "'Geist Mono','JetBrains Mono',Consolas,'DejaVu Sans Mono',monospace"
SANS = "'Geist','Segoe UI',Inter,'Helvetica Neue',Arial,sans-serif"
DISP = "'Unbounded','Segoe UI Black','Arial Black',sans-serif"
FONT_DIR = os.environ.get('FONT_DIR', 'node_modules/@fontsource')
FONT_FILES = {'Unbounded': 'unbounded', 'Geist': 'geist-sans', 'Geist Mono': 'geist-mono'}
DEFS = (f'<linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{I}"/><stop offset=".5" stop-color="{V}"/><stop offset="1" stop-color="{P}"/></linearGradient>'
        f'<linearGradient id="bd" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".18"/><stop offset=".5" stop-color="#fff" stop-opacity=".04"/><stop offset="1" stop-color="{V}" stop-opacity=".35"/></linearGradient>'
        '<linearGradient id="tw" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#a7c4b3"/></linearGradient>'
        '<linearGradient id="cardbg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d1a13"/><stop offset="1" stop-color="#08110c"/></linearGradient>'
        '<filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="55"/></filter>'
        '<filter id="soft" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')

STACK = [('react', 'React'), ('typescript', 'TypeScript'), ('redux', 'Redux'), ('tailwindcss', 'Tailwind'),
         ('ionic', 'Ionic'), ('capacitor', 'Capacitor'), ('react', 'React Native'), ('tauri', 'Tauri'),
         ('nodedotjs', 'Node.js'), ('firebase', 'Firebase'), ('mongodb', 'MongoDB'), ('git', 'Git')]
ABBR = {'TypeScript': 'TS', 'JavaScript': 'JS', 'Python': 'PY', 'Kotlin': 'KT', 'Rust': 'RS', 'Dart': 'DT', 'Swift': 'SW'}


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def embed_fonts(body):
    """subset + inline (woff2/base64) every font/weight the card uses, so it renders the same everywhere"""
    import base64, html, io, re
    from fontTools import subset
    chars = set(html.unescape(''.join(re.findall(r'>([^<>]+)<', body)))) | set(' 0123456789')
    css = ''
    for w, fam in sorted(set(re.findall(r"font:(\d+) [\d.]+px '([^']+)'", body))):
        if fam not in FONT_FILES:
            continue
        pkg = FONT_FILES[fam]
        opts = subset.Options(); opts.flavor = 'woff2'; opts.layout_features = ['*']
        path = f'{FONT_DIR}/{pkg}/files/{pkg}-latin-{w}-normal.woff2'
        if not os.path.exists(path):
            continue
        font = subset.load_font(path, opts)
        sub = subset.Subsetter(opts); sub.populate(text=''.join(chars)); sub.subset(font)
        buf = io.BytesIO(); subset.save_font(font, buf, opts)
        css += f"@font-face{{font-family:'{fam}';font-weight:{w};src:url(data:font/woff2;base64,{base64.b64encode(buf.getvalue()).decode()}) format('woff2')}}"
    return f'<style>{css}</style>' if css else ''


def svg(w, h, body, defs=DEFS):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" fill="none">'
            f'<defs>{embed_fonts(body)}{defs}</defs>{body}</svg>')


def icon(name, x, y, size, color=None):
    ic = ICONS[name]
    return f'<g transform="translate({x:.1f},{y:.1f}) scale({size/24:.3f})"><path d="{ic["path"]}" fill="{color or "#" + ic["hex"]}"/></g>'


def card(x, y, w, h, r=20):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="url(#cardbg)"/>'
            f'<rect x="{x+.5}" y="{y+.5}" width="{w-1}" height="{h-1}" rx="{r}" stroke="url(#bd)"/>')


def label(x, y, t):
    return f'<text x="{x}" y="{y}" fill="{MUT}" style="font:500 11px {MONO};letter-spacing:2.5px">{esc(t.upper())}</text>'


# ── static cards ───────────────────────────────────────────────────────
def hero():
    W, H = 1000, 400
    blobs = ''
    for cx, cy, r, c, dx, dy, d in [(150, 60, 170, I, 60, 40, 14), (480, 380, 150, V, -70, -30, 17), (900, 60, 150, P, -50, 50, 12), (760, 420, 140, CY, 60, -40, 15)]:
        blobs += (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{c}" opacity=".4" filter="url(#blur)">'
                  f'<animate attributeName="cx" values="{cx};{cx+dx};{cx}" dur="{d}s" repeatCount="indefinite"/>'
                  f'<animate attributeName="cy" values="{cy};{cy+dy};{cy}" dur="{d}s" repeatCount="indefinite"/></circle>')
    gx, gy, R = 770, 205, 150
    defs = DEFS + (f'<clipPath id="hc"><rect width="{W}" height="{H}" rx="24"/></clipPath>'
                   '<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#fff" opacity=".06"/></pattern>'
                   '<radialGradient id="sph" cx="38%" cy="32%" r="75%"><stop offset="0" stop-color="#14532d"/><stop offset=".6" stop-color="#062414"/><stop offset="1" stop-color="#020a05"/></radialGradient>'
                   f'<radialGradient id="atm" cx="50%" cy="50%" r="50%"><stop offset=".85" stop-color="{V}" stop-opacity="0"/><stop offset=".93" stop-color="{V}" stop-opacity=".35"/><stop offset="1" stop-color="{V}" stop-opacity="0"/></radialGradient>'
                   f'<clipPath id="gc"><circle cx="{gx}" cy="{gy}" r="{R}"/></clipPath>')
    g = f'<circle cx="{gx}" cy="{gy}" r="{R+18}" fill="url(#atm)"/><circle cx="{gx}" cy="{gy}" r="{R}" fill="url(#sph)" stroke="{V}" stroke-opacity=".5"/><g clip-path="url(#gc)">'
    for lat in range(-60, 61, 30):
        y = gy - R * math.sin(math.radians(lat)); w = R * math.cos(math.radians(lat))
        g += f'<path d="M{gx-w:.1f},{y:.1f} H{gx+w:.1f}" stroke="{V}" stroke-opacity=".22"/>'
    T, N = 16, 13
    for m in range(6):
        vals = ';'.join(f'{abs(R*math.cos(math.radians(m*30 + 360*k/(N-1)))):.0f}' for k in range(N))
        g += f'<ellipse cx="{gx}" cy="{gy}" rx="{R}" ry="{R}" stroke="{V}" stroke-opacity=".22"><animate attributeName="rx" values="{vals}" dur="{T}s" repeatCount="indefinite"/></ellipse>'
    rr = random.Random(4)
    for lat in [-50, -35, -20, -5, 10, 25, 40, 55]:
        cl = math.cos(math.radians(lat)); y = gy - R * math.sin(math.radians(lat))
        for lon in range(0, 360, 20):
            if rr.random() < .45:
                continue
            xs, ops = [], []
            for k in range(N):
                a = math.radians(lon + 360*k/(N-1))
                xs.append(f'{gx + R*cl*math.sin(a):.0f}'); ops.append(f'{max(0, math.cos(a)):.1f}'.replace('0.', '.'))
            g += (f'<circle cy="{y:.1f}" r="2.2" fill="{P}"><animate attributeName="cx" values="{";".join(xs)}" dur="{T}s" repeatCount="indefinite"/>'
                  f'<animate attributeName="opacity" values="{";".join(ops)}" dur="{T}s" repeatCount="indefinite"/></circle>')
    g += '</g>'
    hx, hy = gx + 30, gy - 40
    for i, ((x, y), name) in enumerate([((gx-95, gy-70), 'EUROPE'), ((gx-110, gy+55), 'AFRICA'), ((gx+105, gy+30), 'ASIA'), ((gx+30, gy+110), 'GULF')]):
        d = f'M{hx},{hy} Q{(hx+x)/2:.0f},{min(hy, y)-70:.0f} {x},{y}'
        g += (f'<path d="{d}" stroke="{P}" stroke-width="1.6" stroke-dasharray="4 5" opacity=".8"><animate attributeName="stroke-dashoffset" values="18;0" dur="1s" repeatCount="indefinite"/></path>'
              f'<circle r="3.5" fill="#fff" filter="url(#soft)"><animateMotion path="{d}" dur="{2.2+i*.4:.1f}s" begin="{-i*.6:.1f}s" repeatCount="indefinite"/></circle>'
              f'<circle cx="{x}" cy="{y}" r="4" fill="{P}"/><text x="{x}" y="{y+18}" text-anchor="middle" fill="{TXT}" fill-opacity=".8" style="font:700 9px {MONO};letter-spacing:1.5px">{name}</text>')
    g += (f'<circle cx="{hx}" cy="{hy}" r="6" fill="{P}" filter="url(#soft)"/>'
          f'<circle cx="{hx}" cy="{hy}" r="6" stroke="{P}" stroke-width="2"><animate attributeName="r" values="6;22" dur="1.8s" repeatCount="indefinite"/><animate attributeName="opacity" values="1;0" dur="1.8s" repeatCount="indefinite"/></circle>'
          f'<rect x="{hx-37}" y="{hy+14}" width="74" height="22" rx="11" fill="#04140b" stroke="{P}" stroke-opacity=".7"/>'
          f'<text x="{hx}" y="{hy+29}" text-anchor="middle" fill="{P}" style="font:700 11px {MONO}">MARY, TM</text>')
    chips, x = '', 56
    for t, c in [('Web', CY), ('Android', P), ('iOS', '#fff'), ('Desktop', V)]:
        w = len(t) * 8 + 34
        chips += (f'<rect x="{x}" y="318" width="{w}" height="30" rx="15" fill="#fff" fill-opacity=".05" stroke="#fff" stroke-opacity=".14"/>'
                  f'<circle cx="{x+15}" cy="333" r="4" fill="{c}"/><text x="{x+25}" y="338" fill="{TXT}" style="font:600 13px {SANS}">{t}</text>')
        x += w + 8
    body = (f'<g clip-path="url(#hc)"><rect width="{W}" height="{H}" fill="{BG}"/>{blobs}'
            f'<rect width="{W}" height="{H}" fill="{BG}" opacity=".4"/><rect width="{W}" height="{H}" fill="url(#dots)"/>'
            '<rect x="56" y="62" width="316" height="32" rx="16" fill="#ffffff" fill-opacity=".06" stroke="#fff" stroke-opacity=".14"/>'
            f'<circle cx="74" cy="78" r="4" fill="{P}"><animate attributeName="opacity" values="1;.3;1" dur="2s" repeatCount="indefinite"/></circle>'
            f'<text x="86" y="83" fill="{TXT}" style="font:600 13px {SANS};letter-spacing:.5px">Available for freelance &amp; collaboration</text>'
            f'<text x="54" y="160" fill="url(#tw)" style="font:800 58px {DISP};letter-spacing:1px">ZERRATUN</text>'
            f'<text x="56" y="208" fill="url(#g)" style="font:600 22px {DISP}">Built in Turkmenistan.</text>'
            f'<text x="56" y="244" fill="url(#g)" style="font:600 22px {DISP}">Made for every platform.</text>'
            f'<text x="56" y="286" fill="{MUT}" style="font:500 16px {SANS}">Cross-platform engineer · React · Ionic · Tauri</text>'
            + chips + g + f'</g><rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="24" stroke="url(#bd)"/>')
    return svg(W, H, body, defs)


def section(t):
    return svg(1000, 56, f'<text x="0" y="36" fill="{TXT}" style="font:700 22px {DISP}">{esc(t)}</text>'
                         '<rect x="0" y="48" width="44" height="3" rx="1.5" fill="url(#g)"/>')


def about():
    W, H = 1000, 300
    b = card(1, 1, W - 2, H - 2, 22) + label(36, 48, 'About me')
    b += (f'<text x="36" y="94" fill="{TXT}" style="font:600 22px {DISP}">Building software for markets</text>'
          f'<text x="36" y="128" fill="url(#g)" style="font:600 22px {DISP}">others overlook.</text>')
    for i, t in enumerate(['Based in Mary, Turkmenistan. I design and ship products —', 'HR platforms, POS systems, everyday apps — from one', 'TypeScript codebase to every screen.']):
        b += f'<text x="36" y="{170+i*24}" fill="{MUT}" style="font:500 16px {SANS}">{t}</text>'
    items = [('Web', 'React · Redux · Tailwind', CY), ('Mobile', 'Ionic · Capacitor · RN', '#3ddc84'),
             ('Desktop', 'Tauri · Win · macOS · Linux', I), ('Backend', 'Node · Firebase · Mongo', P)]
    for i, (t, s, c) in enumerate(items):
        x, y = 560 + (i % 2) * 210, 40 + (i // 2) * 124
        b += (f'<rect x="{x}" y="{y}" width="196" height="108" rx="16" fill="#fff" fill-opacity=".03" stroke="#fff" stroke-opacity=".08"/>'
              f'<rect x="{x+18}" y="{y+18}" width="32" height="32" rx="10" fill="{c}" fill-opacity=".16"/><circle cx="{x+34}" cy="{y+34}" r="6" fill="{c}"/>'
              f'<text x="{x+18}" y="{y+76}" fill="{TXT}" style="font:700 16px {SANS}">{t}</text>'
              f'<text x="{x+18}" y="{y+96}" fill="{MUT}" style="font:500 12px {SANS}">{esc(s)}</text>')
    return svg(W, H, b)


def stack():
    W, cols, tw, th, gap = 1000, 6, 154, 118, 15
    H = 2 * (th + gap) + 4
    x0 = (W - (cols * tw + (cols - 1) * gap)) / 2
    pos = [(x0 + (i % cols) * (tw + gap), 2 + (i // cols) * (th + gap)) for i in range(len(STACK))]
    defs = DEFS + ('<linearGradient id="sh" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                   '<stop offset=".5" stop-color="#fff" stop-opacity=".09"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
                   '<clipPath id="tiles">' + ''.join(f'<rect x="{x}" y="{y}" width="{tw}" height="{th}" rx="18"/>' for x, y in pos) + '</clipPath>')
    b = ''
    for (ic, name), (cx, cy) in zip(STACK, pos):
        hx = '#' + ICONS[ic]['hex']
        b += (card(cx, cy, tw, th, 18) + f'<circle cx="{cx+tw/2}" cy="{cy+44}" r="26" fill="{hx}" opacity=".18" filter="url(#soft)"/>'
              + icon(ic, cx + tw / 2 - 18, cy + 26, 36) +
              f'<text x="{cx+tw/2}" y="{cy+96}" text-anchor="middle" fill="{TXT}" style="font:600 14px {SANS}">{esc(name)}</text>')
    b += (f'<g clip-path="url(#tiles)"><rect x="-300" y="0" width="300" height="{H}" fill="url(#sh)" transform="skewX(-20)">'
          '<animate attributeName="x" values="-300;1300" dur="4.5s" repeatCount="indefinite"/></rect></g>')
    return svg(W, H, b, defs)


def project():
    W, H = 1000, 300
    defs = DEFS + '<clipPath id="pc"><rect x="1" y="1" width="998" height="298" rx="22"/></clipPath>'
    b = (f'<g clip-path="url(#pc)">{card(1, 1, W-2, H-2, 22)}<circle cx="850" cy="150" r="140" fill="{I}" opacity=".35" filter="url(#blur)"/></g>'
         f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="22" stroke="url(#g)" stroke-opacity=".6"/>' + label(36, 48, 'Featured project'))
    b += (f'<text x="36" y="104" fill="url(#tw)" style="font:800 38px {DISP}">MeteoMax</text>'
          f'<text x="36" y="140" fill="{MUT}" style="font:500 17px {SANS}">A beautiful cross-platform weather app.</text>'
          f'<text x="36" y="164" fill="{MUT}" style="font:500 17px {SANS}">PWA + native Android from a single codebase.</text>')
    x = 36
    for t in ['12 languages', 'Air quality', 'Islamic features']:
        w = len(t) * 7.6 + 30
        b += (f'<rect x="{x}" y="186" width="{w}" height="30" rx="15" fill="#fff" fill-opacity=".05" stroke="#fff" stroke-opacity=".12"/>'
              f'<text x="{x+w/2}" y="206" text-anchor="middle" fill="{TXT}" style="font:600 13px {SANS}">{t}</text>')
        x += w + 10
    for k, ic in enumerate(['react', 'ionic', 'capacitor', 'typescript', 'pwa']):
        b += icon(ic, 36 + k * 38, 240, 22)
    px, py = 770, 34
    b += (f'<rect x="{px}" y="{py}" width="160" height="236" rx="28" fill="#08110c" stroke="#fff" stroke-opacity=".18" stroke-width="1.5"/>'
          f'<rect x="{px+60}" y="{py+12}" width="40" height="8" rx="4" fill="#000"/>'
          f'<circle cx="{px+80}" cy="{py+78}" r="24" fill="#fbbf24" filter="url(#soft)"><animate attributeName="r" values="22;26;22" dur="4s" repeatCount="indefinite"/></circle>'
          f'<text x="{px+80}" y="{py+152}" text-anchor="middle" fill="{TXT}" style="font:300 44px {SANS}">28°</text>'
          f'<text x="{px+80}" y="{py+176}" text-anchor="middle" fill="{MUT}" style="font:500 12px {SANS}">Mary · Sunny</text>'
          f'<rect x="{px+22}" y="{py+196}" width="116" height="18" rx="9" fill="#fff" fill-opacity=".06"/>'
          f'<text x="{px+80}" y="{py+209}" text-anchor="middle" fill="#3ddc84" style="font:600 10px {SANS}">AQI 42 · Good</text>')
    return svg(W, H, b, defs)


def button(ic, t, prim):
    x, y, bw, bh = 8, 8, 200, 56
    if prim:
        b = f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="28" fill="url(#g)" filter="url(#soft)"/>'
    else:
        b = (f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="28" fill="#0b1510"/>'
             f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="28" fill="#fff" fill-opacity=".05" stroke="#fff" stroke-opacity=".16"/>')
    gx = x + (bw - (34 + len(t) * 9.2)) / 2
    b += icon(ic, gx, y + 17, 22, '#fff') + f'<text x="{gx+34:.1f}" y="{y+34}" fill="#fff" style="font:600 16px {SANS}">{t}</text>'
    return svg(216, 72, b)


def footer():
    return svg(1000, 100, f'<text x="500" y="44" text-anchor="middle" fill="url(#tw)" style="font:700 22px {DISP}">Let\'s build something together.</text>'
                          f'<text x="500" y="76" text-anchor="middle" fill="{MUT}" style="font:500 15px {SANS}">Open to freelance &amp; collaboration · Mary, Turkmenistan · UTC+5</text>')


# ── live data ──────────────────────────────────────────────────────────
QUERY = '''query($login:String!,$from:DateTime!,$to:DateTime!){
  user(login:$login){
    repositories(ownerAffiliations:OWNER,isFork:false,privacy:PUBLIC,first:100){
      totalCount
      nodes{ name languages(first:10,orderBy:{field:SIZE,direction:DESC}){ edges{ size node{ name color } } } }
    }
    contributionsCollection(from:$from,to:$to){
      contributionCalendar{ totalContributions weeks{ contributionDays{ date contributionCount } } }
    }
  }
}'''


def fetch():
    now = dt.datetime.now(dt.timezone.utc)
    body = json.dumps({'query': QUERY, 'variables': {'login': LOGIN, 'from': (now - dt.timedelta(days=365)).isoformat(), 'to': now.isoformat()}}).encode()
    req = urllib.request.Request('https://api.github.com/graphql', data=body, headers={
        'Authorization': f'bearer {os.environ["GITHUB_TOKEN"]}', 'Content-Type': 'application/json', 'User-Agent': 'profile-cards'})
    data = json.load(urllib.request.urlopen(req, timeout=30))
    if data.get('errors'):
        raise SystemExit(f'GraphQL error: {data["errors"]}')
    u = data['data']['user']
    langs = {}
    for repo in u['repositories']['nodes']:
        if repo['name'] == LOGIN:  # skip the profile repo itself
            continue
        for e in repo['languages']['edges']:
            n = e['node']['name']
            langs.setdefault(n, [0, e['node']['color'] or '#8b949e'])
            langs[n][0] += e['size']
    cal = u['contributionsCollection']['contributionCalendar']
    days = sorted((d['date'], d['contributionCount']) for w in cal['weeks'] for d in w['contributionDays'])
    return {'repos': u['repositories']['totalCount'], 'total': cal['totalContributions'], 'langs': langs, 'days': days}


def demo():
    real = {'2026-09-13': 8, '2026-09-14': 5, '2026-09-15': 5, '2026-09-16': 9, '2026-09-17': 8, '2026-09-20': 2, '2026-09-21': 5, '2026-09-22': 6,
            '2026-09-23': 5, '2026-09-24': 1, '2026-09-27': 1, '2026-09-28': 9, '2026-09-29': 23, '2026-09-30': 23, '2026-10-01': 13}
    base = dt.date(2026, 10, 4)
    days = [((base - dt.timedelta(days=i)).isoformat(), 0) for i in range(365, -1, -1)]
    return {'repos': 2, 'total': 208, 'days': [(d, real.get(d, 0)) for d, _ in days],
            'langs': {'TypeScript': [406594, '#3178c6'], 'JavaScript': [95736, '#f1e05a'], 'CSS': [35113, '#663399'], 'HTML': [13246, '#e34c26'], 'Java': [1300, '#b07219']}}


def stats_card(d):
    tot = sum(v[0] for v in d['langs'].values()) or 1
    langs = sorted(((n, v[0] * 100 / tot, v[1]) for n, v in d['langs'].items()), key=lambda x: -x[1])
    top = langs[:5]
    if len(langs) > 5:
        top.append(('Other', sum(p for _, p, _ in langs[5:]), '#5b6b62'))
    tn = langs[0][0] if langs else '—'
    rows = [('Contributions', str(d['total']), 'last 12 months'), ('Public repos', str(d['repos']), 'open source'),
            ('Top language', ABBR.get(tn, tn[:3].upper()), f'{tn} {langs[0][1]:.0f}%' if langs else ''),
            ('Platforms', '3', 'web · mobile · desktop')]
    b = card(1, 1, 488, 248) + card(511, 1, 488, 248) + label(30, 44, 'Overview') + label(540, 44, 'Languages')
    for i, (k, v, sub) in enumerate(rows):
        x, y = 30 + (i % 2) * 230, 76 + (i // 2) * 84
        off = len(v) * 31 + 16
        b += (f'<text x="{x}" y="{y+38}" fill="url(#g)" style="font:800 34px {DISP}">{esc(v)}</text>'
              f'<text x="{x+off}" y="{y+20}" fill="{TXT}" style="font:600 14px {SANS}">{esc(k)}</text>'
              f'<text x="{x+off}" y="{y+38}" fill="{MUT}" style="font:500 12px {SANS}">{esc(sub)}</text>')
    x = 540.0
    b += '<clipPath id="bar"><rect x="540" y="70" width="430" height="12" rx="6"/></clipPath><g clip-path="url(#bar)">'
    for n, p, c in top:
        b += f'<rect x="{x:.1f}" y="70" width="{430*p/100+1:.1f}" height="12" fill="{c}"/>'
        x += 430 * p / 100
    b += '</g>'
    for i, (n, p, c) in enumerate(top):
        xx, yy = 540 + (i % 2) * 220, 118 + (i // 2) * 34
        b += (f'<circle cx="{xx+6}" cy="{yy-5}" r="6" fill="{c}"/><text x="{xx+20}" y="{yy}" fill="{TXT}" style="font:600 14px {SANS}">{esc(n)}</text>'
              f'<text x="{xx+200}" y="{yy}" text-anchor="end" fill="{MUT}" style="font:500 13px {SANS}">{p:.1f}%</text>')
    return svg(1000, 250, b)


def activity_card(d, n=31):
    days = d['days'][-n:]
    vals = [c for _, c in days]
    x0, y0, w, h = 40, 80, 920, 130
    mx = max(vals) or 1
    pts = [(x0 + i * w / (len(vals) - 1), y0 + h - (v / mx) * h) for i, v in enumerate(vals)]
    line = f'M{pts[0][0]:.1f},{pts[0][1]:.1f}'
    for i in range(1, len(pts)):
        (xa, ya), (xb, yb) = pts[i - 1], pts[i]
        cx = (xa + xb) / 2
        line += f' C{cx:.1f},{ya:.1f} {cx:.1f},{yb:.1f} {xb:.1f},{yb:.1f}'
    area = line + f' L{x0+w},{y0+h} L{x0},{y0+h} Z'
    defs = DEFS + (f'<linearGradient id="ar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{V}" stop-opacity=".35"/><stop offset="1" stop-color="{V}" stop-opacity="0"/></linearGradient>'
                   '<clipPath id="reveal"><rect x="0" y="0" width="0" height="400"><animate attributeName="width" values="0;1000" dur="3s" fill="freeze"/></rect></clipPath>')
    b = card(1, 1, 998, 268, 22) + label(36, 46, f'Contribution activity · last {n} days')
    b += f'<text x="964" y="46" text-anchor="end" fill="{P}" style="font:700 13px {SANS}">{sum(vals)} contributions</text>'
    for k in range(4):
        b += f'<path d="M40,{80+k*43.3:.0f} H960" stroke="#fff" stroke-opacity=".05"/>'
    b += (f'<path d="{area}" fill="url(#ar)" clip-path="url(#reveal)"/>'
          f'<path d="{line}" stroke="url(#g)" stroke-width="3" stroke-linecap="round" filter="url(#soft)" clip-path="url(#reveal)"/>')
    for v, (x, y) in zip(vals, pts):
        if v and v >= mx * 0.5:
            b += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{BG}" stroke="#fff" stroke-width="2"/>'
    first = dt.date.fromisoformat(days[0][0])
    b += (f'<text x="40" y="244" fill="{MUT}" style="font:500 12px {SANS}">{first.strftime("%b")} {first.day}</text>'
          f'<text x="960" y="244" text-anchor="end" fill="{MUT}" style="font:500 12px {SANS}">Today</text>')
    return svg(1000, 270, b, defs)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    files = {'hero.svg': hero(), 'h-about.svg': section('About'), 'about.svg': about(), 'h-stack.svg': section('Tech stack'),
             'stack.svg': stack(), 'h-stats.svg': section('GitHub stats'), 'h-work.svg': section('Featured work'),
             'project.svg': project(), 'h-contact.svg': section('Get in touch'), 'contact-footer.svg': footer(),
             'btn-portfolio.svg': button('vercel', 'Portfolio', True), 'btn-telegram.svg': button('telegram', 'Telegram', False),
             'btn-email.svg': button('gmail', 'Email', False), 'btn-github.svg': button('github', 'GitHub', False)}
    data = demo() if '--demo' in sys.argv else fetch()  # fails the job on API errors -> last good cards stay online
    files['stats.svg'] = stats_card(data)
    files['activity.svg'] = activity_card(data)
    for name, s in files.items():
        open(os.path.join(OUT, name), 'w', encoding='utf-8').write(s)
    print(f'{len(files)} cards written to {OUT}/')
