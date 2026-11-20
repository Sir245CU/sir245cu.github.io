import asyncio, json
from playwright.async_api import async_playwright
SEED = """(()=>{const T=(ms)=>({toMillis:()=>ms,toDate:()=>new Date(ms)});const n=Date.now();
window.__MOCKDB={requests:{AAABBBCCCDDDEEEF:{st:'attesa',src:'fi',uso:'pf',at:T(n-6e4)},GGGHHHJJJKKKMMMN:{st:'attesa',at:T(n-36e5)},PPPQQQRRRSSSTTTU:{st:'ok',src:'pp',uso:'pr',at:T(n-864e5)},VVVWWWXXXYYYZZZ2:{st:'no',src:'in',at:T(n-2*864e5)}},
access:{config:{auto:false,open:true,maxDay:0}},codes:{},stats:{tot:{rq:4,kpp:1,kfi:1,kin:1,upr:1,upf:1,nuovi:2,ra:0,us:1,un:0},['m-'+new Date().toISOString().slice(0,7)]:{att:2}}}})()"""
OK=[]
def chk(n,c,x=''):
    c=bool(c);OK.append(c);print(('  ok  ' if c else '  !!  ')+n+(' — '+str(x) if x else ''))
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
        for w,h in [(1280,900),(390,844)]:
            c=await b.new_context(viewport={'width':w,'height':h}); pg=await c.new_page(); errs=[]
            pg.on('pageerror',lambda e: errs.append(str(e)[:200]))
            await c.route('https://**/*', lambda r: r.abort())
            await pg.add_init_script(SEED)
            await pg.goto('http://127.0.0.1:8766/admin.html'); await pg.wait_for_timeout(800)
            chk(f'{w}: area visibile', await pg.evaluate("!document.getElementById('app').hidden"))
            t=await pg.inner_text('#pendT'); chk(f'{w}: 2 richieste in attesa nel titolo', '(2)' in t and document_title_ok(await pg.title()), t)
            rows=await pg.evaluate("[...document.querySelectorAll('#pend tbody tr')].map(r=>r.innerText.replace(/\\s+/g,' '))")
            chk(f'{w}: righe in attesa con codice, ora, risposte', len(rows)==2 and 'AAA-BBB' in rows[0] and 'Fiera o evento' in rows[0] and 'Professionale' in rows[0], rows)
            src=await pg.inner_text('#src'); chk(f'{w}: grafico «come ci hanno conosciuto»', 'Passaparola' in src and 'Non ha risposto' in src, src.replace('\n',' '))
            await pg.screenshot(path=f'/tmp/adm_{w}.png', full_page=True)
            if w==1280:
                await pg.click('#pend button[data-r=ok][data-i=AAABBBCCCDDDEEEF]'); await pg.wait_for_timeout(300)
                chk('Approva: stato ok', await pg.evaluate("window.__MOCKDB.requests.AAABBBCCCDDDEEEF.st")=='ok')
                await pg.click('#pend button[data-r=no][data-i=GGGHHHJJJKKKMMMN]'); await pg.wait_for_timeout(300)
                chk('Rifiuta: stato no', await pg.evaluate("window.__MOCKDB.requests.GGGHHHJJJKKKMMMN.st")=='no')
                chk('nessuna in attesa', 'Nessuna richiesta' in await pg.inner_text('#pend'))
                await pg.click('#appr button[data-r=no][data-i=PPPQQQRRRSSSTTTU]'); await pg.wait_for_timeout(300)
                chk('Ritira un accesso approvato', await pg.evaluate("window.__MOCKDB.requests.PPPQQQRRRSSSTTTU.st")=='no')
                b2=pg.locator('#rej button[data-r=del][data-i=VVVWWWXXXYYYZZZ2]'); await pg.evaluate("document.querySelector('#rej').closest('details').open=true")
                await b2.click(); await b2.click(); await pg.wait_for_timeout(300)
                chk('Elimina con doppio tocco', await pg.evaluate("!('VVVWWWXXXYYYZZZ2' in window.__MOCKDB.requests)"))
                await pg.click('input[name=am][value=auto]',force=True); await pg.fill('#mxd','5'); await pg.click('#sva'); await pg.wait_for_timeout(300)
                cfg=await pg.evaluate("window.__MOCKDB.access.config")
                chk('Salva: automatica con limite 5', cfg=={'auto':True,'open':True,'maxDay':5}, cfg)
                chk('nota sotto le impostazioni', 'fino a 5 al giorno' in await pg.inner_text('#accNote'))
                await pg.fill('#max','2'); await pg.click('#mk'); await pg.wait_for_timeout(300)
                chk('Crea codice', len(await pg.evaluate("Object.keys(window.__MOCKDB.codes)"))==1)
            chk(f'{w}: nessun errore', not errs, errs)
            await c.close()
        await b.close()
    print('ESITO',sum(OK),'su',len(OK))
def document_title_ok(t): return t.startswith('(2)')
asyncio.run(main())
