#!/usr/bin/env python3
"""Ramometro web (dal 19/11/2026: nessun dato personale) — dalla produzione claude.ai al sito.
uso: python3 build.py src/prod.html dist firebase-config.json
Il sito: niente account e niente cloud personale (dati sul dispositivo), uso su invito,
statistiche solo con contatori anonimi, caratteri e librerie ospitati sul sito, AI spenta.
"""
import sys, os, re, json, base64, urllib.parse, subprocess, hashlib, shutil, glob

here = os.path.dirname(os.path.abspath(__file__))
src, out, cfgp = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, os.path.join(here, 'src'))
import pages

for d in ['icons', 'fonts', 'lib/pdfjs']:
    os.makedirs(os.path.join(out, d), exist_ok=True)
s = open(src, encoding='utf-8').read()
NM = os.path.join(here, 'node_modules')


def must(old, new, count=1):
    global s
    n = s.count(old)
    if n != count:
        raise SystemExit('trovati %d invece di %d: %s' % (n, count, old[:90]))
    s = s.replace(old, new)


def must_re(pat, new, flags=0):
    global s
    m = list(re.finditer(pat, s, flags))
    if len(m) != 1:
        raise SystemExit('trovati %d: %s' % (len(m), pat))
    s = s[:m[0].start()] + new + s[m[0].end():]


cfg = json.load(open(cfgp))
pub = {k: cfg[k] for k in ('apiKey', 'projectId')}

# 1 · strato web (nessuna libreria esterna: archivio locale, invito e contatori via REST)
subprocess.run(['npx', 'esbuild', 'src/shim.js', '--minify', '--target=es2017', '--outfile=build/shim.min.js', '--log-level=warning'], cwd=here, check=True)
shim = open(os.path.join(here, 'build/shim.min.js'), encoding='utf-8').read().replace('</script', '<\\/script')
inject = '<script>window.__RM_FB=%s;window.__WEB=2;</script><script>%s</script>' % (json.dumps(pub), shim)
s = re.sub(r'(<title>[^<]*</title>)', lambda m: m.group(1) + inject, s, count=1)

# 2 · ambiente: identità propria sul dispositivo
must("var E='prod',k='cu_xenv'", "var E='web',k='cu_xenv'")

# 3 · manifest e icone come file veri
m = re.search(r'<link rel="manifest" href="data:application/manifest\+json,([^"]+)">', s)
man = json.loads(urllib.parse.unquote(m.group(1)))
icons = []
for ic in man.get('icons', []):
    u = ic['src']
    if u.startswith('data:image/png;base64,'):
        name = 'icons/icon-%s.png' % ic.get('sizes', 'x').split(' ')[0]
        open(os.path.join(out, name), 'wb').write(base64.b64decode(u.split(',', 1)[1]))
        icons.append(dict(ic, src=name))
man.update({'id': './', 'start_url': './', 'scope': './', 'icons': icons, 'lang': 'it', 'name': 'Ramometro',
            'description': 'Stima del rame recuperabile dai cavi elettrici e del margine teorico. Nessun dato personale.'})
json.dump(man, open(os.path.join(out, 'manifest.json'), 'w'), ensure_ascii=False, indent=1)
s = s.replace(m.group(0), '<link rel="manifest" href="manifest.json">')

# 4 · messaggi che rimandavano a claude.ai (qui l'AI non c'è)
W = 'nella versione web l’AI non è disponibile: usa la versione su claude.ai'
for old, new in [
    ('non è disponibile in questa vista: apri l’app in Claude. Resta l’analisi di prima.', 'non è disponibile: ' + W + '. Resta l’analisi di prima.'),
    ('solo aprendo l’app in Claude: scrivi i km a mano.', 'solo nella versione su claude.ai: scrivi i km a mano.'),
    ('solo aprendo l’app in Claude. Resta l’ultimo dato.', 'solo nella versione su claude.ai. Resta l’ultimo dato.'),
    ('solo aprendo l’app in Claude.', 'solo nella versione su claude.ai.'),
]:
    s = s.replace(old, new)

