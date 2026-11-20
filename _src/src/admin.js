// Ramometro · area riservata al gestore: codici d'invito e statistiche anonime
import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup, signInWithRedirect, getRedirectResult, onAuthStateChanged, signOut } from 'firebase/auth';
import { getFirestore, collection, doc, getDoc, getDocs, setDoc, updateDoc, deleteDoc, Timestamp } from 'firebase/firestore/lite';

const app = initializeApp(window.__RM_FB);
const auth = getAuth(app);
const db = getFirestore(app);
getRedirectResult(auth).catch(() => {});
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const SITE = 'https://sir245cu.github.io';
const AB = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';

function msg(t, bad) { const m = $('msg'); m.textContent = t || ''; m.className = 'msg' + (bad ? ' bad' : ''); }
function fdate(ms) { return ms ? new Date(ms).toLocaleDateString('it-IT') : '—'; }
function randCode() { const a = new Uint32Array(8); crypto.getRandomValues(a); let s = ''; for (let i = 0; i < 8; i++) s += AB[a[i] % AB.length]; return s.slice(0, 4) + '-' + s.slice(4); }

$('in').onclick = async () => {
  const p = new GoogleAuthProvider();
  try { await signInWithPopup(auth, p); } catch (e) { if (/popup/.test(e.code || '')) return signInWithRedirect(auth, p); msg('Accesso non riuscito: ' + (e.code || e.message), true); }
};
$('out').onclick = () => signOut(auth);

onAuthStateChanged(auth, async u => {
  $('who').textContent = u ? u.email : '';
  $('in').hidden = !!u; $('out').hidden = !u;
  $('app').hidden = true;
  if (!u) { msg('Accedi con l’account del gestore.'); return; }
  msg('Carico…');
  try { await loadAccess(); await loadReqs(); await loadCodes(); await loadStats(); $('app').hidden = false; msg(''); startAuto(); }
  catch (e) { msg(e && e.code === 'permission-denied' ? 'Accesso riservato al gestore dell’app (oppure le regole del database non sono ancora aggiornate).' : 'Errore: ' + (e.code || e.message), true); }
});

/* ---------- codici d'invito ---------- */
let codes = [];
async function loadCodes() {
  const s = await getDocs(collection(db, 'codes'));
  codes = s.docs.map(d => ({ id: d.id, ...d.data() })).sort((a, b) => (b.at?.toMillis?.() || 0) - (a.at?.toMillis?.() || 0));
  paintCodes();
}
function state(c) {
  if (!c.on) return 'Ritirato';
  if ((c.used || 0) >= (c.max || 0)) return 'Esaurito';
  if (c.exp && c.exp.toMillis() < Date.now()) return 'Scaduto per nuove attivazioni';
  return 'Attivo';
}
function paintCodes() {
  const t = $('codes');
  if (!codes.length) { t.innerHTML = '<p class="mut">Nessun codice. Creane uno qui sopra.</p>'; return; }
  t.innerHTML = '<div class="tw"><table class="rq"><thead><tr><th>Codice</th><th>Attivazioni</th><th>Attivabile fino al</th><th>Stato</th><th>Creato</th><th></th></tr></thead><tbody>' +
    codes.map(c => `<tr><td class="code">${esc(c.id)}</td><td data-l="Attivazioni">${c.used || 0} di ${c.max || 0}</td><td data-l="Attivabile fino al">${c.exp ? fdate(c.exp.toMillis()) : 'nessun limite'}</td><td data-l="Stato">${state(c)}</td><td data-l="Creato">${c.at ? fdate(c.at.toMillis()) : '—'}</td>
      <td class="acts"><button data-a="copy" data-c="${esc(c.id)}">Copia</button>${navigator.share ? `<button data-a="share" data-c="${esc(c.id)}">Invia</button>` : ''}<button data-a="${c.on ? 'off' : 'on'}" data-c="${esc(c.id)}">${c.on ? 'Ritira' : 'Riattiva'}</button><button data-a="del" data-c="${esc(c.id)}" class="bad">Elimina</button></td></tr>`).join('') +
    '</tbody></table></div><p class="mut">Ritirare o eliminare un codice blocca l’app sui dispositivi che lo usano (alla prossima apertura con rete); i loro dati restano sul dispositivo e si possono esportare.</p>';
}
function invite(c) { return `Ecco il tuo codice d’invito per Ramometro: ${c}\nApri ${SITE} e scrivilo alla prima apertura.`; }
let armed = '';
$('codes').onclick = async e => {
  const b = e.target.closest('button[data-a]'); if (!b) return;
  const c = b.dataset.c, a = b.dataset.a;
  try {
    if (a === 'copy') { await navigator.clipboard.writeText(invite(c)); msg('Messaggio con il codice ' + c + ' copiato.'); return; }
    if (a === 'share') { await navigator.share({ text: invite(c) }); return; }
    if (a === 'del') {
      if (armed !== c) { armed = c; b.textContent = 'Tocca ancora'; setTimeout(() => { if (armed === c) { armed = ''; b.textContent = 'Elimina'; } }, 3000); return; }
      armed = ''; await deleteDoc(doc(db, 'codes', c)); msg('Codice ' + c + ' eliminato.');
    } else await updateDoc(doc(db, 'codes', c), { on: a === 'on' });
    await loadCodes();
  } catch (err) { if (err && err.name === 'AbortError') return; msg('Operazione non riuscita: ' + (err.code || err.message), true); }
};
$('mk').onclick = async () => {
  const max = Math.max(1, Math.min(500, parseInt($('max').value, 10) || 1));
  const d = $('exp').value ? new Date($('exp').value + 'T23:59:59') : null;
  $('mk').disabled = true;
  try {
    let c = '';
    for (let i = 0; i < 5; i++) { c = randCode(); const s = await getDoc(doc(db, 'codes', c)); if (!s.exists()) break; }
    await setDoc(doc(db, 'codes', c), { max, used: 0, on: true, exp: d ? Timestamp.fromDate(d) : null, at: Timestamp.now() });
    msg('Creato il codice ' + c + '. Copialo o invialo dall’elenco.');
    await loadCodes();
  } catch (e) { msg('Creazione non riuscita: ' + (e.code || e.message), true); }
  $('mk').disabled = false;
};

