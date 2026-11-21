"""Prove della web 6.26.0: logo con la R maiuscola nelle pagine d'accesso e nell'area riservata, riga e avviso sui browser."""
import asyncio, sys, json, time
from playwright.async_api import async_playwright
URL = sys.argv[1]; SHOT = sys.argv[2] if len(sys.argv) > 2 else None
OK = []
def chk(n, c, x=''):
    OK.append(bool(c)); print(('  ok  ' if c else '  !!  ') + n + (' — ' + str(x)[:300] if x else ''))
RD = 'M0 0V-60H14C25-60 32-53.5 32-44S25-28 14-28H0M15-28L33 0'
INV = json.dumps({'c': 'ABCD-2345', 't': int(time.time() * 1000), 'a': '2026-11-20', 'ok': True})
SPL = "(()=>{var s=document.getElementById('spl');if(s&&!s.hidden){var b=s.querySelector('[data-splic=completa]')||s.querySelector('button');b&&b.click()}})()"

async def ctx(b, init=None, ua=None):
    kw = dict(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, locale='it-IT')
    if ua: kw['user_agent'] = ua
    c = await b.new_context(**kw)
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
        c, pg, errs = await ctx(b, "try{localStorage.setItem('cu_lang','it')}catch(e){}"); ev = pg.evaluate
        await pg.goto(URL); await pg.wait_for_timeout(1500)
        g = await ev("(()=>{var w=document.querySelector('#rmGate .rmWm svg');return [!!w,w?w.outerHTML.indexOf(%r)>-1:false,w?w.getBoundingClientRect().width:0]})()" % RD)
        chk('logo con la R maiuscola nella richiesta d’accesso', g[0] and g[1] and g[2] > 100, g)
        t = await ev("document.getElementById('rmGate').innerText")
        chk('riga sui browser', 'Funziona con Chrome, Edge, Safari, Samsung Internet e Firefox aggiornati' in t, t[-300:])
        chk('nessun avviso con un browser normale', await ev("document.getElementById('rmBrwW').hidden"))
        if SHOT: await pg.screenshot(path=SHOT)
        await ev("document.getElementById('rmToCode').click()"); await pg.wait_for_timeout(400)
        chk('logo anche nella pagina del codice', await ev("!!document.querySelector('#rmGate .rmWm svg')&&!!document.getElementById('rmCode').getClientRects().length"))
        chk('nessun errore', not errs, errs[:3]); await c.close()
        # tedesco
        c, pg, errs = await ctx(b, "try{localStorage.setItem('cu_lang','de')}catch(e){}"); ev = pg.evaluate
        await pg.goto(URL); await pg.wait_for_timeout(2000)
        t = await ev("document.getElementById('rmGate').innerText")
        chk('riga sui browser in tedesco', 'Funktioniert mit aktuellem Chrome' in t, t[-300:]); await c.close()
        # browser interno di un'altra app
        ua = 'Mozilla/5.0 (Linux; Android 13; SM-A536B Build/TP1A; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/120.0 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/440.0.0.0;]'
        c, pg, errs = await ctx(b, "try{localStorage.setItem('cu_lang','it')}catch(e){}", ua); ev = pg.evaluate
        await pg.goto(URL); await pg.wait_for_timeout(1800)
        w = await ev("(()=>{var e=document.getElementById('rmBrwW');return [e.hidden,e.textContent]})()")
        chk('avviso nel browser interno di Facebook', not w[0] and 'browser interno' in w[1], w); await c.close()
        # stessa situazione con l'app già abilitata: barra in alto, una volta
        c, pg, errs = await ctx(b, "try{localStorage.setItem('cu_lang','it');localStorage.setItem('rm_inv',%r);localStorage.setItem('rm_st','{}')}catch(e){}" % INV, ua); ev = pg.evaluate
        await pg.goto(URL); await pg.wait_for_timeout(1500); await ev(SPL); await pg.wait_for_timeout(1500)
        n = await ev("document.querySelectorAll('.rmBrwBar').length"); chk('barra di avviso nell’app abilitata', n == 1, n)
        await ev("document.querySelector('.rmBrwBar button').click()"); await pg.wait_for_timeout(200)
        chk('la barra si chiude', await ev("!document.querySelector('.rmBrwBar')")); await c.close()
        # area riservata
        c, pg, errs = await ctx(b); ev = pg.evaluate
        await pg.goto(URL + 'admin.html'); await pg.wait_for_timeout(800)
        a = await ev("(()=>{var w=document.querySelector('header .wmk svg');return [!!w,w?w.outerHTML.indexOf(%r)>-1:false,w?w.getBoundingClientRect().width:0]})()" % RD)
        chk('logo nell’area riservata', a[0] and a[1] and a[2] > 100, a); await c.close()
        await b.close()
    print('ESITO', sum(OK), 'su', len(OK))
asyncio.run(main())
