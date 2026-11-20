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
    s = s[:m[0].start()] + (new(m[0]) if callable(new) else new) + s[m[0].end():]


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
        "{g:'App',t:'Dati sul dispositivo e copie su file',k:'cloud salvataggio continuo sincronizza dispositivi telefono tablet computer copia sicurezza dati persi file versione web',h:'<p>Nella versione web i dati restano <b>solo su questo dispositivo</b>: storico, magazzino, rese, acquirenti, tariffe, siti, parametri e moduli. Non c’è un cloud e non serve un account.</p><p>Per non perderli, o per portarli su un altro telefono o PC, fai ogni tanto una copia: Menu → <b>I miei dati</b> → <b>Esporta e recupera</b> → <b>Scarica un file</b>. Sull’altro dispositivo usa <b>Carica da un file</b>.</p><p>Cancellare i dati del sito dal browser cancella anche quelli dell’app.</p>',a:'bk'},")
must_re(r"\{id:'bk',nv:'6\.17\.0',t:'Salvataggio continuo e copia di sicurezza',.*?\]\},",
        "{id:'bk',nv:'6.17.0',t:'Copia di sicurezza su file',s:'I dati restano sul dispositivo: come conservarli',k:'backup copia sicurezza cloud salvare recuperare ripristino file dispositivo telefono nuovo tablet',st:[{x:'Nella versione web i dati restano <b>solo su questo dispositivo</b>.',el:'#bkOpen',p:{menu:'root'}},{x:'Apri il <b>Menu</b> e tocca <b>Esporta e recupera</b>.',el:'#bkOpen',p:{menu:'root'}},{x:'<b>Scarica un file</b> salva tutti i dati: conservalo dove vuoi.',el:'#bkOpen',p:{menu:'root'}},{x:'Su un altro telefono o PC apri l’app e tocca <b>Carica da un file</b>.',el:'#bkOpen',p:{menu:'root'}}]},")
# privacy: dalla 6.24.0 l'app ha la sua pagina «Privacy e avvertenze» (Menu › Aiuto); la web ne cambia testi, Guida e tutorial
LEG_G = "{g:'App',t:'Privacy, accesso e avvertenze',k:'privacy dati personali informativa avvertenze responsabilità consigli acquisto richiesta accesso approvazione codice invito statistiche anonime gdpr cookie',h:'<p>Ramometro <b>non raccoglie dati personali</b>: niente account, email o nome. I dati restano su questo dispositivo.</p><p>Alla prima apertura <b>chiedi l’accesso</b> dall’app: il gestore lo approva, oppure l’app lo approva da sola se il gestore ha scelto così. Il gestore vede solo il codice casuale della richiesta e, se rispondi, come hai conosciuto Ramometro e per che uso. Se hai ricevuto un <b>codice d’invito</b>, tocca <b>Ho già un codice</b>.</p><p>L’app conta solo <b>numeri totali</b> (aperture, calcoli, salvataggi), senza sapere chi sei.</p><p>Ramometro fa <b>stime e calcoli, non dà consigli di acquisto</b>: ogni decisione e responsabilità resta tua. Leggi le <b>Avvertenze d’uso</b> e l’<b>Informativa privacy</b> in Menu → <b>Aiuto</b> → <b>Privacy e avvertenze</b>.</p>',a:'legal'},"
LEG_T = "{id:'legal',nv:'6.23.5',t:'Privacy e avvertenze',s:'Nessun dato personale, ogni decisione è tua',k:'privacy dati personali avvertenze responsabilità richiesta accesso approvazione codice invito statistiche',st:[{x:'Apri il <b>Menu</b>: in <b>Aiuto</b> trovi <b>Privacy e avvertenze</b>.',el:'#rmLeg',p:{menu:'root'}},{x:'L’<b>Informativa privacy</b> spiega che i dati restano sul dispositivo, che l’accesso si chiede senza dati personali e che l’app conta solo numeri totali.',el:'#rmLeg',p:{menu:'root'}},{x:'Le <b>Avvertenze d’uso</b> spiegano che l’app fa stime e non dà consigli di acquisto: ogni decisione è tua.',el:'#rmLeg',p:{menu:'root'}}]}"
if '<div class="pvw" id="pvLeg" hidden>' in s:
    must_re(r"\{g:'App',t:'Privacy e avvertenze',k:'[^']*',h:'[^']*',a:'leg',al:'Apri «Privacy e avvertenze»'\},",
            LEG_G.replace("a:'legal'},", "a:'leg',al:'Apri «Privacy e avvertenze»'},"))
    must_re(r"\{id:'legal',nv:'[0-9.]+',t:'Privacy e avvertenze',.*?\]\},\n",
            LEG_T.replace("el:'#rmLeg',p:{menu:'root'}", "el:'#lgBd',p:{menu:'leg'}").replace("el:'#lgBd',p:{menu:'leg'}", "el:'#pvMenu [data-go=\"leg\"]',p:{menu:'root'}", 1) + ",\n", re.S)
