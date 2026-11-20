#!/usr/bin/env python3
"""Ramometro web · aggiorna borsa del rame, cambio e notizie (eseguito da GitHub Actions, gratis).

uso: python3 mercato.py data/base.json data/market.json

- base.json: i dati di mercato incorporati nell'app (li scrive build.py a ogni pubblicazione).
- market.json: base + borsa LME (prezzo cash e scorte, Westmetall), cambio euro-dollaro (BCE tramite
  Frankfurter) e titoli delle notizie sul rame (MINING.COM). Nessun dato personale, nessuna AI.
Se una fonte non risponde resta l'ultimo dato buono; se manca la borsa il file non cambia.
"""
import sys, json, re, html, datetime, urllib.request, email.utils, os

BASE, OUT = sys.argv[1], sys.argv[2]
UA = {'User-Agent': 'Mozilla/5.0 (compatible; Ramometro/1.0; +https://sir245cu.github.io)'}
WM = 'https://www.westmetall.com/en/markdaten.php?action=table&field=LME_Cu_cash'
FX = 'https://api.frankfurter.app/latest?from=EUR&to=USD'
RSS = ['https://www.mining.com/commodity/copper/feed/']
MO = {m: i + 1 for i, m in enumerate(['january', 'february', 'march', 'april', 'may', 'june', 'july',
                                      'august', 'september', 'october', 'november', 'december'])}
MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre',
        'ottobre', 'novembre', 'dicembre']


