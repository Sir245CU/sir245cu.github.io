"""Pagine statiche del sito: Informativa privacy e Avvertenze d'uso (testi approvati il 19/11/2026)."""
GEST = 'SIR 245 Urban Mining'
NEUTRE = False   # True con l'app 6.24.0 o successiva (Margine ok, Margine basso, In perdita, Prezzo limite)
MERCATO = True   # borsa, cambio e notizie aggiornati da GitHub Actions (data/market.json)
DATA = '25/11/2026'        # Informativa privacy (6.29.0: tolto «magazzino»; prima 20/11/2026)
DATA_AVV = '25/11/2026'    # Avvertenze d'uso (6.29.0: tolti spedizioni e Filo; prima 21/11/2026, sezione Browser)

PRIVACY = [
    ('In breve', '''<p><b>Ramometro non raccoglie dati personali.</b> Non chiede nome, email o telefono, non ha account e non usa cookie di profilazione né pubblicità.</p>
<p>Calcoli, storico e impostazioni restano sul tuo dispositivo. Online passano solo la richiesta d’accesso (o la verifica di un codice d’invito) e alcuni contatori anonimi, senza nulla che permetta di riconoscerti.</p>'''),
    ('Chi gestisce l’app', f'''<p>Ramometro è sviluppata e gestita da <b>{GEST}</b>. Poiché l’app non raccoglie dati personali, non c’è un archivio di utenti a cui chiedere accesso o cancellazione. Per domande rivolgiti a chi ti ha dato il codice d’invito.</p>'''),
    ('Cosa resta sul tuo dispositivo', '''<p>L’app salva nella memoria del browser del tuo telefono o PC:</p>
<ul><li>calcoli, storico e impostazioni;</li>
<li>l’abilitazione ottenuta (richiesta approvata o codice d’invito), il codice casuale della richiesta e l’accettazione delle Avvertenze d’uso;</li>
<li>un promemoria che evita di contare due volte lo stesso giorno o mese nelle statistiche;</li>
<li>una copia dell’app, per usarla anche senza rete.</li></ul>
<p>Sono strumenti tecnici necessari al funzionamento: non richiedono consenso e nessuno li legge a distanza. Le copie di sicurezza che scarichi (Menu › I miei dati › Esporta e recupera) sono file tuoi e restano dove li salvi.</p>
<p>Per cancellare tutto, cancella i dati del sito dalle impostazioni del browser, oppure disinstalla l’app dal telefono.</p>'''),
    ('Accesso su approvazione', '''<p>Alla prima apertura chiedi l’accesso dall’app. La richiesta contiene solo:</p>
<ul><li>un codice casuale creato dall’app (per esempio K7M-Q3X), che non è collegato a te;</li>
<li>data e ora della richiesta;</li>
<li>se scegli di rispondere, come hai conosciuto Ramometro (passaparola, fiera o evento, internet, altro) e per che uso (privato o professionale).</li></ul>
<p>Il gestore approva o rifiuta la richiesta, oppure l’app la approva da sola se il gestore ha scelto l’approvazione automatica. <b>Il gestore non sa chi sei</b>: se vuoi, puoi mostrargli di persona il codice della tua richiesta.</p>
<p>In alternativa puoi usare un codice d’invito ricevuto dal gestore: il sistema conta solo <b>quante volte</b> è stato attivato, senza registrare chi lo usa.</p>
<p>Quando c’è rete, l’app controlla che l’accesso sia ancora attivo. Se il gestore lo ritira, l’app si blocca su questo dispositivo, ma i dati restano qui e si possono sempre esportare. Le richieste restano nel database finché il gestore non le cancella.</p>'''),
    ('Statistiche anonime', '''<p>Per sapere quanto viene usata l’app, ogni dispositivo aggiunge 1 ad alcuni contatori comuni:</p>
<ul><li>aperture, dispositivi attivi nel giorno e nel mese, nuove attivazioni;</li>
<li>calcoli fatti per tipo, esiti del calcolo, salvataggi, copie del riepilogo e stampe;</li>
<li>versione dell’app, telefono o PC, app installata o no;</li>
<li>richieste d’accesso e risposte facoltative (come hai conosciuto Ramometro, per che uso);</li>
<li>risposta sì o no alla domanda «Ramometro ti è utile?».</li></ul>
<p>I contatori sono solo totali e sono conservati in Europa (Milano). Non contengono identificativi, indirizzi IP, posizione, testi o importi dei tuoi calcoli, e non si possono ricondurre a un dispositivo o a una persona.</p>'''),
    ('Servizi tecnici di altri', '''<p>Come ogni sito, Ramometro passa da fornitori tecnici che ricevono l’indirizzo IP del tuo dispositivo per consegnare i dati. Noi non lo riceviamo e non lo conserviamo.</p>
<div class="tw"><table><thead><tr><th>Servizio</th><th>A cosa serve</th><th>Cosa riceve</th><th>Informativa</th></tr></thead><tbody>
<tr><td>GitHub Pages (GitHub)</td><td>ospita il sito sir245cu.github.io</td><td>indirizzo IP, che GitHub registra per sicurezza (<a href="https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages" target="_blank" rel="noopener">dettagli</a>)</td><td><a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement" target="_blank" rel="noopener">GitHub General Privacy Statement</a></td></tr>
<tr><td>Google Firebase, Cloud Firestore (Google)</td><td>richieste d’accesso, codici d’invito e contatori anonimi</td><td>indirizzo IP durante il collegamento</td><td><a href="https://firebase.google.com/support/privacy" target="_blank" rel="noopener">Privacy and Security in Firebase</a></td></tr>
</tbody></table></div>
<p>I caratteri del testo e le librerie per leggere PDF ed Excel sono ospitati sul sito stesso: il browser non li scarica da altri. {MKT}</p>'''),
    ('Cosa non facciamo', '''<ul><li>Nessun account, nessuna email, nessun nome o numero di telefono.</li>
<li>Nessun cookie di profilazione o di terze parti, nessuna pubblicità.</li>
<li>Nessun Google Analytics o strumento simile.</li>
<li>Nessuna vendita o cessione di dati.</li>
<li>Nessuna intelligenza artificiale nella versione web: foto e testi che usi nell’app non escono dal dispositivo.</li></ul>'''),
    ('Diritti, modifiche e data', f'''<p>L’app non raccoglie dati che permettano di identificarti, quindi non abbiamo dati personali da mostrarti, correggere o cancellare. Quelli sul tuo dispositivo li gestisci tu; per l’indirizzo IP valgono le informative di GitHub e Google. Puoi rivolgerti al Garante per la protezione dei dati personali (<a href="https://www.garanteprivacy.it" target="_blank" rel="noopener">garanteprivacy.it</a>).</p>
<p>Se cambia il modo in cui funziona l’app, aggiorniamo questa pagina e la data. Vedi anche le <a href="avvertenze.html">Avvertenze d’uso</a>.</p>
<p class="mut">Ultimo aggiornamento: {DATA}.</p>'''),
]

