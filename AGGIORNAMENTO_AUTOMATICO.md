# Controllo giornaliero automatico — istruzioni per Claude

Queste istruzioni vengono seguite ogni giorno alle 18:25 (ora italiana) da un'attività pianificata di Claude.
Lo scopo è aggiornare `data/content.json` e `data/catalog.json` (MW4) solo quando le fonti mostrano novità verificate. Il cron Aruba
`CODMeta-sync-MW4` lo pubblica poi sul sito alle 19:00.

## Regole fisse

- Modifica **solo** `data/content.json` e `data/catalog.json`. Non toccare `.github/`, `scripts/` o altri file.
- Ogni file ha la sua `release`: aumenta solo quella del file che cambia.
- Non inventare mai dati. Ogni dato nuovo deve venire da una fonte letta in questa esecuzione.
- Classifiche e build WZStats sono **editoriali di terzi**: non presentarle come ufficiali Activision.
- Dati di meta e build vanno letti **due volte** e devono coincidere. Se non coincidono, non pubblicarli.
- Nel dubbio non pubblicare: meglio un giorno senza aggiornamento che un dato sbagliato online.
- Testi in italiano, nello stesso stile e formato dei campi già presenti (date come `28 OTT 2026`, nomi armi in MAIUSCOLO in `metaOrder` e `builds[].name`).
- Non cambiare le date di verifica se non è cambiato niente.
- `release` va aumentato di esattamente 1 rispetto alla versione su `main`.

## Passi

1. **Stato del sito.** Leggi `https://www.kandodj.com/codmeta/monitor/sync-mw4-status.json`
   (non aprire mai `sync-mw4.php`). Annota se `ok` e `content.ok` sono `true` e quali `release` (MW4) e `content.release` sono online.
   Se online c'è una release più bassa di quella su `main` da più di due ore, segnalalo nel resoconto.

2. **Meta Warzone (WZStats).** Con WebFetch leggi `https://wzstats.gg/it` e la data «Updated …» della classifica Battle Royale.
   - Se la data corrisponde a `warzone.currentBuildDate`, la classifica non è cambiata: passa al punto 3.
   - Se è più recente: rileggi la classifica, aggiorna `metaOrder` (prime 23 armi), `roleRanks` e i tier.
     Per ogni arma in `builds` apri la pagina build `https://wzstats.gg/it/best-loadouts/...` e confronta
     il codice build. Aggiorna accessori, livelli, `code`, `updated` solo per le build cambiate o nuove.
     Aggiorna `currentBuildDate`, `currentBuildLabel`, `checked`, `status`, l'intro se cita la data,
     e aggiungi una voce in testa a `ticker`.

3. **Patch ufficiali.** Controlla `https://www.callofduty.com/patchnotes` (Warzone, Black Ops 7, Modern Warfare 4).
   Per ogni nota più recente di quelle già presenti in `ticker` e `news`:
   aggiungi una voce in testa a `ticker` (tag `GG MMM · GIOCO`, testo breve, `url` ufficiale) e, se rilevante,
   un elemento in `news.items`. Se una patch modifica armi in classifica, aggiungi la nota in
   `warzone.weaponNotes.notes` e, se la valutazione non è più affidabile, il nome in `warzone.pendingReview`.
   Se la pagina ufficiale non si legge, puoi usare fonti terze solo per segnalare l'esistenza di una patch,
   indicandolo chiaramente, senza riportarne il contenuto come ufficiale.

4. **MW4 Multigiocatore (`data/catalog.json`).** Con WebFetch leggi `https://wzstats.gg/it/mw4/meta`
   e la data «Aggiornato».
   - Le build del sito sono le armi della prima sezione «Modern Warfare 4 Meta» (non A Tier, non DMZ, non Warzone).
   - `order` = quelle armi nell'ordine della pagina, nomi in MAIUSCOLO come in `catalog[].name` (es. `AXION`, `MOSIN-NAGANT`).
   - `builds` ha una voce per ogni arma di `order`, nello stesso ordine. `rank` = posizione dell'arma tra le armi
     della **stessa categoria** in `order` (es. primo fucile d'assalto = 1, primo mitragliatore = 1).
     `category` al plurale come nelle voci esistenti (`Fucili d’assalto`, `Mitragliette`, `Fucili tattici`…).
     `slug` = nome in minuscolo con trattini (`iso-nightshade`).
   - Per ogni arma apri `https://wzstats.gg/it/best-loadouts/<slug>-mw4` e prendi **solo la build Multiplayer
     «Versatile»** (non Apex, non DMZ). Servono esattamente 5 accessori con slot diversi: `[slot, NOME, livello]`,
     livello `null` se la fonte non lo indica. Slot in italiano come nelle voci esistenti
     (Ottica, Volata, Canna, Sottocanna, Calcio, Impugnatura posteriore, Laser, Caricatore, Munizioni).
     Nomi accessori in inglese MAIUSCOLO, nella forma già usata (es. `FSS TAC90 GRIP`, non `IMPUGNATURA FSS TAC90`).
   - Leggi due volte classifica e build cambiate: devono coincidere. Se una build non ha 5 accessori, o un'arma
     in classifica non è in `catalog`, non pubblicare il file MW4 e spiegalo nel resoconto.
   - Se classifica e build sono identiche a quelle presenti, non toccare il file (nemmeno le date).
   - Se cambia qualcosa: aggiorna `buildCheckedAt` (AAAA-MM-GG), aumenta `release` di 1 e valida con
     `git show HEAD:data/catalog.json > /tmp/rif_cat.json && python3 scripts/check_catalog.py data/catalog.json /tmp/rif_cat.json`.
   - Il catalogo delle armi (`catalog`, `catalogCheckedAt`) si cambia solo se compare un'arma nuova con livello di sblocco,
     livello massimo e Apex letti da una fonte; altrimenti segnalalo nel resoconto senza aggiungerla.
   - Se cambia la classifica MW4, aggiungi anche una voce in testa a `ticker` di `content.json`.

5. **Sfide settimanali.** Prova a trovare la settimana successiva a `weekly.week` da una fonte leggibile.
   Pubblica solo l'elenco completo per tutte e tre le modalità, con fonte e data. Altrimenti lascia tutto com'è.

6. **Limita le dimensioni.** Tieni al massimo 20 voci in `ticker` e 20 in `news.items`, togliendo le più vecchie.
   Testi lunghi fino a 2000 caratteri, brevi fino a 300.

7. **Se non è cambiato niente:** non fare commit. Fine.

8. **Se ci sono novità:**
   - aumenta `release` di 1 nei file cambiati;
   - per `catalog.json` usa il controllo del punto 4;
   - `git show HEAD:data/content.json > /tmp/riferimento.json`, poi
     `python3 scripts/check_content.py data/content.json /tmp/riferimento.json` deve stampare `VALIDO`;
   - commit su `main` con messaggio `Contenuti: aggiornamento automatico GG MMM AAAA` e un elenco breve delle modifiche;
   - `git fetch origin main` e, se serve, `git rebase origin/main` prima del push. Se `main` è cambiato nel frattempo,
     ricontrolla che `release` sia ancora quella giusta.
   - Se il controllo non è `VALIDO` o il push fallisce, non forzare: annulla e riportalo nel resoconto.

## Resoconto finale

In italiano, breve, leggibile da telefono:
- pubblicato sì/no e con quale `release`;
- cosa è cambiato (meta Warzone, meta MW4, build, patch, sfide);
- cosa non è stato possibile verificare e perché;
- stato del sito letto al punto 1.