# 5 · caratteri e librerie dal sito stesso (nessuna richiesta a Google Fonts o cdnjs)
must('<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@600&family=Archivo+Black&display=swap" rel="stylesheet">',
     '<link href="fonts/fonts.css" rel="stylesheet">')
must("var PDFU='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/';", "var PDFU='lib/pdfjs/';")
must("loadScript('https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js'", "loadScript('lib/xlsx.full.min.js'")
shutil.copy(os.path.join(NM, 'pdfjs-dist/build/pdf.min.js'), os.path.join(out, 'lib/pdfjs/pdf.min.js'))
shutil.copy(os.path.join(NM, 'pdfjs-dist/build/pdf.worker.min.js'), os.path.join(out, 'lib/pdfjs/pdf.worker.min.js'))
shutil.copy(os.path.join(NM, 'xlsx/dist/xlsx.full.min.js'), os.path.join(out, 'lib/xlsx.full.min.js'))
css = []
for f in ['ibm-plex-sans/400.css', 'ibm-plex-sans/500.css', 'ibm-plex-sans/600.css', 'ibm-plex-sans-condensed/600.css', 'archivo-black/400.css']:
    c = open(os.path.join(NM, '@fontsource', f), encoding='utf-8').read()
    base = os.path.join(NM, '@fontsource', f.split('/')[0], 'files')
    for w in set(re.findall(r'url\(\./files/([^)]+\.woff2)\)', c)):
        shutil.copy(os.path.join(base, w), os.path.join(out, 'fonts', w))
    c = re.sub(r"url\(\./files/([^)]+\.woff2)\) format\('woff2'\), url\(\./files/[^)]+\.woff\) format\('woff'\)", r"url(\1) format('woff2')", c)
    css.append(c)
open(os.path.join(out, 'fonts/fonts.css'), 'w', encoding='utf-8').write('\n'.join(css))
for bad in ['fonts.googleapis.com', 'fonts.gstatic.com', 'cdnjs.cloudflare.com']:
    if bad in s:
        raise SystemExit('resta un collegamento esterno: ' + bad)

# 6 · niente cloud: copia di sicurezza e salvataggio continuo lavorano solo con il file
DBX = "var dbp=null;function dbx(){if(!dbp)dbp=(async function(){try{var cl=window.claude;if(!cl||!cl.use)return null;var db=await cl.use('db'),u=await cl.use('user');if(!db||!u)return null;return{db:db,id:await u.id()}}catch(e){return null}})();return dbp}"
must(DBX, "var dbp=null;function dbx(){return Promise.resolve(null)}/* web: niente cloud */", 2)
i = s.index('<div class="lbl mdh">Salvataggio continuo</div>')
j = s.index('<div class="lbl mdh">Su file</div>', i)
s = s[:i] + '<div hidden>' + s[i:j] + '</div><p class="k" style="margin:0 0 10px">Nella versione web i dati restano solo su questo dispositivo: non c’è un cloud. Per non perderli, o per portarli su un altro telefono o PC, scarica ogni tanto un file.</p>' + s[j:]
must_re(r'<p class="aiw">Il cloud è il tuo conto Claude[^<]*</p>',
        '<p class="aiw">Il file contiene storico, magazzino, rese, acquirenti, tariffe, siti, parametri, moduli e valori imparati. Recuperare un file sostituisce i dati di adesso: prima li salvo, così puoi tornare indietro.</p>')