AVVERTENZE = [
    ('In breve', '''<p><b>Ramometro è uno strumento di calcolo.</b> Stima il rame contenuto nei cavi e il margine teorico a partire dai dati che inserisci tu.</p>
<p><b>Non offre suggerimenti né consigli di acquisto o vendita di metalli</b>, e nemmeno consulenza finanziaria, fiscale o legale. Ogni decisione (se comprare, quanto, a che prezzo, a chi vendere) e ogni responsabilità che ne deriva restano esclusivamente tue.</p>'''),
    ('Cosa sono i risultati', '''<p>Le scritte {RIS}, i colori e le soglie sono il <b>risultato aritmetico</b> di formule applicate ai tuoi dati e al margine minimo che hai scelto tu.</p>
<p>Non sono raccomandazioni, valutazioni del materiale, perizie né offerte di acquisto. Cambiano appena cambi un dato.</p>'''),
    ('Stime, non misure', '''<p>Rese, sezioni, densità, pesi teorici e tabelle tecniche sono valori indicativi, presi da schede dei produttori e da medie. Un cavo reale può essere diverso:</p>
<ul><li>sezioni fuori tolleranza o conduttori sottodimensionati;</li>
<li>conduttori in alluminio ramato (CCA) o in alluminio scambiati per rame;</li>
<li>stagnatura, schermi, armature, isolanti e riempitivi diversi da quelli previsti;</li>
<li>umidità, sporco, olio, sfridi e perdite di lavorazione.</li></ul>
<p>Le stime da foto e le letture automatiche, dove presenti, possono sbagliare. Pesa il materiale con una bilancia affidabile e verifica sempre di persona.</p>'''),
    ('Prezzi e dati di mercato', '''<p>Quotazioni del rame (LME e altre borse), cambi, listini dei rottami e prezzi degli annunci vengono da <b>fonti di terzi</b>: possono essere in ritardo, incompleti o sbagliati, e cambiano di continuo. {AGG}</p>
<p>Non sono offerte: il prezzo vero lo fa chi compra il tuo rame, al momento della consegna, secondo qualità, quantità e condizioni di mercato.</p>'''),
    ('Norme da rispettare, a cura tua', '''<p>L’app non controlla il rispetto delle norme. In particolare:</p>
<ul><li><b>Rifiuti.</b> Cavi e rottami di rame possono essere rifiuti. Chi li raccoglie e trasporta come attività deve essere iscritto all’Albo nazionale gestori ambientali (art. 212 d.lgs. 152/2006; per i metalli anche la categoria 4-bis) e rispettare formulari, registri e tracciabilità.</li>
<li><b>Provenienza del materiale.</b> I furti di rame sono frequenti. Comprare materiale di provenienza illecita può costituire ricettazione (art. 648 c.p.) o acquisto di cose di sospetta provenienza (art. 712 c.p.). Verifica chi vende e da dove viene il materiale.</li>
<li><b>Niente fuoco.</b> Bruciare i cavi per togliere la guaina è vietato e pericoloso: è il reato di combustione illecita di rifiuti (art. 256-bis d.lgs. 152/2006).</li>
<li><b>Fisco.</b> L’app non calcola imposte, IVA né altri adempimenti. Le cessioni di rottami tra soggetti IVA seguono di regola l’inversione contabile (art. 74, commi 7 e 8, d.P.R. 633/1972). Chiedi al tuo commercialista.</li></ul>
<p>Questo elenco non è completo e le norme cambiano: non sostituisce il parere di un professionista.</p>'''),
    ('Browser', '''<p>Ramometro funziona con Chrome, Edge, Safari, Samsung Internet e Firefox aggiornati. Con browser più vecchi può perdere colori o funzioni. Non usarla dentro il browser interno di altre app (WhatsApp, Facebook, Instagram, Telegram) né in navigazione privata: lì dati e accesso possono andare persi.</p>'''),
    ('Sicurezza', '''<p>Tagliare e spellare cavi può causare ferite: usa attrezzi adatti, guanti e occhiali. Non lavorare mai su cavi collegati alla corrente. I tempi di spellatura dell’app sono stime.</p>'''),
    ('Nessuna garanzia', '''<p>Ramometro è fornita gratuitamente, «così com’è». Può contenere errori di calcolo o di programma, può non essere sempre disponibile e può cambiare o essere interrotta in qualsiasi momento.</p>
<p>I dati restano sul tuo dispositivo e possono andare persi, per esempio cancellando i dati del browser: fai spesso una copia su file (Menu › I miei dati › Esporta e recupera › Scarica un file).</p>'''),
    ('Limitazione di responsabilità', f'''<p>Nei limiti consentiti dalla legge, {GEST} non risponde di perdite, mancati guadagni o altri danni, diretti o indiretti, derivanti dall’uso dell’app o dall’affidamento sui suoi risultati.</p>
<p>Restano salvi i casi di dolo o colpa grave (art. 1229 c.c.) e i diritti che la legge riconosce ai consumatori e che non si possono escludere.</p>'''),
    ('Link e marchi di terzi', '''<p>L’app contiene collegamenti a siti di annunci, listini, schede tecniche e notizie. Non siamo affiliati a questi siti e non rispondiamo dei loro contenuti. Nomi e marchi appartengono ai rispettivi titolari.</p>'''),
    ('Intelligenza artificiale', '''<p>Nella versione su claude.ai alcune funzioni usano l’AI (lettura di foto e annunci, prezzi dal web, km). Danno stime che possono essere sbagliate e consumano crediti dell’account Claude: controlla sempre il risultato. Nella versione web l’AI non c’è.</p>'''),
    ('Accesso su approvazione', '''<p>L’uso è personale e su approvazione del gestore, che può approvare le richieste a mano o in automatico e ritirare l’accesso in qualsiasi momento, senza obbligo di motivazione. I dati sul tuo dispositivo restano tuoi e si possono esportare.</p>'''),
    ('Accettazione, modifiche e legge applicabile', f'''<p>Chiedendo l’accesso o attivando un codice d’invito dichiari di aver letto e accettato queste avvertenze. Possono cambiare: la data qui sotto indica l’ultima versione. Si applica la legge italiana.</p>
<p>Gestore dell’app: <b>{GEST}</b>. Vedi anche l’<a href="privacy.html">Informativa privacy</a>.</p>
<p class="mut">Ultimo aggiornamento: {DATA_AVV}.</p>'''),
]

