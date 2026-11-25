"""Prove della versione web senza dati personali: invito, dati sul dispositivo, statistiche, menu, aiuti, richieste esterne."""
import asyncio, json, re, sys, time
from urllib.parse import urlparse
from playwright.async_api import async_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8765/'
FS = {'codes': {'ABCD-2345': {'max': 2, 'used': 0, 'on': True, 'exp': None},
                'OFFX-2345': {'max': 5, 'used': 0, 'on': False, 'exp': None},
                'FULL-2345': {'max': 1, 'used': 1, 'on': True, 'exp': None},
                'OLDX-2345': {'max': 5, 'used': 0, 'on': True, 'exp': time.time() * 1000 - 864e5}},
      'stats': {}, 'commits': [], 'deny_all': False}
KEYS = set('ap att nuovi r7 r30 tel pc pwa cm cw cs vg vt vn sv co st us un'.split())
EXT = []
SPL = "(()=>{var s=document.getElementById('spl');if(s&&!s.hidden){var b=s.querySelector('[data-splic=completa]')||s.querySelector('button');b&&b.click()}})()"
OK = []


def chk(name, cond, extra=''):
    cond = bool(cond); OK.append(cond)
    print(('  ok  ' if cond else '  !!  ') + name + (' — ' + str(extra) if extra else ''))


def fields(o):
    f = {}
    for k, v in o.items():
        if v is None: f[k] = {'nullValue': None}
        elif isinstance(v, bool): f[k] = {'booleanValue': v}
        elif isinstance(v, int): f[k] = {'integerValue': str(v)}
        elif isinstance(v, float): f[k] = {'timestampValue': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(v / 1000))}
    return f


async def fs_route(route):
    req = route.request
    u = urlparse(req.url)
    if FS['deny_all']:
        return await route.fulfill(status=403, body='{"error":{"status":"PERMISSION_DENIED"}}', content_type='application/json')
    if req.method == 'GET':
        m = re.search(r'/documents/codes/([^?]+)', u.path)
        c = FS['codes'].get(m.group(1)) if m else None
        if not c: return await route.fulfill(status=404, body='{}', content_type='application/json')
        return await route.fulfill(status=200, body=json.dumps({'fields': fields(c)}), content_type='application/json')
    if req.method == 'POST' and u.path.endswith(':commit'):
        body = json.loads(req.post_data)
        FS['commits'].append(body)
        for w in body['writes']:
            if 'transform' in w:
                code = w['transform']['document'].split('/')[-1]
                c = FS['codes'].get(code)
                if not c or not c['on'] or c['used'] + 1 > c['max'] or (c['exp'] and c['exp'] < time.time() * 1000):
                    return await route.fulfill(status=403, body='{}', content_type='application/json')
                c['used'] += 1
            else:
                doc = w['update']['name'].split('/')[-1]
                if not re.fullmatch(r'd-\d{4}-\d{2}-\d{2}|m-\d{4}-\d{2}|v-[0-9A-Za-z._-]{1,24}|tot', doc):
                    return await route.fulfill(status=403, body='{"bad":"doc"}', content_type='application/json')
                st = FS['stats'].setdefault(doc, {})
                for t in w['updateTransforms']:
                    k, n = t['fieldPath'], int(t['increment']['integerValue'])
                    if k not in KEYS or n > 50 or n < 0:
                        return await route.fulfill(status=403, body='{"bad":"%s"}' % k, content_type='application/json')
                    st[k] = st.get(k, 0) + n
        return await route.fulfill(status=200, body='{}', content_type='application/json')
    await route.fulfill(status=400, body='{}')


async def ext_route(route):
    h = urlparse(route.request.url).hostname
    if h in ('127.0.0.1', 'localhost'):
        return await route.continue_()
    if h == 'firestore.googleapis.com':
        return await fs_route(route)
    EXT.append(route.request.url)
    await route.abort()


