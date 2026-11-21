"""Web 6.26.2: copia su file e recupero che sostituisce lo storico (uso: t7.py URL)."""
import asyncio, sys, json, time
sys.path.insert(0,'/home/claude/tools')
from playwright.async_api import async_playwright
import a2
URL=sys.argv[1]
INV=json.dumps({'c':'ABCD-2345','t':int(time.time()*1000),'a':'2026-11-20','ok':True})
SPL="(()=>{var s=document.getElementById('spl');if(s&&!s.hidden){var b=s.querySelector('[data-splic=completa]')||s.querySelector('button');b&&b.click()}})()"
OK=[]
def chk(n,c,x=''):
    OK.append(bool(c)); print(('  ok  ' if c else '  !!  ')+n+(' — '+str(x)[:300] if not c else ''))
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    c=await b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,locale='it-IT',accept_downloads=True)
    async def route(r):
        if r.request.url.startswith(URL): return await r.continue_()
        return await r.abort()
    await c.route('**/*',route)
    await c.add_init_script("try{if(!localStorage.getItem('__s')){localStorage.setItem('__s','1');localStorage.setItem('cu_lang','it');localStorage.setItem('rm_inv',%r);localStorage.setItem('rm_st','{}');localStorage.setItem('cu_xintro','1')}}catch(e){}"%INV)
    pg=await c.new_page(); errs=[]; pg.on('pageerror',lambda e: errs.append(str(e))); ev=pg.evaluate
    await pg.goto(URL); await pg.wait_for_timeout(2500); await ev(SPL); await pg.wait_for_timeout(800)
    async def reloaded():
        for i in range(60):
            await pg.wait_for_timeout(250)
            try:
                if await ev("()=>!window.__old&&!!window.__CU&&window.__CU.histReady()"): break
            except Exception: pass
        await ev(SPL); await pg.wait_for_timeout(800)
    await ev(a2.HIST); await pg.wait_for_timeout(600)
    h=await ev("()=>window.__CU.hist().length"); chk('web: 4 calcoli nello storico',h==4,h)
    await ev(a2.MENU); await ev("()=>document.getElementById('bkOpen').click()"); await pg.wait_for_timeout(500)
    async with pg.expect_download() as di:
        await ev("()=>document.getElementById('bkDl').click()")
    d=await di.value; path='/tmp/webcopia.json'; await d.save_as(path)
    n=len(json.load(open(path))['hist']); chk('web: file scaricato con 4 calcoli',n==4,n)
    await ev(a2.CLOSE)
    await ev("()=>{for(var k=0;k<3;k++){var L=document.querySelectorAll('#hList li button[data-i]');if(L.length)L[L.length-1].click()}}"); await pg.wait_for_timeout(900)
    h=await ev("()=>window.__CU.hist().length"); chk('web: tolti 3 calcoli',h==1,h)
    await ev(a2.MENU); await ev("()=>document.getElementById('bkOpen').click()"); await pg.wait_for_timeout(500)
    await ev("()=>{window.__old=1}"); await pg.set_input_files('#bkFile',path); await reloaded()
    h=await ev("()=>window.__CU.hist().length"); chk('web: recupero dal file, 4 calcoli',h==4,h)
    await ev(a2.MENU); await ev("()=>document.getElementById('bkOpen').click()"); await pg.wait_for_timeout(500)
    await ev("()=>{window.__old=1;document.getElementById('bkBack').click()}"); await pg.wait_for_timeout(150); await ev("()=>document.getElementById('bkBack').click()"); await reloaded()
    h=await ev("()=>window.__CU.hist().length"); chk('web: torna a prima del recupero, 1 calcolo',h==1,h)
    await ev(a2.MENU); await ev("()=>document.getElementById('bkOpen').click()"); await pg.wait_for_timeout(300)
    await ev("()=>document.querySelector('#bkOv [data-help]').click()"); await pg.wait_for_timeout(300)
    t=await ev("()=>document.getElementById('hpOv').innerText")
    chk('web: Aiuto della copia dice che il recupero sostituisce','Il recupero sostituisce storico e liste con quelli del file.' in t and 'stesso conto' not in t,t[:400])
    chk('web: nessun errore',not errs,errs)
    print('ESITO %d su %d'%(sum(OK),len(OK)))
    await b.close()
asyncio.run(main())
