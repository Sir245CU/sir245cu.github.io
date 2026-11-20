"""Prove della versione web senza dati personali: invito, dati sul dispositivo, statistiche, menu, aiuti, richieste esterne."""
import asyncio, json, re, sys, time
from urllib.parse import urlparse
from playwright.async_api import async_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8765/'
FS = {'codes': {'ABCD-2345': {'max': 2, 'used': 0, 'on': True, 'exp': None},
                'OFFX-2345': {'max': 5, 'used': 0, 'on': False, 'exp': None},
                'FULL-2345': {'max': 1, 'used': 1, 'on': True, 'exp': None},
                'OLDX-2345': {'max': 5, 'used': 0, 'on': True, 'exp': time.time() * 1000 - 864e5}},
      'stats': {}, 'commits': [], 'deny_all': False, 'requests': {}, 'access': {}}
KEYS = set('ap att nuovi r7 r30 tel pc pwa cm cw cs vg vt vn sv co st us un rq ra kpp kfi kin kal upr upf'.split())
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
        m2 = re.search(r'/documents/(requests|access)/([^?]+)', u.path)
        if m2:
            c = FS[m2.group(1)].get(m2.group(2))
            if not c: return await route.fulfill(status=404, body='{}', content_type='application/json')
            f = {}
            for k, v in c.items():
                f[k] = {'stringValue': v} if isinstance(v, str) else ({'booleanValue': v} if isinstance(v, bool) else {'integerValue': str(v)})
            return await route.fulfill(status=200, body=json.dumps({'fields': f}), content_type='application/json')
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
            elif '/requests/' in w['update']['name']:
                rid = w['update']['name'].split('/')[-1]
                f = {k: list(v.values())[0] for k, v in w['update']['fields'].items()}
                cfg = FS['access'].get('config', {})
                ok = (re.fullmatch(r'[A-Z0-9]{16}', rid) and set(f) <= {'st', 'src', 'uso'} and rid not in FS['requests']
                      and (f['st'] == 'attesa' or (f['st'] == 'ok' and cfg.get('auto') is True)) and cfg.get('open', True) is not False
                      and f.get('src', 'pp') in ('pp', 'fi', 'in', 'al') and f.get('uso', 'pr') in ('pr', 'pf')
                      and w['updateTransforms'][0]['fieldPath'] == 'at')
                if not ok: return await route.fulfill(status=403, body='{"bad":"req"}', content_type='application/json')
                FS['requests'][rid] = dict(f)
            elif '/access/' in w['update']['name']:
                d = w['update']['name'].split('/')[-1]
                if not re.fullmatch(r'd-\d{4}-\d{2}-\d{2}', d): return await route.fulfill(status=403, body='{}', content_type='application/json')
                FS['access'][d] = {'n': FS['access'].get(d, {}).get('n', 0) + 1}
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
    await c.add_init_script("try{if(!localStorage.getItem('cu_lang'))localStorage.setItem('cu_lang','it')}catch(e){}")
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
        gate = await pg.evaluate("(()=>{var g=document.getElementById('rmGate');return !!g&&!g.hidden&&!document.getElementById('rmVReq').hidden})()")
        chk('prima apertura: chiede l’accesso, con domande facoltative', gate)
        await pg.screenshot(path='/tmp/w_req.png')
        chk('senza spunta «Chiedi l’accesso» resta spento', await pg.evaluate("document.getElementById('rmAsk').disabled"))
        await pg.click('#rmVReq input[name=rmSrc][value=fi]', force=True); await pg.click('#rmVReq input[name=rmUso][value=pf]', force=True)
        await pg.check('#rmAcc'); await pg.click('#rmAsk'); await pg.wait_for_timeout(1200)
        rq = list(FS['requests'].items())
        chk('richiesta salvata con codice casuale, stato «attesa» e risposte facoltative', len(rq) == 1 and rq[0][1] == {'st': 'attesa', 'src': 'fi', 'uso': 'pf'}, rq)
        wt = await pg.evaluate("[document.getElementById('rmGateT').innerText, document.getElementById('rmRc').innerText, !document.getElementById('rmChk').hidden]")
        chk('schermata d’attesa con il codice da mostrare', wt[0] == 'Richiesta inviata' and wt[1] == rq[0][0][:3] + '-' + rq[0][0][3:6] and wt[2], wt)
        await pg.screenshot(path='/tmp/w_wait.png')
        await pg.wait_for_timeout(600)
        chk('statistiche della richiesta: rq, kfi, upf (totali)', FS['stats'].get('tot', {}).get('rq') == 1 and FS['stats']['tot'].get('kfi') == 1 and FS['stats']['tot'].get('upf') == 1, FS['stats'].get('tot'))
        await pg.click('#rmChk'); await pg.wait_for_timeout(700)
        chk('«Controlla ora» quando è ancora in attesa', 'attesa' in await pg.inner_text('#rmGateM'), await pg.inner_text('#rmGateM'))
        FS['requests'][rq[0][0]]['st'] = 'ok'
        await pg.click('#rmChk'); await pg.wait_for_timeout(1800)
        chk('richiesta approvata: l’app si apre', await pg.evaluate("document.getElementById('rmGate').hidden"))
        inv = await pg.evaluate("JSON.parse(localStorage.getItem('rm_inv'))")
        chk('sul dispositivo: solo il codice della richiesta, date e versione delle avvertenze', set(inv) == {'r', 't', 'a', 'ok'}, inv)
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
        core = await pg.evaluate("!!document.querySelector('#pvMenu [data-go=leg]')")
        if core:   # app 6.24.0 o successiva: pagina del menu con il testo della web
            it = await pg.evaluate("(()=>{var b=document.querySelector('#pvMenu [data-go=leg]');return b?b.innerText:null})()")
            chk('voce di menu «Privacy e avvertenze» in Aiuto', bool(it) and not await pg.evaluate("!!document.getElementById('rmLeg')"), it)
            await pg.evaluate("document.querySelector('#pvMenu [data-go=leg]').click()"); await pg.wait_for_timeout(400)
            lg = await pg.evaluate("(()=>{var o=document.getElementById('pvLeg');return [!o.hidden,[].map.call(o.querySelectorAll('a'),function(a){return a.getAttribute('href')}),o.innerText]})()")
            chk('pagina con informativa e avvertenze (testo della web)', lg[0] and 'privacy.html' in lg[1] and 'avvertenze.html' in lg[1] and 'claude.ai' not in lg[2].split('Le funzioni AI')[0], lg[1])
            await pg.screenshot(path='/tmp/w_legal.png')
            await pg.evaluate("document.querySelector('#pvLeg [data-back]').click()")
            await pg.evaluate("(()=>{var p=document.getElementById('setPop');if(!p.hidden)document.getElementById('setBtn').click()})()")
        else:
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
        src = open(sys.argv[2] if len(sys.argv) > 2 else '/home/claude/web/dist/index.html', encoding='utf-8').read()
        chk('Guida: voce «Privacy, accesso e avvertenze»', "t:'Privacy, accesso e avvertenze'" in src and src.count("t:'Privacy e avvertenze',k:") == 0)
        chk('Tutorial: «Privacy e avvertenze»', src.count("{id:'legal'") == 1)
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
        FS['requests'][rq[0][0]]['st'] = 'no'
        await pg.evaluate("(()=>{var v=JSON.parse(localStorage.getItem('rm_inv'));v.ok=0;localStorage.setItem('rm_inv',JSON.stringify(v))})()")
        await pg.reload(); await pg.wait_for_timeout(3000)
        blk = await pg.evaluate("(()=>{var g=document.getElementById('rmGate');return g&&!g.hidden?[document.getElementById('rmGateT').innerText,!document.getElementById('rmDl').hidden,!document.getElementById('rmAsk').hidden]:null})()")
        chk('accesso ritirato: l’app si blocca, offre «Scarica i miei dati» e «Chiedi di nuovo»', blk and blk[0] == 'Accesso ritirato' and blk[1] and blk[2], blk)
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
        # codice d'invito (seconda strada), su un altro dispositivo
        c2, p2, e2 = await ctx(b)
        await p2.goto(URL); await p2.wait_for_timeout(2000)
        await p2.click('#rmToCode'); await p2.wait_for_timeout(200)
        await p2.fill('#rmCode', 'zzzz2345'); await p2.check('#rmAcc')
        chk('«Ho già un codice»: codice in maiuscolo con trattino', await p2.input_value('#rmCode') == 'ZZZZ-2345')
        await p2.click('#rmGo'); await p2.wait_for_timeout(800)
        chk('codice inesistente: messaggio chiaro', 'non valido' in await p2.inner_text('#rmGateM'))
        for code, want in [('OFFX-2345', 'non è più attivo'), ('FULL-2345', 'numero massimo'), ('OLDX-2345', 'scaduto')]:
            await p2.fill('#rmCode', code); await p2.click('#rmGo'); await p2.wait_for_timeout(700)
            chk('codice %s: «%s»' % (code, want), want in await p2.inner_text('#rmGateM'))
        await p2.fill('#rmCode', 'ABCD-2345'); await p2.click('#rmGo'); await p2.wait_for_timeout(1600)
        chk('codice valido: l’app si apre', await p2.evaluate("document.getElementById('rmGate').hidden") and FS['codes']['ABCD-2345']['used'] == 1)
        await c2.close()
        # approvazione automatica con limite 1 al giorno
        FS['access']['config'] = {'auto': True, 'open': True, 'maxDay': 1}
        c3, p3, e3 = await ctx(b, 1366, 860, False)
        await p3.goto(URL); await p3.wait_for_timeout(2000)
        await p3.check('#rmAcc'); await p3.click('#rmAsk'); await p3.wait_for_timeout(1800)
        chk('approvazione automatica: entra subito', await p3.evaluate("document.getElementById('rmGate').hidden"))
        chk('contatore del giorno e statistica «ra»', list(FS['access'].values())[-1].get('n') == 1 and FS['stats']['tot'].get('ra') == 1, FS['access'])
        await c3.close()
        c4, p4, e4 = await ctx(b)
        await p4.goto(URL); await p4.wait_for_timeout(2000)
        await p4.check('#rmAcc'); await p4.click('#rmAsk'); await p4.wait_for_timeout(1500)
        chk('oltre il limite del giorno: resta in attesa', await p4.evaluate("document.getElementById('rmGateT').innerText") == 'Richiesta inviata')
        last = [k for k, v in FS['requests'].items() if v['st'] == 'attesa'][-1]
        FS['requests'][last]['st'] = 'no'
        await p4.click('#rmChk'); await p4.wait_for_timeout(1200)
        chk('richiesta rifiutata: lo dice e offre «Chiedi di nuovo»', await p4.evaluate("document.getElementById('rmGateT').innerText") == 'Richiesta non approvata')
        await p4.check('#rmAcc'); await p4.click('#rmAsk'); await p4.wait_for_timeout(600)
        chk('«Chiedi di nuovo» subito dopo un rifiuto: aspetta qualche minuto', 'tra qualche minuto' in await p4.inner_text('#rmGateM'))
        await p4.screenshot(path='/tmp/w_no.png')
        await c4.close()
        # richieste chiuse
        FS['access']['config'] = {'auto': False, 'open': False}
        c5, p5, e5 = await ctx(b)
        await p5.goto(URL); await p5.wait_for_timeout(2000)
        await p5.check('#rmAcc'); await p5.click('#rmAsk'); await p5.wait_for_timeout(1000)
        chk('richieste chiuse: messaggio chiaro, nessuna richiesta salvata', 'non si accettano' in await p5.inner_text('#rmGateM'), await p5.inner_text('#rmGateM'))
        await c5.close()
        chk('nessun errore di programma negli altri dispositivi', not (e2 or e3 or e4 or e5), (e2 + e3 + e4 + e5)[:3])
        ext = sorted(set(urlparse(u).hostname for u in EXT))
        chk('nessuna richiesta a domini esterni (oltre a Firestore)', not [h for h in ext if h not in ('www.googleapis.com', 'identitytoolkit.googleapis.com', 'securetoken.googleapis.com', 'apis.google.com', 'ramometro-eddb8.firebaseapp.com')], ext)
        print('richieste esterne bloccate:', ext)
        await b.close()
    print('ESITO', sum(OK), 'su', len(OK))

asyncio.run(main())