else:
    must_re(r"(\{g:'App',t:'Dati sul dispositivo e copie su file',k:'[^']*',h:'[^']*',a:'bk'\},)", lambda m: m.group(1) + "\n    " + LEG_G)
    must_re(r"\{id:'set',", LEG_T + ",\n      {id:'set',")
must_re(r"H\.bk=\{t:'Copia di sicurezza',s:\[.*?\],n:\[.*?\]\}",
        "H.bk={t:'Copia di sicurezza',s:['Nella versione web i dati restano solo su questo dispositivo: non c’è un cloud.','Tocca <b>Scarica un file</b> e conservalo dove vuoi: è la tua copia di sicurezza.','Su un altro telefono o PC, o dopo un problema, tocca <b>Carica da un file</b>.'],n:['Il file contiene storico, magazzino, rese, acquirenti, tariffe, siti, parametri e moduli, con le foto delle matasse dei calcoli nello storico.','Se il file viene da una versione più nuova dell’app ti avviso prima di recuperarlo.','Prima di ogni recupero salvo i dati presenti: puoi tornare indietro.','Cancellare i dati del sito dal browser cancella anche quelli dell’app: fai copie spesso.']}")
must("'<b>Riconoscimenti</b>: il logo, chi ha realizzato l’app e le fonti dei dati.'",
     "'<b>Riconoscimenti</b>: il logo, chi ha realizzato l’app e le fonti dei dati.','<b>Privacy e avvertenze</b>: nessun dato personale; l’app fa stime, non dà consigli di acquisto.'")


# 7b · mercato, avvisi e AI nella web (20/11/2026)
# borsa e notizie da data/market.json (aggiornato da GitHub Actions), al posto del database di claude.ai
must("var cl=window.claude,db=cl&&cl.use?await cl.use('db'):null;if(!db)return;", "var db=window.__WEBDB||null;if(!db)return;")
# niente email del gestore nelle pagine pubbliche
must_re(r"var MAIL='[^'@]+@[^']+';", "var MAIL='';")
# Avvisi e soglie: nella web niente compito pianificato, notifiche o mail; le soglie si controllano all'apertura
must_re(r"  function paintAl\(\)\{.*?\n    b\.innerHTML=h\}",
        "  function paintAl(){\n    var b=$('alBd');if(!b)return;var c=cfg,h='';\n"
        "    h+='<div class=\"alsec\">'+sw('on',c.on,T('Avvisi all’apertura'),T('Quando apri l’app controllo le soglie del rame con l’ultimo prezzo di borsa'))+'</div>';\n"
        "    h+='<p class=\"note\">'+T('Nella versione web non ci sono notifiche né mail: gli avvisi compaiono in alto quando apri l’app. Il prezzo di borsa si aggiorna da solo due volte al giorno, nei giorni feriali.')+'</p>';\n"
        "    h+='<button type=\"button\" class=\"gact algo\" data-go=\"cu\">'+T('Modifica le soglie del rame')+'</button>';\n"
        "    h+='<button type=\"button\" class=\"gact\" data-k=\"reset\">'+T('Ripristina i valori iniziali')+'</button>';\n"
        "    b.innerHTML=h}", re.S)