/* ---------- statistiche ---------- */
const COLS = [['att', 'Dispositivi attivi'], ['ap', 'Aperture'], ['rq', 'Richieste d’accesso'], ['nuovi', 'Nuovi dispositivi'], ['cm', 'Calcoli a metro'], ['cw', 'Calcoli per peso'], ['cs', 'Somme'],
  ['vg', 'Esito «Margine ok»'], ['vt', 'Esito «Margine basso»'], ['vn', 'Esito «In perdita»'], ['sv', 'Salvataggi'], ['co', 'Copie riepilogo'], ['st', 'Stampe PDF'],
  ['tel', 'Da telefono'], ['pc', 'Da PC'], ['pwa', 'Da app installata'], ['r7', 'Tornati dopo 7+ giorni'], ['r30', 'Tornati dopo 30+ giorni']];
function pad(n) { return (n < 10 ? '0' : '') + n; }
function ymd(d) { return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }
async function loadStats() {
  const s = await getDocs(collection(db, 'stats'));
  const all = {}; s.docs.forEach(d => { all[d.id] = d.data(); });
  const days = []; const now = new Date();
  for (let i = 29; i >= 0; i--) { const d = new Date(now); d.setDate(now.getDate() - i); days.push(ymd(d)); }
  const g = (id, k) => (all[id] && all[id][k]) || 0;
  const tot = all.tot || {};
  const thisM = 'm-' + ymd(now).slice(0, 7);
  const sum = (k, n) => days.slice(-n).reduce((a, d) => a + g('d-' + d, k), 0);
  const calc = n => sum('cm', n) + sum('cw', n) + sum('cs', n);
  const us = tot.us || 0, un = tot.un || 0;
  const bars = (el, rows) => { const t = Math.max(1, ...rows.map(r => r[1])); $(el).innerHTML = '<div class="bars">' + rows.map(([l, v]) => `<span>${l}</span><i style="width:${Math.round(v * 100 / t)}%"></i><b>${v}</b>`).join('') + '</div>'; };
  const rq = tot.rq || 0, k = n => tot[n] || 0;
  bars('src', [['Passaparola', k('kpp')], ['Fiera o evento', k('kfi')], ['Internet', k('kin')], ['Altro', k('kal')], ['Non ha risposto', Math.max(0, rq - k('kpp') - k('kfi') - k('kin') - k('kal'))]]);
  bars('uso', [['Privato', k('upr')], ['Professionale', k('upf')], ['Non ha risposto', Math.max(0, rq - k('upr') - k('upf'))]]);
  $('kpi').innerHTML = [
    ['Attivi questo mese', g(thisM, 'att'), 'dispositivi diversi'],
    ['Attivi oggi', g('d-' + days[29], 'att'), 'dispositivi'],
    ['Calcoli in 30 giorni', calc(30), 'completi'],
    ['Richieste d’accesso', rq, (tot.ra || 0) + ' approvate in automatico'],
    ['Dispositivi entrati', tot.nuovi || 0, 'con richiesta o codice'],
    ['«Ti è utile?»', us + un ? Math.round(us * 100 / (us + un)) + ' % sì' : '—', us + ' sì · ' + un + ' no']
  ].map(([t, v, s]) => `<div class="kpi"><small>${t}</small><b>${v}</b><small>${s}</small></div>`).join('');
  // grafico: dispositivi attivi al giorno, ultimi 30 giorni
  const vals = days.map(d => g('d-' + d, 'att')), mx = Math.max(1, ...vals), W = 600, H = 160, bw = W / 30;
  $('chart').innerHTML = `<svg viewBox="0 0 ${W} ${H + 22}" role="img" aria-label="Dispositivi attivi al giorno negli ultimi 30 giorni">` +
    vals.map((v, i) => { const h = Math.round(v / mx * H); return `<rect x="${i * bw + 2}" y="${H - h}" width="${bw - 4}" height="${h}" rx="2"><title>${days[i]}: ${v}</title></rect>`; }).join('') +
    `<line x1="0" y1="${H}" x2="${W}" y2="${H}"/><text x="0" y="${H + 16}">${fdate(Date.parse(days[0]))}</text><text x="${W}" y="${H + 16}" text-anchor="end">oggi</text><text x="${W}" y="12" text-anchor="end">max ${mx}</text></svg>`;
  // tabella giornaliera (più recenti in alto)
  const rows = days.slice().reverse().filter(d => all['d-' + d]);
  $('days').innerHTML = rows.length ? '<div class="tw"><table><thead><tr><th>Giorno</th>' + COLS.map(c => `<th>${c[1]}</th>`).join('') + '</tr></thead><tbody>' +
    rows.map(d => '<tr><td>' + fdate(Date.parse(d)) + '</td>' + COLS.map(c => `<td>${g('d-' + d, c[0])}</td>`).join('') + '</tr>').join('') + '</tbody></table></div>' : '<p class="mut">Ancora nessun dato negli ultimi 30 giorni.</p>';
  // mesi e versioni
  const ms = Object.keys(all).filter(k => k.startsWith('m-')).sort().reverse().slice(0, 12);
  $('months').innerHTML = ms.length ? '<div class="tw"><table><thead><tr><th>Mese</th><th>Dispositivi attivi</th><th>Nuove attivazioni</th></tr></thead><tbody>' +
    ms.map(m => `<tr><td>${m.slice(2)}</td><td>${g(m, 'att')}</td><td>${g(m, 'nuovi')}</td></tr>`).join('') + '</tbody></table></div>' : '<p class="mut">Nessun dato.</p>';
  const vs = Object.keys(all).filter(k => k.startsWith('v-')).sort().reverse();
  $('vers').innerHTML = vs.length ? '<div class="tw"><table><thead><tr><th>Versione</th><th>Giorni-dispositivo</th></tr></thead><tbody>' +
    vs.map(v => `<tr><td>${esc(v.slice(2))}</td><td>${g(v, 'att')}</td></tr>`).join('') + '</tbody></table></div>' : '<p class="mut">Nessun dato.</p>';
}
$('rl').onclick = async () => { msg('Aggiorno…'); try { await loadReqs(); await loadStats(); await loadCodes(); msg(''); } catch (e) { msg('Errore: ' + (e.code || e.message), true); } };