CSS = '''@import url("fonts/fonts.css");
:root{--accent:#0f6f66;--ink:#142326;--muted:#566b70;--line:#d5dee1;--bg:#f4f7f7;--surface:#fff;--tint:#e4f1ef}
@media (prefers-color-scheme:dark){:root{--accent:#5cc3b8;--ink:#e6eef0;--muted:#9fb3b7;--line:#2b3b3f;--bg:#0f1719;--surface:#16211f;--tint:#1d2f2c}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 "IBM Plex Sans",system-ui,sans-serif}
main{max-width:760px;margin:0 auto;padding:20px 18px 48px}
header{display:flex;align-items:center;gap:12px;margin:4px 0 18px}
header img{width:44px;height:44px;border-radius:10px}
header b{font-family:"Archivo Black",system-ui,sans-serif;font-size:1.25em;letter-spacing:.01em}
h1{font-size:1.55em;margin:0 0 6px;line-height:1.25}
.lead{color:var(--muted);margin:0 0 18px}
section{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:6px 18px 10px;margin:12px 0}
h2{font-family:"IBM Plex Sans Condensed","IBM Plex Sans",sans-serif;font-weight:600;font-size:1.15em;color:var(--accent);margin:14px 0 6px}
p{margin:8px 0}ul{margin:8px 0;padding-left:22px}li{margin:4px 0}
a{color:var(--accent);font-weight:600}
.mut{color:var(--muted);font-size:.92em}
.tw{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.93em;margin:8px 0}
th,td{border:1px solid var(--line);padding:8px;text-align:left;vertical-align:top}
th{background:var(--tint)}
.back{display:inline-flex;align-items:center;min-height:44px;padding:0 16px;border-radius:10px;border:1px solid var(--line);background:var(--surface);text-decoration:none;margin-top:14px}
.back:hover{border-color:var(--accent);background:var(--tint)}
nav{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 0}'''


