"""Prove della web 6.25.0: lingua alla prima apertura (anche nelle pagine d'accesso), previsioni sospese, Analisi del rame usato."""
import asyncio, sys, json, time
from playwright.async_api import async_playwright

URL = sys.argv[1]
OK = []
def chk(n, c, x=''):
    OK.append(bool(c)); print(('  ok  ' if c else '  !!  ') + n + (' — ' + str(x)[:300] if x else ''))

SPL = "(()=>{var s=document.getElementById('spl');if(s&&!s.hidden){var b=s.querySelector('[data-splic=completa]')||s.querySelector('button');b&&b.click()}})()"
INV = json.dumps({'c': 'ABCD-2345', 't': int(time.time() * 1000), 'a': '2026-11-20', 'ok': True})

async def ctx(b, init=None):
    c = await b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, locale='it-IT')
    async def route(r):
        if r.request.url.startswith(URL): return await r.continue_()
        return await r.abort()
    await c.route('**/*', route)
    if init: await c.add_init_script(init)
    pg = await c.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    return c, pg, errs

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # 1 · prima apertura: lingua prima della richiesta d'accesso
        c, pg, errs = await ctx(b); ev = pg.evaluate
        await pg.goto(URL); await pg.wait_for_timeout(1500)
        st = await ev("[!document.getElementById('lgFirst').hidden,!!document.getElementById('rmGate')]")
        chk('scelta della lingua visibile', st[0], st)
        top = await ev("(()=>{var e=document.elementFromPoint(195,422);return !!e&&!!e.closest('#lgFirst')})()"); chk('sopra la richiesta d’accesso', top)
        lb = await ev("[].map.call(document.querySelectorAll('#lgFirst [data-lgf]'),function(b){return b.getAttribute('data-lgf')})")
        chk('6.30.0: tre lingue alla prima apertura', lb == ['it', 'en', 'vec'], lb)
        await ev("document.querySelector('#lgFirst [data-lgf=en]').click()"); await pg.wait_for_timeout(1500)
        g = await ev("(()=>{var g=document.getElementById('rmGate');return g&&!g.hidden?g.innerText:''})()")
        chk('richiesta d’accesso in inglese', 'Welcome to Ramometro' in g and 'Ask for access' in g and 'I already have a code' in g and 'Terms of use' in g, g[:400])
        chk('nessun testo italiano rimasto', not any(w in g for w in ['Benvenuto', 'Chiedi l’accesso', 'Facoltativo', 'Ho già un codice', 'Non chiediamo']), g[:400])
        await ev("document.getElementById('rmToCode').click()"); await pg.wait_for_timeout(500)
        g = await ev("document.getElementById('rmGate').innerText"); chk('pagina del codice in inglese', 'Invitation code' in g and 'Activate the code' in g, g[:300])
        await pg.reload(); await pg.wait_for_timeout(1500)
        st = await ev("[document.getElementById('lgFirst').hidden,localStorage.getItem('cu_lang')]"); chk('la lingua resta', st == [True, 'en'], st)
        g = await ev("document.getElementById('rmGate').innerText"); chk('dopo la riapertura ancora in inglese', 'Welcome' in g or 'Invitation code' in g, g[:200])
        chk('nessun errore', not errs, errs[:3])
        await c.close()
        # 1b · veneto
        c, pg, errs = await ctx(b); ev = pg.evaluate
        await pg.goto(URL); await pg.wait_for_timeout(1500)
        await ev("document.querySelector('#lgFirst [data-lgf=vec]').click()"); await pg.wait_for_timeout(1500)
        g = await ev("document.getElementById('rmGate').innerText"); chk('richiesta d’accesso in veneto', 'Benvegnù in Ramometro' in g and 'Domanda l’acesso' in g, g[:300])
        await c.close()
        # 2 · app abilitata: previsioni sospese, Analisi del rame usato funziona
        c, pg, errs = await ctx(b, "try{localStorage.setItem('cu_lang','it');localStorage.setItem('rm_inv',%r);localStorage.setItem('rm_st','{}')}catch(e){}" % INV); ev = pg.evaluate
        await pg.goto(URL); await pg.wait_for_timeout(1500); await ev(SPL); await pg.wait_for_timeout(2500)
        chk('niente scelta per chi ha già la lingua', await ev("document.getElementById('lgFirst').hidden"))
        chk('Proiezione spenta', await ev("window.__MOD.on('pj')===false&&![].some.call(document.querySelectorAll('[data-open=\"pj\"]'),function(e){return !!e.getClientRects().length})"))
        r = await ev("window.__GO('an')"); await pg.wait_for_timeout(800)
        chk('6.29.0: «Analisi rame usato» tolta: «Vai alla funzione» non apre nulla', r is False and await ev("document.getElementById('anOv').hidden&&document.getElementById('setPop').hidden"), r)
        chk('nessun errore (app)', not errs, errs[:3])
        await c.close()
        await b.close()
    print('ESITO', sum(OK), 'su', len(OK))
asyncio.run(main())
