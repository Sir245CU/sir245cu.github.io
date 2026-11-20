# Sorgenti della versione web di Ramometro

- `build.py`: dalla versione di produzione su claude.ai (`src/prod.html`, non incluso) al sito. Uso: `python3 build.py src/prod.html dist firebase-config.json`.
- `src/shim.js`: strato web (dati sul dispositivo, accesso su richiesta o codice, statistiche anonime, Privacy e avvertenze).
- `src/admin.js`, `src/admin.html`: area riservata (accesso, richieste, codici, statistiche).
- `src/pages.py`: testi di Informativa privacy e Avvertenze d'uso.
- `test/`: prove con Firestore finto (`t2.py` app, `t3.py` area riservata).
- Pacchetti npm: esbuild, firebase, @fontsource/ibm-plex-sans, @fontsource/ibm-plex-sans-condensed, @fontsource/archivo-black, pdfjs-dist@3.11.174, xlsx@0.18.5.
- `tools/mercato.py` e `tools/estrai_data.js`: dati di mercato. `build.py` scrive `data/base.json` (i dati incorporati nell'app); l'automazione `.github/workflows/mercato.yml` (giorni feriali, 7:41 e 17:41) legge borsa LME (Westmetall), cambio (BCE tramite Frankfurter) e titoli delle notizie (MINING.COM) e scrive `data/market.json`, che l'app legge all'apertura. Nessun dato personale, nessuna AI.
- `test/t4.py`: prove di borsa e notizie aggiornate, avvisi all'apertura, etichette «solo su claude.ai», pagina Avvisi della web.
- Le regole del database sono nella console Firebase (copia nel progetto Claude: `claude/ramometro-web-firestore.rules`). Non vanno messe qui: il repository è pubblico.
