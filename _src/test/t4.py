"""Prove della web: borsa e notizie da data/market.json, avvisi all'apertura, etichette «solo su claude.ai», Avvisi e soglie, pagine."""
import asyncio, sys, json, time
from playwright.async_api import async_playwright

URL, DIST = sys.argv[1], sys.argv[2]
OK = []
def chk(n, c, x=''):
    OK.append(bool(c)); print(('  ok  ' if c else '  !!  ') + n + (' — ' + str(x)[:200] if x else ''))

SPL = "(()=>{var s=document.getElementById('spl');if(s&&!s.hidden){var b=s.querySelector('[data-splic=completa]')||s.querySelector('button');b&&b.click()}})()"
INV = json.dumps({'c': 'ABCD-2345', 't': int(time.time() * 1000), 'a': '2026-11-20', 'ok': True})

async def main():
    mk = json.load(open(DIST + '/data/market.json', encoding='utf-8'))
    async with async_playwright() as p:
        b = await p.chromium.launch()
        c = await b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, locale='it-IT')
        ext = []
        async def route(r):
            u = r.request.url
            if u.startswith(URL): return await r.continue_()
            if 'firestore.googleapis.com' not in u: ext.append(u)
            return await r.abort()
        await c.route('**/*', route)
        await c.add_init_script("try{localStorage.setItem('cu_lang','it');localStorage.setItem('rm_inv',%r);localStorage.setItem('rm_st','{}');localStorage.setItem('cu_al',JSON.stringify({on:true,src:{qt:true},cu:{d24:{on:true,v:1},d7:{on:true,v:5},r24:{on:true,v:3},r7:{on:true,v:5},lo:{on:false,v:null},hi:{on:false,v:null}}}))}catch(e){}" % INV)
        pg = await c.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(1500); await pg.evaluate(SPL); await pg.wait_for_timeout(4500)
        # 1 · borsa aggiornata nella riga del prezzo
        line = await pg.evaluate("(()=>{var e=document.getElementById('pvMk');return e?e.innerText:''})()")
        # v6.27.3: data e prezzo presi da data/market.json (cambiano ogni giorno feriale)
        MESI = ['gen', 'feb', 'mar', 'apr', 'mag', 'giu', 'lug', 'ago', 'set', 'ott', 'nov', 'dic']
        sd = mk['spot']['date']; dd = '%d %s' % (int(sd[8:10]), MESI[int(sd[5:7]) - 1])
        chk('riga della borsa con il dato del ' + dd, dd in line, line)
        # 2 · avviso all'apertura (soglia calo 1 %)
        al = await pg.evaluate("(()=>{var e=document.querySelector('.rmAlw');return e?e.innerText:null})()")
        chk('avviso sul rame all’apertura', bool(al) and 'Avviso sul rame' in al, al)
        await pg.screenshot(path='/tmp/w4_alert.png')
        if al: await pg.evaluate("document.querySelector('.rmAlw [data-x]').click()")
        # una volta sola
        await pg.reload(); await pg.wait_for_timeout(1500); await pg.evaluate(SPL); await pg.wait_for_timeout(4000)
        al2 = await pg.evaluate("!!document.querySelector('.rmAlw')")
        chk('l’avviso non si ripete alla riapertura', not al2)
        # 3 · Notizie e quotazioni dal file aggiornato
        await pg.evaluate("(()=>{var b=document.querySelector('[data-open=\"nw\"]');if(b)b.click()})()"); await pg.wait_for_timeout(700)
        nw = await pg.evaluate("(()=>{var e=document.getElementById('nwBd');return e?e.innerText:''})()")
        chk('notizie aggiornate (MINING.COM) e timbro dell’aggiornamento', mk['news'][0]['t'][:30] in nw and 'Aggiornamento automatico' in nw, nw[:300])
        await pg.evaluate("(()=>{var x=document.querySelector('#nwOv .imx,#nwX');if(x)x.click();else document.getElementById('nwOv').hidden=true})()"); await pg.wait_for_timeout(200)
        # 4 · etichette «solo su claude.ai»
        await pg.evaluate("document.getElementById('imBtn').click()"); await pg.wait_for_timeout(600)
        ai = await pg.evaluate("[].map.call(document.querySelectorAll('.rmAiB'),function(e){return (e.id||e.getAttribute('data-dlkm')||e.tagName)+':'+e.getAttribute('data-rmai')})")
        chk('etichetta sulle funzioni con l’AI (Importa)', any(x.startswith('imVoice:solo su claude.ai') for x in ai) and any(x.startswith('imImgT:') for x in ai), ai)
        await pg.screenshot(path='/tmp/w4_import.png')
        await pg.evaluate("(()=>{var x=document.getElementById('imX');if(x)x.click()})()"); await pg.wait_for_timeout(200)
        # 5 · Menu › Avvisi e soglie nella versione web
        await pg.evaluate("document.getElementById('setBtn').click()"); await pg.wait_for_timeout(300)
        sub = await pg.evaluate("(()=>{var e=document.getElementById('alCur');return e?e.textContent:null})()")
        chk('menu: avvisi «Attivi all’apertura»', sub == 'Attivi all’apertura', sub)
        await pg.evaluate("document.querySelector('#pvMenu [data-go=\"al\"]').click()"); await pg.wait_for_timeout(400)
        t = await pg.evaluate("document.getElementById('alBd').innerText")
        chk('pagina avvisi senza notifiche, mail e compito', 'Nella versione web non ci sono notifiche' in t and '@' not in t and 'Periodicità' not in t, t[:200])
        mods = await pg.evaluate("(()=>{var h=document.documentElement.innerHTML;return [h.indexOf('usa crediti AI'),h.search(/[A-Za-z0-9._-]+@gmail\\.com/)]})()")
        chk('nessuna mail del gestore e moduli AI segnati', mods[1] < 0 and mods[0] < 0, mods)
        await pg.screenshot(path='/tmp/w4_al.png')
        chk('nessun errore di programma', not errs, errs[:3])
        chk('nessuna richiesta a domini esterni', not ext, ext[:5])
        await b.close()
    av = open(DIST + '/avvertenze.html', encoding='utf-8').read(); pv = open(DIST + '/privacy.html', encoding='utf-8').read()
    neu = "'MARGINE OK'" in open(DIST + '/index.html', encoding='utf-8').read()
    chk('avvertenze con le diciture dell’app', ('«Margine ok»' in av) == neu and ('«Conviene»' in av) != neu)
    chk('pagine: aggiornamento automatico spiegato', 'due volte al giorno' in av and 'automazione di GitHub' in pv)
    print('ESITO', sum(OK), 'su', len(OK))

asyncio.run(main())