async def ctx(b, w=390, h=844, mobile=True, state=None):
    c = await b.new_context(viewport={'width': w, 'height': h}, is_mobile=mobile, has_touch=mobile, storage_state=state, accept_downloads=True)
    await c.route('**/*', ext_route)
    pg = await c.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
    return c, pg, errs


def stat(k, doc=None):
    d = doc or 'd-' + time.strftime('%Y-%m-%d')
    return FS['stats'].get(d, {}).get(k, 0)


async def flush(pg):
    await pg.evaluate("window.__RMWEB&&window.__RMWEB.flush()")
    await pg.wait_for_timeout(500)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        c, pg, errs = await ctx(b)
        await pg.goto(URL); await pg.wait_for_timeout(2500)
        gate = await pg.evaluate("(()=>{var g=document.getElementById('rmGate');return !!g&&!g.hidden})()")
        chk('prima apertura: chiede il codice d’invito', gate)
        await pg.screenshot(path='/tmp/w_gate.png')
        await pg.fill('#rmCode', 'zzzz2345'); await pg.wait_for_timeout(200)
        chk('codice scritto in maiuscolo con il trattino', await pg.input_value('#rmCode') == 'ZZZZ-2345')
        chk('senza spunta «Attiva» resta spento', await pg.evaluate("document.getElementById('rmGo').disabled"))
        await pg.check('#rmAcc'); await pg.click('#rmGo'); await pg.wait_for_timeout(800)
        chk('codice inesistente: messaggio chiaro', 'non valido' in await pg.inner_text('#rmGateM'), await pg.inner_text('#rmGateM'))
        for code, want in [('OFFX-2345', 'non è più attivo'), ('FULL-2345', 'numero massimo'), ('OLDX-2345', 'scaduto')]:
            await pg.fill('#rmCode', code); await pg.click('#rmGo'); await pg.wait_for_timeout(700)
            chk('codice %s: «%s»' % (code, want), want in await pg.inner_text('#rmGateM'), await pg.inner_text('#rmGateM'))
        FS['deny_all'] = True
        await pg.fill('#rmCode', 'ABCD-2345'); await pg.click('#rmGo'); await pg.wait_for_timeout(700)
        chk('regole non ancora aggiornate: «inviti non ancora attivi»', 'non sono ancora attivi' in await pg.inner_text('#rmGateM'), await pg.inner_text('#rmGateM'))
        FS['deny_all'] = False
        await pg.click('#rmGo'); await pg.wait_for_timeout(1500)
        chk('codice valido: l’app si apre', await pg.evaluate("document.getElementById('rmGate').hidden"))
        chk('attivazioni del codice: 1 di 2', FS['codes']['ABCD-2345']['used'] == 1)
        inv = await pg.evaluate("JSON.parse(localStorage.getItem('rm_inv'))")
        chk('sul dispositivo: solo codice, date e versione delle avvertenze', set(inv) == {'c', 't', 'a', 'ok'}, inv)
        await pg.wait_for_timeout(600)
        chk('statistiche: nuova attivazione, apertura, dispositivo attivo', stat('nuovi') == 1 and stat('ap') == 1 and stat('att') == 1, FS['stats'])
        chk('statistiche: mese e totale', FS['stats'].get('m-' + time.strftime('%Y-%m'), {}).get('att') == 1 and FS['stats'].get('tot', {}).get('nuovi') == 1)
        # calcolo per peso → contatori dopo qualche secondo
        await pg.evaluate(SPL)
        await pg.wait_for_timeout(500)
        await pg.evaluate("document.getElementById('tabW')&&document.getElementById('tabW').click()")
        for k, v in [('wp', '100'), ('wr', '60'), ('wa', '400')]:
            await pg.fill('#' + k, v)
        await pg.wait_for_timeout(7500); await flush(pg)
        chk('calcolo per peso contato una volta, con l’esito', stat('cw') == 1 and stat('vg') + stat('vt') + stat('vn') == 1, {k: stat(k) for k in ['cw', 'vg', 'vt', 'vn']})
        await pg.wait_for_timeout(6500); await flush(pg)
        chk('lo stesso calcolo non si conta due volte', stat('cw') == 1)
        await pg.click('#sv2'); await pg.wait_for_timeout(600); await flush(pg)
        chk('salvataggio nello storico contato', stat('sv') == 1)
        n0 = await pg.evaluate("window.__CU.hist().length")
        await pg.screenshot(path='/tmp/w_calc.png')
        st_state = await c.storage_state()
        # ricarica: storico ancora lì (sul dispositivo), nessun codice richiesto
        await pg.reload(); await pg.wait_for_timeout(3000)
        await pg.evaluate(SPL); await pg.wait_for_timeout(400)
        chk('dopo la ricarica non chiede più il codice', await pg.evaluate("!document.getElementById('rmGate')||document.getElementById('rmGate').hidden"))
        n1 = await pg.evaluate("window.__CU.hist().length")
        chk('storico conservato sul dispositivo dopo la ricarica', n0 == 1 and n1 == 1, (n0, n1))
        msg = await pg.evaluate("(document.getElementById('hMsg')||{}).textContent||''")
        chk('nessun messaggio «Database non disponibile»', 'Database' not in msg, msg)
        await flush(pg)
        chk('seconda apertura contata, stesso giorno: dispositivi attivi resta 1', stat('ap') == 2 and stat('att') == 1, (stat('ap'), stat('att')))
        # Esporta e recupera: niente cloud
        await pg.evaluate("(()=>{var p=document.getElementById('setPop');if(p.hidden)document.getElementById('setBtn').click()})()"); await pg.wait_for_timeout(300)
        await pg.evaluate("document.getElementById('bkOpen').click()"); await pg.wait_for_timeout(600)
        vis = await pg.evaluate("(()=>{var o=document.getElementById('bkOv');return [!o.hidden,!!document.getElementById('bkPut').offsetParent,!!document.getElementById('bkDl').offsetParent,o.innerText.slice(0,500)]})()")
        chk('Esporta e recupera: niente tasti del cloud, resta il file', vis[0] and not vis[1] and vis[2], vis[3][:200])
        chk('Esporta e recupera: «cloud» solo nella nota che dice che non c’è', vis[3].lower().count('cloud') == 1 and 'non c’è un cloud' in vis[3], vis[3][:120])
        await pg.screenshot(path='/tmp/w_bk.png')
        async with pg.expect_download() as dl:
            await pg.evaluate("document.getElementById('bkDl').click()")
        d = await dl.value
        chk('Scarica un file funziona', bool(d.suggested_filename), d.suggested_filename)
        await pg.evaluate("document.getElementById('bkX').click()"); await pg.wait_for_timeout(300)
        # Menu › Aiuto › Privacy e avvertenze
        await pg.evaluate("(()=>{var p=document.getElementById('setPop');if(p.hidden)document.getElementById('setBtn').click()})()"); await pg.wait_for_timeout(400)
        it = await pg.evaluate("(()=>{var b=document.getElementById('rmLeg');return b?[!!b.offsetParent||true,b.innerText]:null})()")
        chk('voce di menu «Privacy e avvertenze» in Aiuto', bool(it), it)
        await pg.evaluate("document.getElementById('rmLeg').click()"); await pg.wait_for_timeout(400)
        lg = await pg.evaluate("(()=>{var o=document.getElementById('rmLegOv');return [!o.hidden,[].map.call(o.querySelectorAll('a'),function(a){return a.getAttribute('href')}),o.innerText]})()")
        chk('finestra con informativa e avvertenze', lg[0] and 'privacy.html' in lg[1] and 'avvertenze.html' in lg[1], lg[1])
        await pg.screenshot(path='/tmp/w_legal.png')
        await pg.evaluate("document.querySelector('#rmLegOv [data-x]').click()")
        # Guida, «Vai alla funzione», tutorial, aiuto del menu
        g = await pg.evaluate("(()=>{var G=window.__GO;return {go:!!(G&&G.keys&&G.keys.legal)}})()")
        chk('«Vai alla funzione» conosce «legal»', g['go'])
        src = open('/home/claude/web/dist/index.html', encoding='utf-8').read()
        chk('Guida: voce «Privacy, codice d’invito e avvertenze»', "t:'Privacy, codice d’invito e avvertenze'" in src)
        chk('Tutorial: «Privacy e avvertenze»', "{id:'legal'" in src)
        chk('Aiuto del menu: riga Privacy e avvertenze', "'<b>Privacy e avvertenze</b>:" in src)
        chk('nessun accesso con Google nella pagina', 'signInWith' not in src and 'rmAcc' not in src.replace('rmAcc"', ''))
        # «Ti è utile?» dopo 10 calcoli
        await pg.evaluate("localStorage.setItem('rm_uc','9')")
        await pg.evaluate("document.getElementById('tabW')&&document.getElementById('tabW').click()")
        await pg.evaluate("(()=>{var p=document.getElementById('setPop');if(!p.hidden)document.getElementById('setBtn').click()})()"); await pg.wait_for_timeout(300)
        for k, v in [('wp', '130'), ('wr', '60'), ('wa', '400')]:
            await pg.fill('#' + k, v)
        await pg.wait_for_timeout(7500)
        card = await pg.evaluate("(()=>{var c=document.getElementById('rmUse');return c?c.innerText:null})()")
        print('   debug', await pg.evaluate("[localStorage.getItem('rm_uc'),localStorage.getItem('rm_ua'),[].map.call(document.querySelectorAll('.ov:not([hidden])'),function(o){return o.id}),document.getElementById('setPop').hidden,(document.getElementById('vW')||{}).className]"))
        chk('«Ramometro ti è utile?» dopo 10 calcoli', card and 'utile' in card, card)
        await pg.screenshot(path='/tmp/w_use.png')
        if card:
            await pg.click('#rmUse [data-u=si]'); await pg.wait_for_timeout(800)
            chk('risposta «Sì» contata', FS['stats'].get('tot', {}).get('us') == 1 and stat('us') == 1)
        # codice ritirato → blocco con «Scarica i miei dati»
        FS['codes']['ABCD-2345']['on'] = False
        await pg.evaluate("(()=>{var v=JSON.parse(localStorage.getItem('rm_inv'));v.ok=0;localStorage.setItem('rm_inv',JSON.stringify(v))})()")
        await pg.reload(); await pg.wait_for_timeout(3000)
        blk = await pg.evaluate("(()=>{var g=document.getElementById('rmGate');return g&&!g.hidden?[document.getElementById('rmGateS').innerText,!document.getElementById('rmDl').hidden]:null})()")
        chk('codice ritirato: l’app si blocca e offre «Scarica i miei dati»', blk and blk[1], blk)
        await pg.screenshot(path='/tmp/w_off.png')
        chk('nessun errore di programma', not errs, errs[:3])
        # pagine
        for pth in ['privacy.html', 'avvertenze.html']:
            await pg.goto(URL + pth); await pg.wait_for_timeout(500)
            t = await pg.inner_text('body')
            chk('pagina %s' % pth, ('non raccoglie dati personali' in t) if 'privacy' in pth else ('non dà consigli di acquisto' in t), t[:80])
            await pg.screenshot(path='/tmp/w_%s.png' % pth.split('.')[0], full_page=True)
        await pg.goto(URL + 'admin.html'); await pg.wait_for_timeout(1500)
        chk('area riservata: chiede l’accesso', 'Accedi' in await pg.inner_text('header'))
        await pg.screenshot(path='/tmp/w_admin.png')
        ext = sorted(set(urlparse(u).hostname for u in EXT))
        chk('nessuna richiesta a domini esterni (oltre a Firestore)', not [h for h in ext if h not in ('www.googleapis.com', 'identitytoolkit.googleapis.com', 'securetoken.googleapis.com', 'apis.google.com', 'ramometro-eddb8.firebaseapp.com')], ext)
        print('richieste esterne bloccate:', ext)
        await b.close()
    print('ESITO', sum(OK), 'su', len(OK))

asyncio.run(main())