def page(title, lead, sections):
    body = '\n'.join(f'<section><h2>{t}</h2>\n{h}</section>' for t, h in sections)
    return f'''<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#0f6f66">
<title>{title} · Ramometro</title>
<link rel="icon" href="icons/icon-192x192.png">
<style>{CSS}</style>
</head>
<body>
<main>
<header><img src="icons/icon-192x192.png" alt=""><b>Ramometro</b></header>
<h1>{title}</h1>
<p class="lead">{lead}</p>
{body}
<nav><a class="back" href="./">Torna a Ramometro</a><a class="back" href="{'avvertenze.html' if 'Privacy' in title else 'privacy.html'}">{'Avvertenze d’uso' if 'Privacy' in title else 'Informativa privacy'}</a></nav>
</main>
</body>
</html>
'''


def _fill(sections):
    ris = ('«Margine ok», «Margine basso», «In perdita», il «Prezzo limite»' if NEUTRE else
           '«Conviene», «Da trattare», «Non conviene», il «Paga al massimo»')
    agg = ('Nella versione web la borsa LME, il cambio e i titoli delle notizie si aggiornano da soli due volte al giorno nei giorni feriali; il resto alla pubblicazione dell’app.'
           if MERCATO else 'Nella versione web sono aggiornati solo alla pubblicazione dell’app.')
    mkt = ('Borsa, cambio e notizie li scarica dalle fonti pubbliche un’automazione di GitHub, due volte al giorno: il tuo dispositivo li legge dal sito stesso, senza mandare nulla di tuo.'
           if MERCATO else '')
    return [(t, h.replace('{RIS}', ris).replace('{AGG}', agg).replace(' {MKT}', ' ' + mkt if mkt else '')) for t, h in sections]


def write(out):
    import os
    open(os.path.join(out, 'privacy.html'), 'w', encoding='utf-8').write(
        page('Informativa privacy', 'Ramometro non raccoglie dati personali. Qui trovi cosa resta sul tuo dispositivo e cosa passa online.', _fill(PRIVACY)))
    open(os.path.join(out, 'avvertenze.html'), 'w', encoding='utf-8').write(
        page('Avvertenze d’uso e responsabilità', 'Ramometro fa stime e calcoli: non dà consigli di acquisto. Ogni decisione e responsabilità resta di chi usa l’app.', _fill(AVVERTENZE)))
