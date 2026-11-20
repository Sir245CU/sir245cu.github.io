/* Ramometro web · strato per la versione pubblica (dal 19/11/2026)
   Criterio: nessun dato personale.
   - Niente account e niente cloud personale: i dati dell'app restano sul dispositivo (IndexedDB, in mancanza localStorage).
   - Uso su invito: un codice, verificato una volta; il sistema conta solo le attivazioni del codice.
   - Statistiche: solo contatori totali (Firestore, via REST), nessun identificativo.
   - AI spenta (nessun costo).
*/
(function () {
  'use strict';
  var CFG = window.__RM_FB || {};
  var PID = CFG.projectId, KEY = CFG.apiKey;
  var ROOT = PID ? 'projects/' + PID + '/databases/(default)/documents' : '';
  var API = 'https://firestore.googleapis.com/v1/';
  var D = document, W = window;
  var AVV = '2026-11-20';                       // versione delle Avvertenze accettate
  var LS = {
    g: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    s: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
    d: function (k) { try { localStorage.removeItem(k); } catch (e) {} },
    j: function (k) { try { return JSON.parse(localStorage.getItem(k) || 'null'); } catch (e) { return null; } }
  };
  function clone(v) { return v === undefined ? undefined : JSON.parse(JSON.stringify(v)); }

  /* ---------- 1 · archivio sul dispositivo al posto del cloud ---------- */
  var idbP = null;
  function idb() {
    if (!idbP) idbP = new Promise(function (ok) {
      try {
        var r = indexedDB.open('rm-local', 1);
        r.onupgradeneeded = function () { r.result.createObjectStore('docs'); };
        r.onsuccess = function () { ok(r.result); };
        r.onerror = function () { ok(null); };
        r.onblocked = function () { ok(null); };
      } catch (e) { ok(null); }
    });
    return idbP;
  }
  function tx(mode, fn) {
    return idb().then(function (db) {
      if (!db) return fn(null);
      return new Promise(function (ok, ko) {
        try {
          var st = db.transaction('docs', mode).objectStore('docs'), r = fn(st);
          r.onsuccess = function () { ok(r.result); };
          r.onerror = function () { ko(r.error); };
        } catch (e) { ko(e); }
      });
    });
  }
  function iget(k) { return tx('readonly', function (st) { if (!st) { var v = LS.g('rmdb:' + k); return v ? JSON.parse(v) : undefined; } return st.get(k); }); }
  function iput(k, v) { return tx('readwrite', function (st) { if (!st) { LS.s('rmdb:' + k, JSON.stringify(v)); return; } return st.put(v, k); }); }
  function idel(k) { return tx('readwrite', function (st) { if (!st) { LS.d('rmdb:' + k); return; } return st.delete(k); }); }
  function makeDoc(path) {
    path = String(path).split('/').filter(Boolean).join('/');
    var id = path.split('/').pop();
    return {
      path: path, id: id,
      get: function () { return iget(path).then(function (v) { var ex = v !== undefined && v !== null; return { exists: ex, id: id, data: function () { return ex ? clone(v) : undefined; } }; }); },
      set: function (data, opt) {
        return (opt && opt.merge ? iget(path) : Promise.resolve(null)).then(function (o) {
          return iput(path, clone(opt && opt.merge ? Object.assign({}, o || {}, data) : data));
        });
      },
      update: function (data) { return iget(path).then(function (o) { if (o == null) { var e = new Error('Documento assente'); e.code = 'not_found'; throw e; } return iput(path, clone(Object.assign({}, o, data))); }); },
      delete: function () { return idel(path); }
    };
  }
  var dbNS = { doc: makeDoc, collection: function (p) { return { doc: function (k) { return makeDoc(p + '/' + k); } }; } };
  var userNS = { id: function () { return Promise.resolve('locale'); }, me: function () { return Promise.resolve(null); } };
  W.claude = { use: function (n) { return Promise.resolve(n === 'db' ? dbNS : n === 'user' ? userNS : null); } };
  try { var ax = LS.j('cu_aix') || {}; ax.all = 1; LS.s('cu_aix', JSON.stringify(ax)); } catch (e) {}

  /* pulizia, una volta: account e copia locale del cloud della versione precedente (accesso con Google) */
  if (!LS.g('rm_clean')) {
    LS.s('rm_clean', '1');
    try {
      ['firebaseLocalStorageDb', 'firebase-heartbeat-database', 'firebase-installations-database'].forEach(function (n) { indexedDB.deleteDatabase(n); });
      if (indexedDB.databases) indexedDB.databases().then(function (l) { (l || []).forEach(function (x) { if (x && x.name && /^firestore\//.test(x.name)) indexedDB.deleteDatabase(x.name); }); }).catch(function () {});
    } catch (e) {}
  }

  /* ---------- 2 · Firestore via REST, senza accesso e senza identificativi ---------- */
  function val(v) {
    if (!v) return null;
    if ('integerValue' in v) return Number(v.integerValue);
    if ('doubleValue' in v) return Number(v.doubleValue);
    if ('booleanValue' in v) return !!v.booleanValue;
    if ('timestampValue' in v) return Date.parse(v.timestampValue);
    if ('stringValue' in v) return v.stringValue;
    return null;
  }
  function fsGet(path) {
    return fetch(API + ROOT + '/' + path + '?key=' + KEY, { cache: 'no-store', credentials: 'omit' }).then(function (r) {
      if (r.status === 404) return null;
      if (!r.ok) { var e = new Error('HTTP ' + r.status); e.status = r.status; throw e; }
      return r.json().then(function (j) { var o = {}, f = j.fields || {}; for (var k in f) o[k] = val(f[k]); return o; });
    });
  }
  function fsCommit(writes, keep) {
    return fetch(API + ROOT + ':commit?key=' + KEY, { method: 'POST', credentials: 'omit', keepalive: !!keep, headers: { 'content-type': 'application/json' }, body: JSON.stringify({ writes: writes }) }).then(function (r) {
      if (!r.ok) { var e = new Error('HTTP ' + r.status); e.status = r.status; throw e; }
    });
  }
  function incWrite(doc, fields) {
    var t = [];
    for (var k in fields) if (fields[k] > 0) t.push({ fieldPath: k, increment: { integerValue: String(fields[k]) } });
    return t.length ? { update: { name: ROOT + '/stats/' + doc, fields: {} }, updateMask: { fieldPaths: [] }, updateTransforms: t } : null;
  }

  /* ---------- 3 · statistiche anonime ---------- */
  var KEYS = ['ap', 'att', 'nuovi', 'r7', 'r30', 'tel', 'pc', 'pwa', 'cm', 'cw', 'cs', 'vg', 'vt', 'vn', 'sv', 'co', 'st', 'us', 'un', 'rq', 'ra', 'kpp', 'kfi', 'kin', 'kal', 'upr', 'upf'];
  var pend = {}, flT = 0;
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function today() { var d = new Date(); return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }
  function active() { var v = LS.j('rm_inv'); return !!(v && (v.c || v.r)); }
  function bump(k, n) { if (!active() || !PID) return; pend[k] = (pend[k] || 0) + (n || 1); clearTimeout(flT); flT = setTimeout(flush, 15000); }
  function flush(keep) {
    var p = pend, ks = Object.keys(p); if (!ks.length) return;
    pend = {};
    var dd = {}, rest = {}, n = 0;
    ks.forEach(function (k) { var v = Math.min(p[k], 50); if (KEYS.indexOf(k) >= 0 || k === 'matt' || k === 'mnew') { dd[k] = v; n++; } if (p[k] > 50) rest[k] = p[k] - 50; });
    if (!n) return;
    var day = {}, mon = {}, tot = {}, ver = {};
    KEYS.forEach(function (k) { if (dd[k]) day[k] = dd[k]; });
    if (dd.matt) mon.att = dd.matt;
    if (dd.mnew) mon.nuovi = dd.mnew;
    if (dd.nuovi) tot.nuovi = dd.nuovi;
    if (dd.us) tot.us = dd.us;
    if (dd.un) tot.un = dd.un;
    if (dd.att) { ver.att = dd.att; tot.att = dd.att; }
    var t = today(), vv = String(W.__REL || W.__VER || 'x').replace(/[^0-9A-Za-z._-]/g, '_').slice(0, 24);
    var w = [incWrite('d-' + t, day), incWrite('m-' + t.slice(0, 7), mon), incWrite('tot', tot), incWrite('v-' + vv, ver)].filter(Boolean);
    Object.keys(rest).forEach(function (k) { pend[k] = (pend[k] || 0) + rest[k]; });
    if (!w.length) return;
    fsCommit(w, keep).catch(function (e) {
      if (e && e.status && e.status !== 429 && e.status < 500) return;        // rifiutato dalle regole: non riprovo
      Object.keys(p).forEach(function (k) { pend[k] = (pend[k] || 0) + Math.min(p[k], 50); });
    });
  }
  D.addEventListener('visibilitychange', function () { if (D.visibilityState === 'hidden') flush(true); });
  W.addEventListener('pagehide', function () { flush(true); });

  function phone() { try { return matchMedia('(pointer:coarse)').matches && Math.min(screen.width, screen.height) < 700; } catch (e) { return false; } }
  function standalone() { try { return matchMedia('(display-mode: standalone)').matches || navigator.standalone === true; } catch (e) { return false; } }
  function opened() {                          // all'apertura: conteggi del giorno e del mese, una volta per dispositivo
    if (!active()) return;
    bump('ap');
    var st = LS.j('rm_st') || {}, t = today(), m = t.slice(0, 7), inv = LS.j('rm_inv') || {};
    if (st.d !== t) {
      st.d = t; bump('att'); bump(phone() ? 'tel' : 'pc'); if (standalone()) bump('pwa');
      var age = (Date.now() - (inv.t || Date.now())) / 864e5;
      if (age >= 7) bump('r7'); if (age >= 30) bump('r30');
    }
    if (st.m !== m) { st.m = m; bump('matt'); }
    LS.s('rm_st', JSON.stringify(st));
  }

  /* calcoli completi ed esiti: un calcolo conta quando il risultato resta uguale per qualche secondo */
  var seen = {}, cand = {}, MAP = { M: 'm', W: 'w', S: 's' }, CK = { m: 'cm', w: 'cw', s: 'cs' };
  function r2(x) { return Math.round((+x || 0) * 100) / 100; }
  function poll() {
    if (!active() || D.visibilityState === 'hidden') return;
    var CU = W.__CU, cur = null; try { cur = CU && CU.cur && CU.cur(); } catch (e) {}
    if (!cur) return;
    ['M', 'W', 'S'].forEach(function (K) {
      var k = MAP[K], e = D.getElementById('v' + K), c = cur[k];
      if (!e || e.hidden || !c || !e.offsetParent) { cand[k] = null; return; }
      var cl = e.classList.contains('good') ? 'vg' : e.classList.contains('mid') ? 'vt' : e.classList.contains('no') ? 'vn' : '';
      if (!cl) { cand[k] = null; return; }
      var sig = k + JSON.stringify([c.lab, r2(c.tot), r2(c.vend), r2((c.acq || 0) + (c.spe || 0)), cl]);
      if (seen[sig]) return;
      if (cand[k] !== sig) { cand[k] = sig; return; }
      seen[sig] = 1; cand[k] = null;
      bump(CK[k]); bump(cl);
      var n = (+LS.g('rm_uc') || 0) + 1; LS.s('rm_uc', String(n)); askUseful(n);
    });
  }
  setInterval(poll, 3000);
  D.addEventListener('click', function (ev) {
    var t = ev.target && ev.target.closest ? ev.target.closest('button') : null;
    if (!t || t.disabled) return;
    if (/^sv[123]$/.test(t.id)) bump('sv');
    else if (/^sh[123]$/.test(t.id)) bump('co');
    else if (t.id === 'prGo') bump('st');
  }, true);

  /* ---------- 4 · stile comune delle finestre di questo strato ---------- */
  var CSS = '\
.rmOv{position:fixed;inset:0;z-index:2147483000;background:rgba(10,20,22,.55);display:flex;align-items:center;justify-content:center;padding:16px}\
.rmOv[hidden]{display:none}\
.rmCard{background:var(--surface,#fff);color:var(--ink,#142326);width:min(520px,100%);max-height:calc(100vh - 32px);overflow:auto;border-radius:16px;padding:20px 20px 18px;box-shadow:0 10px 40px rgba(0,0,0,.3);font:inherit;line-height:1.45}\
.rmCard h2{margin:0 0 8px;font-size:1.25em}\
.rmCard h3{font-size:1em;margin:16px 0 6px;color:var(--accent,#0f6f66)}\
.rmCard p{margin:6px 0}\
.rmCard ol,.rmCard ul{margin:6px 0;padding-left:22px}\
.rmCard a{color:var(--accent,#0f6f66);font-weight:600}\
.rmMut{color:var(--muted,#566b70);font-size:.9em}\
.rmRow{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0 4px}\
.rmB{min-height:44px;padding:0 16px;border-radius:10px;border:1px solid var(--line,#d5dee1);background:var(--surface,#fff);color:var(--ink,#142326);font:inherit;font-weight:600;cursor:pointer;transition:background .15s,border-color .15s}\
.rmB:hover:not(:disabled){border-color:var(--accent,#0f6f66);background:var(--tint,#e4f1ef)}\
.rmB:disabled{opacity:.45;cursor:not-allowed}\
.rmP{background:var(--accent,#0f6f66);color:var(--accent-ink,#fff);border-color:var(--accent,#0f6f66)}\
.rmP:hover:not(:disabled){filter:brightness(1.08);background:var(--accent,#0f6f66)}\
.rmIn{width:100%;box-sizing:border-box;min-height:52px;padding:0 14px;border:1px solid var(--line,#d5dee1);border-radius:10px;background:var(--field,#fff);color:inherit;font:inherit;font-size:1.35em;letter-spacing:.12em;text-transform:uppercase;text-align:center}\
.rmIn:focus{outline:2px solid var(--accent,#0f6f66);outline-offset:1px}\
.rmChk{display:flex;gap:10px;align-items:flex-start;margin:14px 0 4px;cursor:pointer}\
.rmChk input{width:22px;height:22px;flex:none;margin:1px 0 0;accent-color:var(--accent,#0f6f66)}\
.rmMsg{min-height:1.4em;margin:8px 0 0;font-weight:600}\
.rmMsg.bad{color:var(--neg,#c0302b)}.rmMsg.ok{color:var(--accent,#0f6f66)}\
.rmLogo{display:flex;align-items:center;gap:10px;margin-bottom:6px}\
.rmLogo img{width:40px;height:40px;border-radius:10px}\
.rmLogo b{font-size:1.3em}\
#rmUse{position:fixed;left:50%;transform:translateX(-50%);bottom:calc(84px + env(safe-area-inset-bottom,0px));z-index:2147482000;width:min(440px,calc(100% - 24px));box-sizing:border-box;background:var(--surface,#fff);color:var(--ink,#142326);border:1px solid var(--line,#d5dee1);border-radius:14px;box-shadow:0 8px 30px rgba(0,0,0,.25);padding:10px 10px 10px 14px;display:flex;align-items:center;gap:8px;flex-wrap:nowrap;animation:rmIn .25s ease-out}\
#rmUse[hidden]{display:none}\
#rmUse b{flex:1 1 auto;min-width:0}\
#rmUse .rmB{min-height:40px}\
#rmUse .rmX{border:0;background:none;color:inherit;font-size:1.4em;line-height:1;cursor:pointer;padding:4px 8px;min-height:40px}\
@keyframes rmIn{from{opacity:0;transform:translate(-50%,8px)}to{opacity:1;transform:translate(-50%,0)}}\
@media (prefers-reduced-motion:reduce){#rmUse{animation:none}}\
.rmFs{border:1px solid var(--line,#d5dee1);border-radius:12px;margin:10px 0 0;padding:6px 10px 10px}\
.rmFs legend{padding:0 4px;font-size:.9em;color:var(--muted,#566b70)}\
.rmOpt{display:flex;flex-wrap:wrap;gap:6px}\
.rmOpt label{display:inline-flex;align-items:center;gap:6px;min-height:40px;padding:0 12px;border:1px solid var(--line,#d5dee1);border-radius:999px;cursor:pointer;transition:background .15s,border-color .15s}\
.rmOpt label:hover{border-color:var(--accent,#0f6f66);background:var(--tint,#e4f1ef)}\
.rmOpt input{-webkit-appearance:radio;appearance:auto;accent-color:var(--accent,#0f6f66);width:16px;height:16px;min-width:0;min-height:0;max-width:16px;padding:0;margin:0;flex:none;border:0;box-shadow:none;background:none}\
.rmCard [hidden]{display:none!important}\
.rmOpt label:has(input:checked){border-color:var(--accent,#0f6f66);background:var(--tint,#e4f1ef);font-weight:600}\
.rmBig{font:700 2em/1.2 ui-monospace,Menlo,monospace;letter-spacing:.12em;text-align:center;margin:4px 0 10px;padding:12px;border:2px dashed var(--accent,#0f6f66);border-radius:12px}\
.rmLinks{display:flex;gap:16px;flex-wrap:wrap;margin:4px 0}\
.rmL{border:0;background:none;padding:6px 0;min-height:40px;color:var(--accent,#0f6f66);font:inherit;font-weight:600;text-decoration:underline;cursor:pointer}\
[data-ax]{pointer-events:none;opacity:.5}\
.alsec:has([data-ax="all"])::after{content:"Nella versione web l’AI non è disponibile: usala nella versione su claude.ai.";display:block;font-size:.9em;margin:8px 4px 2px;line-height:1.4;color:var(--muted,#566b70)}\
.rmAlw{position:fixed;left:50%;transform:translateX(-50%);top:calc(70px + env(safe-area-inset-top,0px));z-index:2147482000;width:min(460px,calc(100% - 24px));box-sizing:border-box;background:var(--surface,#fff);color:var(--ink,#142326);border:2px solid var(--neg,#c0302b);border-radius:14px;box-shadow:0 10px 30px rgba(0,0,0,.18);padding:12px 14px}\
.rmAlw ul{margin:6px 0;padding-left:20px}.rmAlw li{margin:3px 0}.rmAlw small{color:var(--muted,#566b70)}\
.rmAlw .rmRow{display:flex;gap:8px;justify-content:flex-end;margin-top:8px}\
.rmAiB::after{content:attr(data-rmai);display:inline-block;margin:4px 0 0 6px;padding:1px 7px;border-radius:9px;font-size:.72rem;font-weight:600;line-height:1.5;background:#fde9c8;color:#6b4300;white-space:nowrap;vertical-align:middle;text-transform:none;letter-spacing:0}\
.alpsw,#spGo{display:none!important}';
  function el(h) { var t = D.createElement('template'); t.innerHTML = h.trim(); return t.content.firstChild; }
  function addCss() { if (D.getElementById('rmCss')) return; var s = D.createElement('style'); s.id = 'rmCss'; s.textContent = CSS; (D.head || D.documentElement).appendChild(s); }
  function wait(p, msg) { try { return W.__WAIT && W.__WAIT.track ? W.__WAIT.track(p, msg) : p; } catch (e) { return p; } }
  function icon() { var l = D.querySelector('link[rel="apple-touch-icon"]'); return l ? l.href : 'icons/icon-192x192.png'; }
  function fdate(t) { try { return new Date(t).toLocaleDateString('it-IT'); } catch (e) { return ''; } }

  /* ---------- 5 · accesso: richiesta dall'app (approvazione manuale o automatica) oppure codice d'invito ---------- */
  var AB = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
  function rid() { var a = new Uint32Array(16), s = ''; crypto.getRandomValues(a); for (var i = 0; i < 16; i++) s += AB[a[i] % AB.length]; return s; }
  function shown(r) { return r ? r.slice(0, 3) + '-' + r.slice(3, 6) : ''; }
  function norm(v) { v = String(v || '').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 8); return v.length > 4 ? v.slice(0, 4) + '-' + v.slice(4) : v; }
  function why(c) {
    if (!c) return 'Codice non valido: controlla lettere e numeri.';
    if (c.on !== true) return 'Questo codice non è più attivo.';
    if (c.exp && Date.now() > c.exp) return 'Questo codice è scaduto.';
    if ((c.used || 0) >= (c.max || 0)) return 'Questo codice è già stato usato il numero massimo di volte.';
    return '';
  }
  function netMsg(e) {
    if (e && e.status === 403) return 'L’accesso non è disponibile in questo momento: riprova più tardi.';
    if (navigator.onLine === false || !(e && e.status)) return 'Serve la rete: collegati e riprova.';
    return 'Operazione non riuscita: riprova tra poco.';
  }
  function statNow(f) {                          // contatori della richiesta: anche prima dell'approvazione, senza identificativi
    if (!PID) return;
    var t = today(), w = [incWrite('d-' + t, f), incWrite('tot', f)].filter(Boolean);
    if (w.length) fsCommit(w).catch(function () {});
  }
  var SRC = [['pp', 'Passaparola'], ['fi', 'Fiera o evento'], ['in', 'Internet'], ['al', 'Altro']];
  var USO = [['pr', 'Privato'], ['pf', 'Professionale']];
  function radios(name, list) {
    return '<div class="rmOpt" role="radiogroup">' + list.map(function (o) { return '<label><input type="radio" name="' + name + '" value="' + o[0] + '"><span>' + o[1] + '</span></label>'; }).join('') +
      '<label><input type="radio" name="' + name + '" value="" checked><span>Preferisco non dire</span></label></div>';
  }
  var gate = null, wT = 0;
  function view(v) { ['rmVReq', 'rmVWait', 'rmVCode'].forEach(function (id) { D.getElementById(id).hidden = id !== v; }); }
  function accOk() { return D.getElementById('rmAcc').checked; }
  function upd() {
    var a = accOk();
    D.getElementById('rmAsk').disabled = !a;
    D.getElementById('rmGo').disabled = !(a && norm(D.getElementById('rmCode').value).length === 9);
  }
  function say(t, cls) { var m = D.getElementById('rmGateM'); if (m) { m.textContent = t || ''; m.className = 'rmMsg' + (cls ? ' ' + cls : ''); } }
  function buildGate() {
    gate = el('<div class="rmOv" id="rmGate" role="dialog" aria-modal="true" aria-labelledby="rmGateT"><div class="rmCard">' +
      '<div class="rmLogo"><img alt="" src="' + icon() + '"><b>Ramometro</b></div>' +
      '<h2 id="rmGateT">Benvenuto in Ramometro</h2>' +
      '<p id="rmGateS">Ramometro si usa con l’approvazione di chi la gestisce. Chiedi l’accesso: non servono nome, email o telefono.</p>' +
      '<div id="rmVReq">' +
        '<fieldset class="rmFs"><legend>Facoltativo · Come hai conosciuto Ramometro?</legend>' + radios('rmSrc', SRC) + '</fieldset>' +
        '<fieldset class="rmFs"><legend>Facoltativo · Per che uso?</legend>' + radios('rmUso', USO) + '</fieldset>' +
      '</div>' +
      '<div id="rmVWait" hidden><p class="rmMut" style="margin-top:4px">Codice della tua richiesta</p><p class="rmBig" id="rmRc"></p>' +
        '<p>Quando il gestore approva la richiesta, l’app si apre da sola. Se lo conosci, puoi mostrargli questo codice di persona.</p>' +
        '<p class="rmMut" id="rmLast"></p></div>' +
      '<div id="rmVCode" hidden><label for="rmCode" class="rmMut">Codice d’invito</label>' +
        '<input id="rmCode" class="rmIn" inputmode="text" autocomplete="off" autocapitalize="characters" spellcheck="false" maxlength="9" placeholder="XXXX-XXXX"></div>' +
      '<label class="rmChk" id="rmChkL"><input type="checkbox" id="rmAcc"><span>Ho letto e accetto le <a href="avvertenze.html" target="_blank" rel="noopener">Avvertenze d’uso</a>: Ramometro fa stime e calcoli, non dà consigli di acquisto; ogni decisione è mia. Ho letto l’<a href="privacy.html" target="_blank" rel="noopener">Informativa privacy</a>.</span></label>' +
      '<p class="rmMsg" id="rmGateM" role="status" aria-live="polite"></p>' +
      '<div class="rmRow">' +
        '<button type="button" class="rmB rmP" id="rmAsk" disabled>Chiedi l’accesso</button>' +
        '<button type="button" class="rmB rmP" id="rmChk" hidden>Controlla ora</button>' +
        '<button type="button" class="rmB rmP" id="rmGo" hidden disabled>Attiva il codice</button>' +
        '<button type="button" class="rmB" id="rmDl" hidden>Scarica i miei dati</button>' +
      '</div>' +
      '<p class="rmLinks"><button type="button" class="rmL" id="rmToCode">Ho già un codice</button><button type="button" class="rmL" id="rmToReq" hidden>Chiedi l’accesso</button></p>' +
      '<p class="rmMut">Non chiediamo nome, email o telefono: i tuoi dati restano su questo dispositivo.</p>' +
      '</div></div>');
    D.body.appendChild(gate);
    var inp = D.getElementById('rmCode');
    D.getElementById('rmAcc').addEventListener('change', upd);
    inp.addEventListener('input', function () { var v = norm(inp.value); if (inp.value !== v) inp.value = v; upd(); });
    inp.addEventListener('keydown', function (e) { if (e.key === 'Enter' && !D.getElementById('rmGo').disabled) { e.preventDefault(); D.getElementById('rmGo').click(); } });
    D.getElementById('rmAsk').addEventListener('click', ask);
    D.getElementById('rmChk').addEventListener('click', function () { poll2(true); });
    D.getElementById('rmGo').addEventListener('click', function () { activate(norm(inp.value)); });
    D.getElementById('rmToCode').addEventListener('click', function () { mode('code'); });
    D.getElementById('rmToReq').addEventListener('click', function () { var q = LS.j('rm_req'); mode(q && q.st === 'attesa' ? 'wait' : 'req'); });
    D.getElementById('rmDl').addEventListener('click', function () { var b = D.getElementById('bkDl'); if (b) b.click(); });
  }
  function mode(m, note) {                       // req · wait · code · no (rifiutata) · off (ritirato)
    addCss(); if (!gate) buildGate();
    var q = LS.j('rm_req') || {}, S = D.getElementById('rmGateS'), T = D.getElementById('rmGateT');
    var isReq = m === 'req' || m === 'no' || m === 'off';
    view(m === 'wait' ? 'rmVWait' : m === 'code' ? 'rmVCode' : 'rmVReq');
    D.getElementById('rmAsk').hidden = !isReq;
    D.getElementById('rmAsk').textContent = m === 'req' ? 'Chiedi l’accesso' : 'Chiedi di nuovo';
    D.getElementById('rmChk').hidden = m !== 'wait';
    D.getElementById('rmGo').hidden = m !== 'code';
    D.getElementById('rmDl').hidden = m !== 'off';
    D.getElementById('rmChkL').hidden = m === 'wait';
    D.getElementById('rmToCode').hidden = m === 'code';
    D.getElementById('rmToReq').hidden = m !== 'code';
    D.getElementById('rmToReq').textContent = q.st === 'attesa' ? 'Torna alla mia richiesta' : 'Chiedi l’accesso';
    if (m === 'req') { T.textContent = 'Benvenuto in Ramometro'; S.textContent = 'Ramometro si usa con l’approvazione di chi la gestisce. Chiedi l’accesso: non servono nome, email o telefono.'; }
    else if (m === 'wait') { T.textContent = 'Richiesta inviata'; S.textContent = 'La tua richiesta è in attesa di approvazione.'; D.getElementById('rmRc').textContent = shown(q.r); }
    else if (m === 'code') { T.textContent = 'Codice d’invito'; S.textContent = 'Se hai ricevuto un codice da chi gestisce l’app, scrivilo qui.'; }
    else if (m === 'no') { T.textContent = 'Richiesta non approvata'; S.textContent = 'La richiesta ' + shown(q.r) + ' non è stata approvata. Puoi chiedere di nuovo più tardi o usare un codice d’invito.'; }
    else if (m === 'off') { T.textContent = 'Accesso ritirato'; S.textContent = 'L’accesso su questo dispositivo non è più attivo. I tuoi dati restano qui: puoi scaricarli in un file, chiedere di nuovo l’accesso o usare un codice.'; }
    say(note || '');
    upd(); gate.hidden = false;
    clearInterval(wT); if (m === 'wait') wT = setInterval(function () { if (D.visibilityState === 'visible') poll2(false); }, 20000);
  }
  function open_() { clearInterval(wT); if (gate) gate.hidden = true; opened(); flush(); }
  function grant(rec) {                           // accesso concesso su questo dispositivo
    var first = !LS.g('rm_inv') && !LS.g('rm_was');
    rec.t = Date.now(); rec.a = AVV; rec.ok = Date.now();
    LS.s('rm_inv', JSON.stringify(rec)); LS.s('rm_was', '1'); LS.d('rm_req');
    if (first) { bump('nuovi'); bump('mnew'); }
  }
  function ask() {
    var last = LS.j('rm_req');
    if (last && last.st === 'no' && Date.now() - (last.t || 0) < 10 * 6e4) { say('Puoi chiedere di nuovo tra qualche minuto.', 'bad'); return; }
    var b = D.getElementById('rmAsk'); b.disabled = true; b.setAttribute('aria-busy', 'true');
    var src = (D.querySelector('input[name=rmSrc]:checked') || {}).value || '', uso = (D.querySelector('input[name=rmUso]:checked') || {}).value || '';
    var id = rid(), auto = false, day = 'd-' + today();
    say('Invio la richiesta…');
    var p = fsGet('access/config').then(function (c) {
      c = c || {};
      if (c.open === false) throw { msg: 'In questo momento non si accettano nuove richieste: riprova più tardi.' };
      if (c.auto !== true) return false;
      var mx = +c.maxDay || 0; if (!mx) return true;
      return fsGet('access/' + day).then(function (d) { return ((d && d.n) || 0) < mx; });
    }).then(function (a) {
      auto = a;
      var f = { st: { stringValue: a ? 'ok' : 'attesa' } };
      if (src) f.src = { stringValue: src };
      if (uso) f.uso = { stringValue: uso };
      var w = [{ update: { name: ROOT + '/requests/' + id, fields: f }, updateTransforms: [{ fieldPath: 'at', setToServerValue: 'REQUEST_TIME' }], currentDocument: { exists: false } }];
      if (a) w.push({ update: { name: ROOT + '/access/' + day, fields: {} }, updateMask: { fieldPaths: [] }, updateTransforms: [{ fieldPath: 'n', increment: { integerValue: '1' } }] });
      return fsCommit(w);
    }).then(function () {
      var sf = { rq: 1 }; if (auto) sf.ra = 1; if (src) sf['k' + src] = 1; if (uso) sf['u' + uso] = 1;
      statNow(sf);
      if (auto) { grant({ r: id }); say('Accesso approvato. Buon lavoro!', 'ok'); setTimeout(open_, 900); }
      else { LS.s('rm_req', JSON.stringify({ r: id, t: Date.now(), st: 'attesa', a: AVV })); mode('wait'); }
    }).catch(function (e) { say(e && e.msg ? e.msg : netMsg(e), 'bad'); })
      .then(function () { b.removeAttribute('aria-busy'); upd(); });
    wait(p, 'Invio la richiesta…');
  }
  function poll2(manual) {                        // in attesa: la richiesta è stata approvata?
    var q = LS.j('rm_req'); if (!q || !q.r || !PID) return;
    if (manual) say('Controllo…');
    var p = fsGet('requests/' + q.r).then(function (r) {
      var L = D.getElementById('rmLast'); if (L) L.textContent = 'Ultimo controllo alle ' + new Date().toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' }) + '.';
      if (r && r.st === 'ok') { grant({ r: q.r }); say('Accesso approvato. Buon lavoro!', 'ok'); setTimeout(open_, 900); }
      else if (!r || r.st === 'no') { q.st = 'no'; q.t = Date.now(); LS.s('rm_req', JSON.stringify(q)); mode('no'); }
      else if (manual) say('Ancora in attesa di approvazione.');
    }).catch(function (e) { if (manual) say(netMsg(e), 'bad'); });
    if (manual) wait(p, 'Controllo…');
  }
  function activate(code) {
    var go = D.getElementById('rmGo'); go.disabled = true; go.setAttribute('aria-busy', 'true');
    say('Controllo il codice…');
    var p = fsGet('codes/' + code).then(function (c) {
      var w = why(c); if (w) throw { msg: w };
      return fsCommit([{ transform: { document: ROOT + '/codes/' + code, fieldTransforms: [{ fieldPath: 'used', increment: { integerValue: '1' } }] }, currentDocument: { exists: true } }])
        .catch(function (e) { if (e && e.status === 403) return fsGet('codes/' + code).then(function (c2) { throw { msg: why(c2) || 'Codice non accettato: riprova.' }; }); throw e; });
    }).then(function () {
      grant({ c: code }); say('Codice attivato. Buon lavoro!', 'ok'); setTimeout(open_, 900);
    }).catch(function (e) { say(e && e.msg ? e.msg : netMsg(e), 'bad'); })
      .then(function () { go.removeAttribute('aria-busy'); upd(); });
    wait(p, 'Controllo il codice…');
  }
  function recheck() {                           // con la rete: l'accesso è ancora attivo?
    var v = LS.j('rm_inv'); if (!PID || navigator.onLine === false) return;
    if (!v || !(v.c || v.r)) { var q = LS.j('rm_req'); if (q && q.st === 'attesa') poll2(false); return; }
    if (v.ok && Date.now() - v.ok < 6 * 36e5) return;
    var get = v.r ? fsGet('requests/' + v.r).then(function (r) { return !!(r && r.st === 'ok'); }) : fsGet('codes/' + v.c).then(function (c) { return !!(c && c.on === true); });
    get.then(function (ok) {
      if (!ok) { LS.d('rm_inv'); mode('off'); return; }
      v.ok = Date.now(); LS.s('rm_inv', JSON.stringify(v));
    }).catch(function () {});
  }

  /* ---------- 6 · «Ramometro ti è utile?» una volta, dopo 10 calcoli ---------- */
  function askUseful(n) {
    var a = LS.g('rm_ua');
    if (a === 'si' || a === 'no' || a === 'x2') return;
    if (!(a === 'x1' ? n >= 30 : n >= 10)) return;
    if (D.getElementById('rmUse') || D.querySelector('.ov:not([hidden])')) return;
    addCss();
    var c = el('<div id="rmUse" role="dialog" aria-label="Ramometro ti è utile?"><b>Ramometro ti è utile?</b><button type="button" class="rmB rmP" data-u="si">Sì</button><button type="button" class="rmB" data-u="no">No</button><button type="button" class="rmX" data-u="x" aria-label="Chiudi">×</button></div>');
    D.body.appendChild(c);
    c.addEventListener('click', function (e) {
      var b = e.target.closest('[data-u]'); if (!b) return;
      var u = b.dataset.u;
      if (u === 'x') LS.s('rm_ua', a === 'x1' ? 'x2' : 'x1');
      else { LS.s('rm_ua', u); bump(u === 'si' ? 'us' : 'un'); flush(); }
      if (u !== 'x') { c.innerHTML = '<b>Grazie!</b>'; setTimeout(function () { c.remove(); }, 1400); } else c.remove();
    });
  }

  /* ---------- 7 · Menu › Aiuto › Privacy e avvertenze ---------- */
  function legalBody() {
    var v = LS.j('rm_inv');
    return '<p>Ramometro <b>non raccoglie dati personali</b>: niente account, niente email, niente nome. Calcoli, storico, magazzino e impostazioni restano su questo dispositivo.</p>' +
      '<p>Ramometro <b>fa stime e calcoli, non dà consigli di acquisto</b>: ogni decisione e responsabilità resta tua.</p>' +
      '<div class="rmRow"><a class="rmB" href="privacy.html" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;text-decoration:none">Informativa privacy</a><a class="rmB" href="avvertenze.html" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;text-decoration:none">Avvertenze d’uso</a></div>' +
      '<p class="rmMut">' + (v && (v.c || v.r) ? 'Accesso attivo dal ' + fdate(v.t) + (v.r ? ' (richiesta ' + shown(v.r) + ').' : ' (codice d’invito).') : 'Accesso non ancora attivo.') + '</p>' +
      '<h3>Cosa fare</h3><ol><li>Leggi l’<b>Informativa privacy</b> per sapere cosa resta sul dispositivo e cosa no.</li><li>Leggi le <b>Avvertenze d’uso</b>: limiti delle stime, norme su rifiuti e provenienza del materiale, responsabilità.</li><li>Per non perdere i dati: Menu › I miei dati › <b>Esporta e recupera</b> › <b>Scarica un file</b>.</li></ol>' +
      '<h3>Poi</h3><ul><li>L’accesso si chiede dall’app ed è approvato dal gestore, che non sa chi sei: vede solo il codice casuale della richiesta e le risposte facoltative.</li><li>L’app conta solo numeri totali (aperture, calcoli, salvataggi), senza sapere chi sei.</li><li>Le funzioni AI qui non ci sono: sono solo nella versione su claude.ai.</li><li>Cancellare i dati del sito dal browser cancella tutto quello che l’app ha salvato qui.</li></ul>';
  }
  function openLegal() {
    addCss();
    var ov = D.getElementById('rmLegOv');
    if (!ov) {
      ov = el('<div class="rmOv" id="rmLegOv" role="dialog" aria-modal="true" aria-labelledby="rmLegT" hidden><div class="rmCard"><div style="display:flex;justify-content:space-between;align-items:center;gap:8px"><h2 id="rmLegT" style="margin:0">Privacy e avvertenze</h2><button type="button" class="rmB" data-x>Chiudi</button></div><div id="rmLegB"></div></div></div>');
      D.body.appendChild(ov);
      ov.addEventListener('click', function (e) { if (e.target === ov || e.target.closest('[data-x]')) ov.hidden = true; });
      D.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !ov.hidden) ov.hidden = true; });
    }
    D.getElementById('rmLegB').innerHTML = legalBody();
    ov.hidden = false;
  }
  W.__RMWEB = { openLegal: openLegal, flush: flush, bump: bump, gate: mode };
  function mount() {
    if (D.getElementById('rmLeg')) return true;
    if (D.querySelector('#pvMenu [data-go="leg"]')) { W.__LEGH = legalBody; return true; }
    var head = [].slice.call(D.querySelectorAll('.pms')).filter(function (x) { return /^\s*Aiuto\s*$/.test(x.textContent); })[0];
    var box = head && head.nextElementSibling; if (!box) return false;
    var b = el('<button type="button" class="pmi" id="rmLeg" aria-haspopup="dialog"><i><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3 5 6v5c0 4.5 3 8.3 7 10 4-1.7 7-5.5 7-10V6z"/><path d="m9 12 2 2 4-4"/></svg></i><span><b>Privacy e avvertenze</b><small>Nessun dato personale · ogni decisione è tua</small></span><svg class="pch" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg></button>');
    box.appendChild(b);
    b.addEventListener('click', function (e) { e.stopPropagation(); openLegal(); });
    return true;
  }
  function goKey() { try { if (W.__GO && W.__GO.keys) { if (!W.__GO.keys.legal) W.__GO.keys.legal = { fn: openLegal }; return true; } } catch (e) {} return false; }


  /* ---------- 9 · borsa e notizie aggiornate (data/market.json, scritto da un'automazione gratuita di GitHub) ---------- */
  var MKT = null, mktP = null;
  function market() {
    if (!mktP) mktP = fetch('data/market.json', { cache: 'no-cache' }).then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) { MKT = j && j.spot && j.asof ? j : null; return MKT; }).catch(function () { return null; });
    return mktP;
  }
  W.__WEBDB = { doc: function (p) { return {
    get: function () { if (p !== 'market/latest') return Promise.resolve({ exists: false, data: function () { return null; } });
      return market().then(function (j) { return { exists: !!j, data: function () { return j; } }; }); },
    set: function () { return Promise.resolve(); } }; } };

  /* ---------- 10 · avvisi sul rame all'apertura (soglie di Menu › Avvisi e soglie, salvate sul dispositivo) ---------- */
  function TT(s) { try { return W.__I18N ? W.__I18N.T(s) : s; } catch (e) { return s; } }
  function TF(s) { var a = [].slice.call(arguments, 1), t = TT(s); return t.replace(/\{(\d+)\}/g, function (m, i) { return a[+i] === undefined ? m : a[+i]; }); }
  function nfi(x, d) { return Number(x).toLocaleString('it-IT', { minimumFractionDigits: d, maximumFractionDigits: d }); }
  function alertsCheck() {
    market().then(function (j) {
      if (!j || !Array.isArray(j.hist) || j.hist.length < 2 || !(j.usdPerEur > 0)) return;
      var c = LS.j('cu_al') || {}, cu = c.cu || {}, src = c.src || {};
      if (c.on === false || src.qt === false) return;
      var DF = { d24: { on: true, v: 3 }, d7: { on: true, v: 5 }, r24: { on: true, v: 3 }, r7: { on: true, v: 5 }, lo: { on: false, v: null }, hi: { on: false, v: null } };
      var g = function (k) { var x = cu[k] || DF[k]; return x && x.on && x.v > 0 ? +x.v : null; };
      var h = j.hist, p0 = h[0][1], p1 = h[1][1], p5 = h[Math.min(5, h.length - 1)][1], c1 = (p0 / p1 - 1) * 100, c5 = (p0 / p5 - 1) * 100, eur = p0 / j.usdPerEur / 1000;
      var R = [
        ['d24', g('d24') !== null && c1 <= -g('d24'), TF('Rame in calo: {0} % in un giorno di borsa', '−' + nfi(-c1, 1))],
        ['d7', g('d7') !== null && c5 <= -g('d7'), TF('Rame in calo: {0} % in una settimana di borsa', '−' + nfi(-c5, 1))],
        ['lo', g('lo') !== null && eur <= g('lo'), TF('Rame sotto la tua soglia: {0} €/kg', nfi(eur, 2))],
        ['r24', g('r24') !== null && c1 >= g('r24'), TF('Rame in salita: {0} % in un giorno di borsa', '+' + nfi(c1, 1))],
        ['r7', g('r7') !== null && c5 >= g('r7'), TF('Rame in salita: {0} % in una settimana di borsa', '+' + nfi(c5, 1))],
        ['hi', g('hi') !== null && eur >= g('hi'), TF('Rame sopra la tua soglia: {0} €/kg', nfi(eur, 2))]];
      var f = LS.j('rm_alw') || {}, out = [];
      R.forEach(function (r) { if (r[1]) { if (!f[r[0]]) { out.push(r[2]); f[r[0]] = h[0][0]; } } else delete f[r[0]]; });
      LS.s('rm_alw', JSON.stringify(f));
      if (!out.length) return;
      addCss();
      var b = el('<div class="rmAlw" role="status"><b>' + TT('Avviso sul rame') + '</b><ul>' + out.map(function (x) { return '<li>' + x + '</li>'; }).join('') + '</ul>' +
        '<small>' + TF('Borsa LME del {0}: {1} $/t', h[0][0].split('-').reverse().join('/'), nfi(p0, 0)) + '</small>' +
        '<div class="rmRow"><button type="button" class="rmB" data-s>' + TT('Soglie') + '</button><button type="button" class="rmB rmP" data-x>' + TT('Chiudi') + '</button></div></div>');
      D.body.appendChild(b);
      b.addEventListener('click', function (e) {
        if (e.target.closest('[data-x]')) b.remove();
        else if (e.target.closest('[data-s]')) { b.remove(); try { W.__GO('cu'); } catch (x) {} }
      });
    });
  }

  /* ---------- 11 · funzioni che usano l'AI: etichetta «solo su claude.ai» ---------- */
  var AISEL = '#srBtn,#sqGo,#fsOpen,#vvKm,[data-dlkm],#imLnkGo,#imVoice,#imImgT,#rfGo';
  function aiMark() {
    var L = D.querySelectorAll(AISEL), t = TT('solo su claude.ai');
    for (var i = 0; i < L.length; i++) if (L[i].getAttribute('data-rmai') !== t) { L[i].setAttribute('data-rmai', t); L[i].classList.add('rmAiB'); }
  }
  var aiT = 0;
  function aiWatch() { aiMark(); try { new MutationObserver(function () { clearTimeout(aiT); aiT = setTimeout(aiMark, 120); }).observe(D.body, { childList: true, subtree: true }); } catch (e) {} }

  /* ---------- 8 · avvio ---------- */
  function start() {
    addCss();
    (function mm(n) { var a = mount(), g = goKey(); if (!(a && g) && n < 120) setTimeout(function () { mm(n + 1); }, 250); })(0);
    var v = LS.j('rm_inv'), q = LS.j('rm_req');
    market().then(function (j) { if (j) [1200, 3500].forEach(function (t) { setTimeout(function () { try { W.__X5 && W.__X5.mk(); } catch (e) {} }, t); }); }); aiWatch();
    if (v && (v.c || v.r)) { opened(); recheck(); setTimeout(alertsCheck, 2500); }
    else if (q && q.st === 'attesa') { mode('wait'); poll2(false); }
    else if (q && q.st === 'no') mode('no');
    else mode(LS.g('rm_was') ? 'off' : 'req');
  }
  if (D.readyState === 'loading') D.addEventListener('DOMContentLoaded', start); else start();
  W.addEventListener('online', recheck);
  D.addEventListener('visibilitychange', function () { if (D.visibilityState === 'visible') recheck(); });

  /* PWA */
  if ('serviceWorker' in navigator && location.protocol === 'https:') W.addEventListener('load', function () { navigator.serviceWorker.register('sw.js').catch(function () {}); });
})();