must("var act=cfg.on&&(cfg.push||cfg.mail);\n    e.textContent=act?(every()===60?T('Attivi · ogni ora'):TF('Attivi · ogni {0}',minL(every()))):T('Spenti');",
     "e.textContent=cfg.on?T('Attivi all’apertura'):T('Spenti');")
for old, new in [
    ("T('A ogni controllo il compito legge il prezzo del rame su Kitco e lo confronta con quello di 24 ore e di 7 giorni prima.')",
     "T('Quando apri l’app confronto l’ultimo prezzo di borsa LME con quello del giorno di borsa prima e di una settimana prima.')"),
    ("T('Ogni soglia avvisa una volta sola e si riattiva quando il prezzo torna indietro. I prezzi in €/kg sono quelli di borsa (Kitco), non il prezzo a cui vendi.')",
     "T('Ogni soglia avvisa una volta sola e si riattiva quando il prezzo torna indietro. I prezzi in €/kg sono quelli di borsa (LME), non il prezzo a cui vendi.')"),
    ("T('Le variazioni a 24 ore e a 7 giorni si calcolano dopo un giorno e una settimana di controlli.')",
     "T('Le variazioni si calcolano con gli ultimi prezzi di borsa, aggiornati due volte al giorno nei giorni feriali.')"),
    ("T('Non salvato nel database: le scelte restano su questo dispositivo.')", "T('Le scelte restano su questo dispositivo.')"),
    ("'<span class=\"mdt ai\">usa crediti AI</span>'", "'<span class=\"mdt ai\">AI solo su claude.ai</span>'"),
]:
    must(old, new)

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
ROWS += [["Avvisi all’apertura", "Alerts when opening", "Avisos al abrir", "Alertes à l’ouverture", "Hinweise beim Öffnen", "Avisos ao abrir", "Оповещения при открытии", "打开时提醒"], ["Attivi all’apertura", "On when opening", "Activos al abrir", "Actives à l’ouverture", "Beim Öffnen aktiv", "Ativos ao abrir", "Включены при открытии", "打开时启用"], ["Quando apri l’app controllo le soglie del rame con l’ultimo prezzo di borsa", "When you open the app I check your copper thresholds against the latest exchange price", "Al abrir la app compruebo tus umbrales del cobre con el último precio de bolsa", "À l’ouverture de l’app, je vérifie vos seuils du cuivre avec le dernier cours de bourse", "Beim Öffnen der App prüfe ich deine Kupfer-Schwellen mit dem letzten Börsenpreis", "Ao abrir a app verifico os teus limites do cobre com o último preço de bolsa", "При открытии приложения я сверяю ваши пороги по меди с последней биржевой ценой", "打开应用时，我会用最新交易所价格检查你的铜价阈值"], ["Nella versione web non ci sono notifiche né mail: gli avvisi compaiono in alto quando apri l’app. Il prezzo di borsa si aggiorna da solo due volte al giorno, nei giorni feriali.", "The web version has no notifications or emails: alerts appear at the top when you open the app. The exchange price updates by itself twice a day on weekdays.", "En la versión web no hay notificaciones ni correos: los avisos aparecen arriba al abrir la app. El precio de bolsa se actualiza solo dos veces al día, en días laborables.", "La version web n’a ni notifications ni e-mails : les alertes s’affichent en haut à l’ouverture de l’app. Le cours de bourse se met à jour tout seul deux fois par jour, en semaine.", "In der Web-Version gibt es keine Benachrichtigungen oder E-Mails: Hinweise erscheinen oben, wenn du die App öffnest. Der Börsenpreis aktualisiert sich werktags zweimal täglich von selbst.", "Na versão web não há notificações nem e-mails: os avisos aparecem no topo ao abrir a app. O preço de bolsa atualiza-se sozinho duas vezes por dia, nos dias úteis.", "В веб-версии нет уведомлений и писем: оповещения появляются вверху при открытии приложения. Биржевая цена обновляется сама дважды в день по будням.", "网页版没有通知或邮件：打开应用时提醒会显示在顶部。交易所价格在工作日每天自动更新两次。"], ["Quando apri l’app confronto l’ultimo prezzo di borsa LME con quello del giorno di borsa prima e di una settimana prima.", "When you open the app I compare the latest LME price with the previous trading day and with one week earlier.", "Al abrir la app comparo el último precio LME con el del día de bolsa anterior y con el de una semana antes.", "À l’ouverture de l’app, je compare le dernier cours LME avec celui de la séance précédente et d’une semaine avant.", "Beim Öffnen der App vergleiche ich den letzten LME-Preis mit dem vorigen Börsentag und mit dem von vor einer Woche.", "Ao abrir a app comparo o último preço LME com o do dia de bolsa anterior e com o de uma semana antes.", "При открытии приложения я сравниваю последнюю цену LME с ценой предыдущего торгового дня и недельной давности.", "打开应用时，我会把最新 LME 价格与上一交易日和一周前的价格比较。"], ["Ogni soglia avvisa una volta sola e si riattiva quando il prezzo torna indietro. I prezzi in €/kg sono quelli di borsa (LME), non il prezzo a cui vendi.", "Each threshold alerts only once and re-arms when the price moves back. Prices in €/kg are exchange prices (LME), not the price you sell at.", "Cada umbral avisa una sola vez y se reactiva cuando el precio vuelve atrás. Los precios en €/kg son de bolsa (LME), no el precio al que vendes.", "Chaque seuil n’alerte qu’une fois et se réarme quand le prix revient. Les prix en €/kg sont ceux de la bourse (LME), pas votre prix de vente.", "Jede Schwelle meldet sich nur einmal und wird wieder aktiv, wenn der Preis zurückgeht. Preise in €/kg sind Börsenpreise (LME), nicht dein Verkaufspreis.", "Cada limite avisa só uma vez e reativa-se quando o preço volta atrás. Os preços em €/kg são de bolsa (LME), não o preço a que vendes.", "Каждый порог срабатывает один раз и снова включается, когда цена возвращается. Цены в €/кг — биржевые (LME), а не ваша цена продажи.", "每个阈值只提醒一次，价格回落后重新生效。€/kg 价格为交易所价格（LME），不是你的卖价。"], ["Le variazioni si calcolano con gli ultimi prezzi di borsa, aggiornati due volte al giorno nei giorni feriali.", "Changes are worked out from the latest exchange prices, updated twice a day on weekdays.", "Las variaciones se calculan con los últimos precios de bolsa, actualizados dos veces al día en días laborables.", "Les variations sont calculées avec les derniers cours, mis à jour deux fois par jour en semaine.", "Die Veränderungen werden aus den letzten Börsenpreisen berechnet, werktags zweimal täglich aktualisiert.", "As variações calculam-se com os últimos preços de bolsa, atualizados duas vezes por dia nos dias úteis.", "Изменения считаются по последним биржевым ценам, которые обновляются дважды в день по будням.", "变化根据最新交易所价格计算，工作日每天更新两次。"], ["Le scelte restano su questo dispositivo.", "Your choices stay on this device.", "Tus opciones se quedan en este dispositivo.", "Vos choix restent sur cet appareil.", "Deine Auswahl bleibt auf diesem Gerät.", "As tuas escolhas ficam neste dispositivo.", "Ваш выбор сохраняется на этом устройстве.", "你的选择保存在此设备上。"], ["AI solo su claude.ai", "AI only on claude.ai", "IA solo en claude.ai", "IA seulement sur claude.ai", "KI nur auf claude.ai", "IA só no claude.ai", "ИИ только на claude.ai", "AI 仅限 claude.ai"], ["solo su claude.ai", "only on claude.ai", "solo en claude.ai", "seulement sur claude.ai", "nur auf claude.ai", "só no claude.ai", "только на claude.ai", "仅限 claude.ai"], ["Avviso sul rame", "Copper alert", "Aviso sobre el cobre", "Alerte cuivre", "Kupfer-Hinweis", "Aviso sobre o cobre", "Оповещение по меди", "铜价提醒"], ["Rame in calo: {0} % in un giorno di borsa", "Copper down: {0} % in one trading day", "Cobre a la baja: {0} % en un día de bolsa", "Cuivre en baisse : {0} % en une séance", "Kupfer fällt: {0} % an einem Börsentag", "Cobre em queda: {0} % num dia de bolsa", "Медь дешевеет: {0} % за торговый день", "铜价下跌：一个交易日 {0} %"], ["Rame in calo: {0} % in una settimana di borsa", "Copper down: {0} % in one trading week", "Cobre a la baja: {0} % en una semana de bolsa", "Cuivre en baisse : {0} % en une semaine de bourse", "Kupfer fällt: {0} % in einer Börsenwoche", "Cobre em queda: {0} % numa semana de bolsa", "Медь дешевеет: {0} % за торговую неделю", "铜价下跌：一个交易周 {0} %"], ["Rame in salita: {0} % in un giorno di borsa", "Copper up: {0} % in one trading day", "Cobre al alza: {0} % en un día de bolsa", "Cuivre en hausse : {0} % en une séance", "Kupfer steigt: {0} % an einem Börsentag", "Cobre em alta: {0} % num dia de bolsa", "Медь дорожает: {0} % за торговый день", "铜价上涨：一个交易日 {0} %"], ["Rame in salita: {0} % in una settimana di borsa", "Copper up: {0} % in one trading week", "Cobre al alza: {0} % en una semana de bolsa", "Cuivre en hausse : {0} % en une semaine de bourse", "Kupfer steigt: {0} % in einer Börsenwoche", "Cobre em alta: {0} % numa semana de bolsa", "Медь дорожает: {0} % за торговую неделю", "铜价上涨：一个交易周 {0} %"], ["Rame sotto la tua soglia: {0} €/kg", "Copper below your threshold: {0} €/kg", "Cobre por debajo de tu umbral: {0} €/kg", "Cuivre sous votre seuil : {0} €/kg", "Kupfer unter deiner Schwelle: {0} €/kg", "Cobre abaixo do teu limite: {0} €/kg", "Медь ниже вашего порога: {0} €/кг", "铜价低于你的阈值：{0} €/kg"], ["Rame sopra la tua soglia: {0} €/kg", "Copper above your threshold: {0} €/kg", "Cobre por encima de tu umbral: {0} €/kg", "Cuivre au-dessus de votre seuil : {0} €/kg", "Kupfer über deiner Schwelle: {0} €/kg", "Cobre acima do teu limite: {0} €/kg", "Медь выше вашего порога: {0} €/кг", "铜价高于你的阈值：{0} €/kg"], ["Borsa LME del {0}: {1} $/t", "LME on {0}: {1} $/t", "Bolsa LME del {0}: {1} $/t", "LME du {0} : {1} $/t", "LME vom {0}: {1} $/t", "Bolsa LME de {0}: {1} $/t", "LME на {0}: {1} $/т", "{0} LME：{1} $/t"]]
k = s.index('["Prossimo cavo",')
s = s[:k] + ''.join(json.dumps(r, ensure_ascii=False) + ',\n' for r in ROWS) + s[k:]

open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(s)

# 9 · pagine: informativa, avvertenze, area riservata; dati di mercato di partenza per GitHub Actions
pages.NEUTRE = "'MARGINE OK'" in s
pages.write(out)
os.makedirs(os.path.join(out, 'data'), exist_ok=True)
subprocess.run(['node', os.path.join(here, 'tools/estrai_data.js'), os.path.join(out, 'index.html'), os.path.join(out, 'data/base.json')], check=True)
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