# 7 · testi sul cloud → dati sul dispositivo
for old, new in [
    ('<li>Copia di sicurezza nel cloud</li>', '<li>Copia di sicurezza su file</li>'),
    ('<small>Storico, apprendimento, cloud, stampe</small>', '<small>Storico, apprendimento, copie, stampe</small>'),
    ("['bk','Copia di sicurezza','Dati nel cloud, anche su altri dispositivi'", "['bk','Copia di sicurezza','Copie su file e ripristino'"),
    ('>Senza rete: i calcoli funzionano. Salvo nel cloud quando torna la rete.</div>', '>Senza rete: l’app funziona e i dati restano sul dispositivo.</div>'),
    ("T('Rete tornata: salvo nel cloud.')", "T('Rete tornata.')"),
    ('lo storico e le modifiche vanno nel cloud da soli quando la rete torna', 'storico e modifiche restano salvati sul dispositivo'),
    ('Usi l’app su più dispositivi o vuoi una copia dei dati nel cloud?', 'Vuoi fare copie di sicurezza dei tuoi dati su file?'),
    ('Nella Completa i dati si salvano già da soli nel cloud; il file serve per conservarli altrove o portarli su un altro account.',
     'Nella versione web i dati restano solo su questo dispositivo: il file serve per conservarli e per portarli su un altro telefono o PC.'),
]:
    must(old, new)
must_re(r"\{g:'App',t:'Salvataggio continuo nel cloud',k:'[^']*',h:'[^']*',a:'bk'\},",
        "{g:'App',t:'Dati sul dispositivo e copie su file',k:'cloud salvataggio continuo sincronizza dispositivi telefono tablet computer copia sicurezza dati persi file versione web',h:'<p>Nella versione web i dati restano <b>solo su questo dispositivo</b>: storico, magazzino, rese, acquirenti, tariffe, siti, parametri e moduli. Non c’è un cloud e non serve un account.</p><p>Per non perderli, o per portarli su un altro telefono o PC, fai ogni tanto una copia: Menu → <b>I miei dati</b> → <b>Esporta e recupera</b> → <b>Scarica un file</b>. Sull’altro dispositivo usa <b>Carica da un file</b>.</p><p>Cancellare i dati del sito dal browser cancella anche quelli dell’app.</p>',a:'bk'},\n"
        "    {g:'App',t:'Privacy, accesso e avvertenze',k:'privacy dati personali informativa avvertenze responsabilità consigli acquisto richiesta accesso approvazione codice invito statistiche anonime gdpr cookie',h:'<p>Ramometro <b>non raccoglie dati personali</b>: niente account, email o nome. I dati restano su questo dispositivo.</p><p>Alla prima apertura <b>chiedi l’accesso</b> dall’app: il gestore lo approva, oppure l’app lo approva da sola se il gestore ha scelto così. Il gestore vede solo il codice casuale della richiesta e, se rispondi, come hai conosciuto Ramometro e per che uso. Se hai ricevuto un <b>codice d’invito</b>, tocca <b>Ho già un codice</b>.</p><p>L’app conta solo <b>numeri totali</b> (aperture, calcoli, salvataggi), senza sapere chi sei.</p><p>Ramometro fa <b>stime e calcoli, non dà consigli di acquisto</b>: ogni decisione e responsabilità resta tua. Leggi le <b>Avvertenze d’uso</b> e l’<b>Informativa privacy</b> in Menu → <b>Aiuto</b> → <b>Privacy e avvertenze</b>.</p>',a:'legal'},")
must_re(r"\{id:'bk',nv:'6\.17\.0',t:'Salvataggio continuo e copia di sicurezza',.*?\]\},",
        "{id:'bk',nv:'6.17.0',t:'Copia di sicurezza su file',s:'I dati restano sul dispositivo: come conservarli',k:'backup copia sicurezza cloud salvare recuperare ripristino file dispositivo telefono nuovo tablet',st:[{x:'Nella versione web i dati restano <b>solo su questo dispositivo</b>.',el:'#bkOpen',p:{menu:'root'}},{x:'Apri il <b>Menu</b> e tocca <b>Esporta e recupera</b>.',el:'#bkOpen',p:{menu:'root'}},{x:'<b>Scarica un file</b> salva tutti i dati: conservalo dove vuoi.',el:'#bkOpen',p:{menu:'root'}},{x:'Su un altro telefono o PC apri l’app e tocca <b>Carica da un file</b>.',el:'#bkOpen',p:{menu:'root'}}]},")