def get(u):
    req = urllib.request.Request(u, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode('utf-8', 'replace')


def lme():
    t = html.unescape(re.sub(r'<[^>]+>', ' ', get(WM)))
    rows = {}
    for m in re.finditer(r'(\d{1,2})\.\s*([A-Za-z]+)\s+(\d{4})\s+([\d,]+(?:\.\d+)?)\s+([\d,]+(?:\.\d+)?)\s+([\d,]+)', t):
        mo = MO.get(m.group(2).lower())
        if not mo:
            continue
        d = '%s-%02d-%02d' % (m.group(3), mo, int(m.group(1)))
        cash = float(m.group(4).replace(',', ''))
        stock = int(m.group(6).replace(',', ''))
        if 3000 < cash < 40000:
            rows[d] = (cash, stock)
    return sorted(((d, v[0], v[1]) for d, v in rows.items()), reverse=True)


def fx():
    j = json.loads(get(FX))
    v = j['rates']['USD']
    if not 0.5 < v < 2:
        raise ValueError('cambio fuori scala')
    return v, j['date']


def news():
    out = []
    for u in RSS:
        x = get(u)
        for it in re.findall(r'<item>(.*?)</item>', x, re.S)[:20]:
            def tag(n):
                m = re.search(r'<%s[^>]*>(.*?)</%s>' % (n, n), it, re.S)
                if not m:
                    return ''
                v = m.group(1).strip()
                v = re.sub(r'^<!\[CDATA\[(.*)\]\]>$', r'\1', v, flags=re.S)
                return html.unescape(re.sub(r'<[^>]+>', ' ', v)).strip()
            t, link, pub = tag('title'), tag('link'), tag('pubDate')
            desc = re.sub(r'\s+', ' ', tag('description'))
            who = tag('dc:creator')
            try:
                d = email.utils.parsedate_to_datetime(pub).date().isoformat()
            except Exception:
                continue
            if not t or not link.startswith('https://') or len(link) > 500 or re.search(r'[\s<>"\']', link):
                continue
            src = 'MINING.COM' + (' (%s)' % who if who and len(who) < 40 and who.lower() != 'mining.com' else '')
            x700 = (desc or t)[:690]
            out.append({'d': d, 't': re.sub(r'[<>]', '', t)[:290], 's': src[:110], 'l': 'EN', 'u': link, 'x': re.sub(r'[<>]', '', x700)})
    return out


def it_date(d):
    y, m, g = d.split('-')
    return '%d %s' % (int(g), MESI[int(m) - 1])


def main():
    base = json.load(open(BASE, encoding='utf-8'))
    old = None
    if os.path.exists(OUT):
        try:
            old = json.load(open(OUT, encoding='utf-8'))
        except Exception:
            old = None
    o = json.loads(json.dumps(base))
    # se il file vecchio è più recente della base, si riparte da lì (notizie e cambio già letti)
    if old and old.get('asof', '') >= base.get('asof', '') and old.get('base') == base.get('asof'):
        for k in ('usdPerEur', 'fxSrc', 'news', 'hist'):
            if k in old:
                o[k] = old[k]
        o['spot'] = old.get('spot', o['spot'])
        o['series'] = old.get('series', o['series'])
    try:
        rows = lme()
    except Exception as e:
        print('borsa non leggibile:', e)
        rows = []
    if not rows:
        print('borsa vuota: file invariato')
        return 0
    d0, p0, s0 = rows[0]
    S = o['spot']
    if d0 < S['date']:
        print('borsa più vecchia della base: file invariato')
        return 0
    S['usdT'], S['date'] = round(p0), d0
    S['stockLme'], S['stockDate'] = s0, d0
    S['stockNote'] = 'scorte LME al %s' % it_date(d0)
    if p0 > S['record']:
        S['record'], S['recordDate'] = round(p0), d0
    last = rows[:30]
    lo = min(last, key=lambda r: r[1])
    S['low'] = round(lo[1])
    S['lowNote'] = '%s, minimo degli ultimi %d giorni di borsa' % (it_date(lo[0]), len(last))
    y = d0[:4]
    ytd = [r[1] for r in rows if r[0][:4] == y]
    if len(ytd) >= 20:
        prev = base['spot']['ytdAvg'] / (1 + base['spot']['ytdPct'] / 100)
        S['ytdAvg'] = round(sum(ytd) / len(ytd))
        S['ytdPct'] = round((S['ytdAvg'] / prev - 1) * 100, 1)
    # medie mensili ($/t) dei mesi chiusi, dalla serie che parte da gennaio 2025
    ser = o['series']
    months = {}
    for d, p, _ in rows:
        months.setdefault(d[:7], []).append(p)
    for ym, v in sorted(months.items()):
        if ym >= d0[:7]:
            continue  # mese in corso
        i = (int(ym[:4]) - 2025) * 12 + int(ym[5:7]) - 1
        if 0 <= i < len(ser):
            ser[i] = round(sum(v) / len(v))
        elif i == len(ser) and len(ser) < 60:
            ser.append(round(sum(v) / len(v)))
    o['hist'] = [[d, round(p)] for d, p, _ in rows[:12]]
    try:
        v, fd = fx()
        o['usdPerEur'] = round(v, 4)
        o['fxSrc'] = 'BCE (Frankfurter), %s' % '/'.join(reversed(fd.split('-')))
    except Exception as e:
        print('cambio non leggibile:', e)
    try:
        nw = news()
        if nw:
            seen, merged = set(), []
            for n in nw + o['news']:
                if n['u'] in seen:
                    continue
                seen.add(n['u'])
                merged.append(n)
            merged.sort(key=lambda n: n['d'], reverse=True)
            o['news'] = merged[:20]
    except Exception as e:
        print('notizie non leggibili:', e)
    today = datetime.datetime.utcnow().date().isoformat()
    o['asof'] = max(today, base['asof'])
    o['updatedAt'] = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
    o['base'] = base['asof']
    # controlli come nell'app (validate): se qualcosa non torna, il file non cambia
    assert 3000 < S['usdT'] < 40000 and 0.3 < o['usdPerEur'] < 3
    assert 22 <= len(o['series']) <= 60 and 5 <= len(o['news']) <= 30
    for n in o['news']:
        assert len(n['t']) <= 300 and len(n['s']) <= 120 and len(n['x']) <= 700
    json.dump(o, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('ok', S['date'], S['usdT'], '$/t', o['usdPerEur'], len(o['news']), 'notizie')
    return 0


if __name__ == '__main__':
    sys.exit(main())
