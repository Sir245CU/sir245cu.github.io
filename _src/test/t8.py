"""Web 6.26.3: link comodi da toccare (Rame usato, Notizie, Privacy e avvertenze, Spedizione) a 390 e 1280 px (uso: t8.py URL)."""
import asyncio, sys, json, time
sys.path.insert(0, '/home/claude/tools')
from playwright.async_api import async_playwright
from lib import LAYOUT
import a2
URL = sys.argv[1]
INV = json.dumps({'c': 'ABCD-2345', 't': int(time.time() * 1000), 'a': '2026-11-20', 'ok': True})
SPL = "(()=>{var s=document.getElementById('spl');if(s&&!s.hidden){var b=s.querySelector('[data-splic=completa]')||s.querySelector('button');b&&b.click()}})()"
OK = []
def chk(n, c, x=''):
    OK.append(bool(c)); print(('  ok  ' if c else '  !!  ') + n + ('' if c else ' — ' + str(x)[:400]))
SC = {s[0]: s for s in a2.SCREENS}
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for w in (390, 1280):
            c = await b.new_context(viewport={'width': w, 'height': 844 if w < 700 else 900}, is_mobile=w < 700, has_touch=w < 700, locale='it-IT')
            async def route(r):
                if r.request.url.startswith(URL): return await r.continue_()
                return await r.abort()
            await c.route('**/*', route)
            await c.add_init_script("try{if(!localStorage.getItem('__s')){localStorage.setItem('__s','1');localStorage.setItem('cu_lang','it');localStorage.setItem('rm_inv',%r);localStorage.setItem('rm_st','{}');localStorage.setItem('cu_xintro','1')}}catch(e){}" % INV)
            pg = await c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); ev = pg.evaluate
            await pg.goto(URL); await pg.wait_for_timeout(2500); await ev(SPL); await pg.wait_for_timeout(800)
            for name in ('rame-usato', 'notizie', 'spedizione'):
                _, acts, root = SC[name]
                for a in acts: await ev(a); await pg.wait_for_timeout(300)
                L = await ev(LAYOUT, root)
                op = await ev("(s)=>{var e=document.querySelector(s);return !!e&&!e.hidden}", root)
                chk('%d px · %s: aperta, niente di piccolo o tagliato' % (w, name), op and not L['small'] and not L['clip'] and not L['over'], (op, L['small'], L['clip'], L['over']))
                await ev(a2.CLOSE); await pg.wait_for_timeout(200)
            for a in SC['menu-leg'][1]: await ev(a); await pg.wait_for_timeout(300)
            L = await ev(LAYOUT, '#pvLeg')
            op = await ev("(()=>{var e=document.getElementById('pvLeg');return !!e&&!e.hidden&&document.querySelectorAll('#lgBd a').length>0})()")
            chk('%d px · Privacy e avvertenze: aperta, link comodi da toccare' % w, op and not L['small'] and not L['clip'], (op, L['small'], L['clip']))
            await ev(a2.CLOSE); await pg.wait_for_timeout(200)
            chk('%d px · nessun errore' % w, not errs, errs[:3])
            await c.close()
        print('ESITO %d su %d' % (sum(OK), len(OK)))
        await b.close()
asyncio.run(main())