must_re(r"\{id:'set',",
        "{id:'legal',nv:'6.23.5',t:'Privacy e avvertenze',s:'Nessun dato personale, ogni decisione è tua',k:'privacy dati personali avvertenze responsabilità richiesta accesso approvazione codice invito statistiche',st:[{x:'Apri il <b>Menu</b>: in <b>Aiuto</b> trovi <b>Privacy e avvertenze</b>.',el:'#rmLeg',p:{menu:'root'}},{x:'L’<b>Informativa privacy</b> spiega che i dati restano sul dispositivo, che l’accesso si chiede senza dati personali e che l’app conta solo numeri totali.',el:'#rmLeg',p:{menu:'root'}},{x:'Le <b>Avvertenze d’uso</b> spiegano che l’app fa stime e non dà consigli di acquisto: ogni decisione è tua.',el:'#rmLeg',p:{menu:'root'}}]},\n      {id:'set',")
must_re(r"H\.bk=\{t:'Copia di sicurezza',s:\[.*?\],n:\[.*?\]\}",
        "H.bk={t:'Copia di sicurezza',s:['Nella versione web i dati restano solo su questo dispositivo: non c’è un cloud.','Tocca <b>Scarica un file</b> e conservalo dove vuoi: è la tua copia di sicurezza.','Su un altro telefono o PC, o dopo un problema, tocca <b>Carica da un file</b>.'],n:['Il file contiene storico, magazzino, rese, acquirenti, tariffe, siti, parametri e moduli, con le foto delle matasse dei calcoli nello storico.','Se il file viene da una versione più nuova dell’app ti avviso prima di recuperarlo.','Prima di ogni recupero salvo i dati presenti: puoi tornare indietro.','Cancellare i dati del sito dal browser cancella anche quelli dell’app: fai copie spesso.']}")
must("'<b>Riconoscimenti</b>: il logo, chi ha realizzato l’app e le fonti dei dati.'",
     "'<b>Riconoscimenti</b>: il logo, chi ha realizzato l’app e le fonti dei dati.','<b>Privacy e avvertenze</b>: nessun dato personale; l’app fa stime, non dà consigli di acquisto.'")