/* ---------- accesso: approvazione manuale o automatica ---------- */
async function loadAccess() {
  const s = await getDoc(doc(db, 'access', 'config'));
  const c = s.exists() ? s.data() : {};
  document.querySelector('input[name=am][value=' + (c.auto ? 'auto' : 'man') + ']').checked = true;
  $('open').checked = c.open !== false;
  $('mxd').value = c.maxDay || 0;
  note(c);
}
function note(c) {
  $('accNote').textContent = c.open === false ? 'Nuove richieste chiuse: chi apre l’app per la prima volta non può chiedere l’accesso.'
    : c.auto ? 'Approvazione automatica: chi chiede l’accesso entra subito' + (c.maxDay ? `, fino a ${c.maxDay} al giorno; oltre il limite le richieste restano in attesa.` : '.')
    : 'Approvazione manuale: ogni richiesta aspetta che tu la approvi qui sotto.';
}
$('sva').onclick = async () => {
  const c = { auto: document.querySelector('input[name=am]:checked').value === 'auto', open: $('open').checked, maxDay: Math.max(0, Math.min(1000, parseInt($('mxd').value, 10) || 0)) };
  $('sva').disabled = true;
  try { await setDoc(doc(db, 'access', 'config'), c); note(c); msg('Impostazioni dell’accesso salvate.'); } catch (e) { msg('Salvataggio non riuscito: ' + (e.code || e.message), true); }
  $('sva').disabled = false;
};

