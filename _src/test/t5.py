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
        await ev("document.querySelector('#lgFirst [data-lgf=de]').click()"); await pg.wait_for_timeout(1500)
        g = await ev("(()=>{var g=document.getElementById('rmGate');return g&&!g.hidden?g.innerText:''})()")
        chk('richiesta d’accesso in tedesco', 'Willkommen bei Ramometro' in g and 'Zugang anfragen' in g and 'Ich habe schon einen Code' in g and 'Nutzungshinweise' in g, g[:400])
        chk('nessun testo italiano rimasto', not any(w in g for w in ['Benvenuto', 'Chiedi l’accesso', 'Facoltativo', 'Ho già un codice', 'Non chiediamo']), g[:400])
        await ev("document.getElementById('rmToCode').click()"); await pg.wait_for_timeout(500)
        g = await ev("document.getElementById('rmGate').innerText"); chk('pagina del codice in tedesco', 'Einladungscode' in g and 'Code aktivieren' in g, g[:300])
        await pg.reload(); await pg.wait_for_timeout(1500)
        st = await ev("[document.getElementById('lgFirst').hidden,localStorage.getItem('cu_lang')]"); chk('la lingua resta', st == [True, 'de'], st)
        g = await ev("document.getElementById('rmGate').innerText"); chk('dopo la riapertura ancora in tedesco', 'Willkommen' in g or 'Einladungscode' in g, g[:200])
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
        await ev("window.__GO('an')"); await pg.wait_for_timeout(1200)
        an = await ev("(document.getElementById('anBd')||{}).innerText||''")
        chk('Analisi del rame usato si apre', 'Rame usato oggi in Italia' in an and 'Da verificare' in an and '€/kg' in an, an[:300])
        chk('senza prospettive', 'Prospettive' not in an and '2027' not in an, an[:300])
        chk('nessun errore (app)', not errs, errs[:3])
        await c.close()
        await b.close()
    print('ESITO', sum(OK), 'su', len(OK))
asyncio.run(main())