# 8 · traduzioni dei testi nuovi più brevi
ROWS = [
    ["Copia di sicurezza su file", "Backup to a file", "Copia de seguridad en archivo", "Sauvegarde dans un fichier", "Sicherung als Datei", "Cópia de segurança em ficheiro", "Резервная копия в файл", "备份到文件"],
    ["Storico, apprendimento, copie, stampe", "History, learning, backups, prints", "Historial, aprendizaje, copias, impresiones", "Historique, apprentissage, copies, impressions", "Verlauf, Lernen, Kopien, Drucke", "Histórico, aprendizagem, cópias, impressões", "История, обучение, копии, печать", "历史、学习、备份、打印"],
    ["Copie su file e ripristino", "File backups and restore", "Copias en archivo y restauración", "Copies dans un fichier et restauration", "Kopien als Datei und Wiederherstellung", "Cópias em ficheiro e restauro", "Копии в файл и восстановление", "文件备份与恢复"],
    ["Senza rete: l’app funziona e i dati restano sul dispositivo.", "No network: the app works and your data stays on the device.", "Sin red: la app funciona y los datos se quedan en el dispositivo.", "Pas de réseau : l’app fonctionne et les données restent sur l’appareil.", "Kein Netz: Die App funktioniert, die Daten bleiben auf dem Gerät.", "Sem rede: a app funciona e os dados ficam no dispositivo.", "Нет сети: приложение работает, данные остаются на устройстве.", "无网络：应用照常工作，数据保存在设备上。"],
    ["Rete tornata.", "Network is back.", "Red recuperada.", "Réseau rétabli.", "Netz wieder da.", "Rede de volta.", "Сеть восстановлена.", "网络已恢复。"],
    ["Vuoi fare copie di sicurezza dei tuoi dati su file?", "Do you want to back up your data to a file?", "¿Quieres hacer copias de seguridad de tus datos en archivo?", "Voulez-vous sauvegarder vos données dans un fichier ?", "Möchtest du deine Daten als Datei sichern?", "Queres fazer cópias de segurança dos teus dados em ficheiro?", "Хотите делать резервные копии данных в файл?", "要把数据备份到文件吗？"],
    ["Privacy e avvertenze", "Privacy and disclaimer", "Privacidad y advertencias", "Confidentialité et avertissements", "Datenschutz und Hinweise", "Privacidade e avisos", "Конфиденциальность и предупреждения", "隐私与免责声明"],
    ["Nessun dato personale · ogni decisione è tua", "No personal data · every decision is yours", "Ningún dato personal · cada decisión es tuya", "Aucune donnée personnelle · chaque décision vous appartient", "Keine personenbezogenen Daten · jede Entscheidung liegt bei dir", "Nenhum dado pessoal · cada decisão é tua", "Никаких личных данных · все решения за вами", "不收集个人数据 · 每个决定由你做出"],
    ["Dati sul dispositivo e copie su file", "Data on the device and file backups", "Datos en el dispositivo y copias en archivo", "Données sur l’appareil et copies dans un fichier", "Daten auf dem Gerät und Kopien als Datei", "Dados no dispositivo e cópias em ficheiro", "Данные на устройстве и копии в файл", "数据保存在设备上，备份到文件"],
    ["Privacy, accesso e avvertenze", "Privacy, access and disclaimer", "Privacidad, acceso y advertencias", "Confidentialité, accès et avertissements", "Datenschutz, Zugang und Hinweise", "Privacidade, acesso e avisos", "Конфиденциальность, доступ и предупреждения", "隐私、访问与免责声明"],
]
k = s.index('["Prossimo cavo",')
s = s[:k] + ''.join(json.dumps(r, ensure_ascii=False) + ',\n' for r in ROWS) + s[k:]

open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(s)

# 9 · pagine: informativa, avvertenze, area riservata
pages.write(out)
subprocess.run(['npx', 'esbuild', 'src/admin.js', '--bundle', '--minify', '--format=iife', '--target=es2019',
                '--outfile=' + os.path.join(os.path.abspath(out), 'admin.min.js'), '--log-level=warning'], cwd=here, check=True)
adm = open(os.path.join(here, 'src/admin.html'), encoding='utf-8').read().replace('<!--CONFIG-->', '<script>window.__RM_FB=%s;</script>' % json.dumps(cfg))
open(os.path.join(out, 'admin.html'), 'w', encoding='utf-8').write(adm)

# 10 · service worker: funziona anche senza rete, aggiorna appena c'è
ver = hashlib.sha1((s + pages.DATA).encode()).hexdigest()[:10]
pre = ['./', 'index.html', 'manifest.json', 'privacy.html', 'avvertenze.html', 'fonts/fonts.css'] + [i['src'] for i in icons]
open(os.path.join(out, 'sw.js'), 'w').write("""const C='rm-%s';const F=%s;
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(F)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==C).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{const r=e.request;if(r.method!=='GET'||new URL(r.url).origin!==location.origin)return;
e.respondWith(fetch(r).then(x=>{if(x.ok){const y=x.clone();caches.open(C).then(c=>c.put(r,y))}return x}).catch(()=>caches.match(r).then(x=>x||caches.match('index.html'))))});
""" % (ver, json.dumps(pre)))
open(os.path.join(out, '.nojekyll'), 'w').write('')
print('ok', out, len(s), 'byte · icone', [i['src'] for i in icons], '· font', len(glob.glob(os.path.join(out, 'fonts/*.woff2'))))