/* ---------- richieste d'accesso ---------- */
const SRCL = { pp: 'Passaparola', fi: 'Fiera o evento', in: 'Internet', al: 'Altro' }, USOL = { pr: 'Privato', pf: 'Professionale' };
const shown = r => r.slice(0, 3) + '-' + r.slice(3, 6);
const fdt = t => t ? t.toDate().toLocaleString('it-IT', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—';
let reqs = [];
async function loadReqs() {
  const s = await getDocs(collection(db, 'requests'));
  reqs = s.docs.map(d => ({ id: d.id, ...d.data() })).sort((a, b) => (b.at?.toMillis?.() || 0) - (a.at?.toMillis?.() || 0));
  paintReqs();
}
function rrow(r, acts) {
  return `<tr><td class="code">${esc(shown(r.id))}</td><td data-l="Arrivata">${fdt(r.at)}</td><td data-l="Come ci ha conosciuto">${SRCL[r.src] || '—'}</td><td data-l="Uso">${USOL[r.uso] || '—'}</td><td class="acts">${acts}</td></tr>`;
}
function rtable(list, acts, empty) {
  return list.length ? '<div class="tw"><table class="rq"><thead><tr><th>Codice</th><th>Arrivata</th><th>Come ci ha conosciuto</th><th>Uso</th><th></th></tr></thead><tbody>' + list.map(r => rrow(r, acts(r))).join('') + '</tbody></table></div>' : `<p class="mut">${empty}</p>`;
}
function paintReqs() {
  const pend = reqs.filter(r => r.st === 'attesa'), ok = reqs.filter(r => r.st === 'ok'), no = reqs.filter(r => r.st === 'no');
  $('pendT').textContent = 'Richieste in attesa' + (pend.length ? ' (' + pend.length + ')' : '');
  document.title = (pend.length ? '(' + pend.length + ') ' : '') + 'Area riservata · Ramometro';
  $('okAll').hidden = pend.length < 2; $('okAll').textContent = 'Approva tutte (' + pend.length + ')';
  $('pend').innerHTML = rtable(pend, r => `<button data-r="ok" data-i="${r.id}" class="p">Approva</button><button data-r="no" data-i="${r.id}" class="bad">Rifiuta</button>`, 'Nessuna richiesta in attesa.');
  $('appr').innerHTML = rtable(ok, r => `<button data-r="no" data-i="${r.id}">Ritira</button><button data-r="del" data-i="${r.id}" class="bad">Elimina</button>`, 'Ancora nessun accesso approvato.') +
    (ok.length ? '<p class="mut">Ritirare o eliminare un accesso blocca l’app su quel dispositivo alla prossima apertura con rete; i dati restano sul dispositivo e si possono esportare.</p>' : '');
  $('rej').innerHTML = rtable(no, r => `<button data-r="ok" data-i="${r.id}">Approva</button><button data-r="del" data-i="${r.id}" class="bad">Elimina</button>`, 'Nessuna.');
}
let armedR = '';
async function onReq(e) {
  const b = e.target.closest('button[data-r]'); if (!b) return;
  const id = b.dataset.i, a = b.dataset.r;
  try {
    if (a === 'del') {
      if (armedR !== id) { armedR = id; b.textContent = 'Tocca ancora'; setTimeout(() => { if (armedR === id) { armedR = ''; b.textContent = 'Elimina'; } }, 3000); return; }
      armedR = ''; await deleteDoc(doc(db, 'requests', id));
    } else await updateDoc(doc(db, 'requests', id), { st: a, dec: Timestamp.now() });
    await loadReqs();
  } catch (err) { msg('Operazione non riuscita: ' + (err.code || err.message), true); }
}
['pend', 'appr', 'rej'].forEach(k => { $(k).onclick = onReq; });
$('okAll').onclick = async () => {
  $('okAll').disabled = true;
  try { for (const r of reqs.filter(r => r.st === 'attesa')) await updateDoc(doc(db, 'requests', r.id), { st: 'ok', dec: Timestamp.now() }); await loadReqs(); msg('Richieste approvate.'); }
  catch (e) { msg('Operazione non riuscita: ' + (e.code || e.message), true); }
  $('okAll').disabled = false;
};
let autoT = 0;
function startAuto() { clearInterval(autoT); autoT = setInterval(() => { if (document.visibilityState === 'visible') loadReqs().catch(() => {}); }, 60000); }
