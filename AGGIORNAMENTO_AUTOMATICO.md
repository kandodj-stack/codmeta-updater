# Controllo giornaliero automatico — istruzioni per Claude

Queste istruzioni vengono seguite ogni giorno alle 18:25 (ora italiana) da un'attività pianificata di Claude.
Lo scopo è aggiornare `data/content.json` e `data/catalog.json` (MW4) solo quando le fonti mostrano novità verificate. Il cron Aruba
`CODMeta-sync-MW4` lo pubblica poi sul sito alle 19:00.

## Regole fisse

- Modifica **solo** `data/content.json` e `data/catalog.json`. Non toccare `.github/`, `scripts/` o altri file.
- `data/camos.json` (tracker mimetiche) e `data/camo-img/` non fanno parte di questo controllo: li aggiorna Claude solo su richiesta di Kando, validando con `python3 scripts/check_camos.py data/camos.json RIFERIMENTO.json`.
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
   - Se la data corrisponde a `warzone.currentBuildDate`, la classifica non è cambiata, ma **controlla comunque le build mancanti**
     (richiesta di Kando, 7 nov 2026: WZStats pubblica le build Warzone un po' alla volta, anche senza cambiare la data):
     per ogni arma di `metaOrder` che non ha una voce in `builds`, apri la sua pagina build e cerca la sezione
     «Migliore classe per … per Warzone Battle Royale» (non Resurgence, Multigiocatore o DMZ). Aggiungi la build solo se due letture
     coincidono, ha 5 accessori tutti con nome, e non è una build Apex (se c'è anche una build non Apex, usa quella).
     `rank` = posizione in `metaOrder`, `tier` `S` per le armi del tier Meta e `A` per le altre, `updated` = data «Creato il»
     della build, nomi degli accessori come scritti sulla pagina italiana. Aggiorna la frase dell'intro sulle build mancanti
     e aggiungi una voce in testa a `ticker`. Poi passa al punto 3.
   - **Tutte le build Battle Royale di ogni arma** (richiesta di Kando, 11 nov 2026; sito v51 e sync-mw4.php v51).
     La sezione Battle Royale di una pagina può avere più build (es. Cronen Osprey: «Lunga distanza» e «Supporto cecchino»).
     Leggi tutte quelle **non Apex**: la prima della pagina resta la build principale (i campi di sempre), le altre vanno
     in `alternatives` (al massimo 3, nell'ordine della pagina). Ogni variante: `buildType`, `role`, `updated`
     (data «Creato il»), `note`, `attachments` (stesso formato delle build: `slot`, `name`, `unlock`), `code` solo se
     la pagina lo mostra. Stesse regole della build principale: 5 accessori tutti con nome, due letture coincidenti
     (italiano e inglese), altrimenti la variante resta fuori senza bloccare il resto.
     `buildType` = etichetta della build, uniformata così (WZStats traduce a volte «Close Range» con «Corto raggio»):
     Long Range → `Lunga distanza`, Close Range / Short Range → `Corta distanza`, Sniper Support → `Supporto cecchino`;
     altre etichette tradotte in italiano con la prima lettera maiuscola. `role` = `buildType` in MAIUSCOLO
     (`LUNGA DISTANZA`, `CORTA DISTANZA`, `SUPPORTO CECCHINO`): il sito crea i filtri per ruolo da questo campo.
     Ogni build principale ha il suo `buildType`. Se una variante sparisce dalla pagina, toglila; se `alternatives`
     resta vuoto, togli il campo. Nel ticker cita le varianti nuove o cambiate.
   - Le build già pubblicate possono cambiare anche se la classifica non cambia (es. Han 86 e VEL 46 ricreate il
     10 nov): a ogni controllo confronta la data «Creato il» di ogni build e variante con `updated`; se è diversa,
     rileggi la build due volte e aggiornala.
   - Dalla Stagione 1 Warzone usa le armi di Modern Warfare 4; quelle dei giochi precedenti sono «Legacy».
     In ogni build `origin` = gioco dell'arma: `MW4` per Modern Warfare 4 (nomi in MAIUSCOLO come in `catalog.json`,
     es. `AXION`, `M4`), `BO7`, `BO6`, `MW3`, `MWII` per le Legacy. Il sito mette una build `MW4` solo sulla scheda MW4.
     Quando WZStats pubblica il primo meta della Stagione 1, sostituisci classifica e build per intero e riscrivi `status`
     e `intro` togliendo il riferimento all'archivio della Stagione 06.
   - Se è più recente: rileggi la classifica, aggiorna `metaOrder` (prime 23 armi), `roleRanks` e i tier.
     Per ogni arma in `builds` apri la pagina build `https://wzstats.gg/it/best-loadouts/...` e confronta
     il codice build (o, se non c'è, data «Creato il» e accessori), varianti comprese.
     Aggiorna accessori, livelli, `code`, `updated` solo per le build cambiate o nuove.
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
   - Servono **sempre tutte le build disponibili** (richiesta di Kando, 2 nov 2026): tutte le armi della classifica
     Multiplayer nell'ordine della pagina, sezione «Modern Warfare 4 Meta» e poi A, B, C, D Tier (non DMZ, non Warzone),
     purché abbiano una build valida secondo le regole qui sotto. Le armi senza build valida si saltano e si elencano nel resoconto.
   - `order` = quelle armi nell'ordine della pagina, nomi in MAIUSCOLO come in `catalog[].name` (es. `AXION`, `MOSIN-NAGANT`,
     `PATRIOT XMR`; attenzione: WZStats scrive «PARTRIOT XMR»).
   - `builds` ha una voce per ogni arma di `order`, nello stesso ordine. `rank` = posizione dell'arma tra le armi
     della **stessa categoria** in `order` (es. primo fucile d'assalto = 1, primo mitragliatore = 1).
     `category` al plurale come nelle voci esistenti (`Fucili d’assalto`, `Mitragliette`, `Fucili tattici`, `Pistole`…).
     `tier` = sezione della pagina in cui si trova l'arma: `META` (prima sezione «Modern Warfare 4 Meta»), `A`, `B`, `C`, `D`.
     `buildType` = nome della build scelta come scritto su WZStats (`Versatile`, `Long Range`, `ADS Speed`, `Low Level`…).
     Ordine dei campi in ogni build: `rank`, `category`, `slug`, `tier`, `buildType`, `attachments`.
     `slug` = la parte dell'indirizzo WZStats prima di `-mw4` (`iso-nightshade`, `wz55-striga`, `partriot-xmr`, `astaroth-57`).
   - Per ogni arma apri `https://wzstats.gg/it/best-loadouts/<slug>-mw4` (se non leggibile, la versione inglese
     `https://wzstats.gg/best-loadouts/<slug>-mw4`: i nomi degli accessori sono in inglese; non usare la versione tedesca)
     e scegli la build Multiplayer così (mai DMZ o Warzone):
     1. la build «Versatile», se c'è;
     2. altrimenti la prima build Multiplayer **non Apex** della pagina (es. «Long Range», «ADS Speed», «Low Level», «Short Range»);
     3. se ci sono solo build Apex (o la build contiene l'arma Apex), l'arma resta fuori.
     Servono esattamente 5 accessori con slot diversi: `[slot, NOME, livello]`,
     livello `null` se la fonte non lo indica. Se un nome di accessorio manca o i due controlli non coincidono, l'arma resta fuori.
     Slot in italiano come nelle voci esistenti
     (Ottica, Volata, Canna, Sottocanna, Calcio, Impugnatura posteriore, Laser, Caricatore, Munizioni, Poggiaguancia,
     Grilletto per «Trigger Action» delle pistole, Otturatore per «Bolt» dei fucili, approvato da Kando il 5 nov 2026).
     Nomi accessori in inglese MAIUSCOLO, nella forma già usata (es. `FSS TAC90 GRIP`, non `IMPUGNATURA FSS TAC90`).
   - Leggi due volte classifica e build cambiate: devono coincidere. Se un'arma in classifica non è in `catalog`,
     non pubblicare il file MW4 e spiegalo nel resoconto. Le armi senza build valida (solo Apex, meno di 5 accessori,
     nomi mancanti, letture diverse) si saltano senza bloccare le altre.
   - Se classifica, tier e build sono identiche a quelle presenti, non toccare il file (nemmeno le date).
   - Se un'arma cambia tier (es. da A a META) la classifica è cambiata: aggiorna `tier`, `order` e `rank`.
   - Se cambia qualcosa: aggiorna `buildCheckedAt` (AAAA-MM-GG), aumenta `release` di 1 e valida con
     `git show HEAD:data/catalog.json > /tmp/rif_cat.json && python3 scripts/check_catalog.py data/catalog.json /tmp/rif_cat.json`.
   - Il catalogo delle armi (`catalog`, `catalogCheckedAt`) si cambia solo se compare un'arma nuova con livello di sblocco,
     livello massimo e Apex letti da una fonte; altrimenti segnalalo nel resoconto senza aggiungerla.
     Le armi del Battle Pass o degli eventi non hanno un livello giocatore: `unlock: null`, `unlockLabel` con il testo
     (es. «Battle Pass Stagione 1, livello 16 (gratis)», «Ricompensa dell'evento …») e `note` con fonti e data,
     come Cronen Osprey e CSG-35 (sito v48 e sync-mw4.php v48 li accettano). `category` al singolare come nelle altre voci.
   - Se cambia la classifica MW4, aggiungi anche una voce in testa a `ticker` di `content.json`.

4b. **Armi nuove → promemoria screenshot per Kando** (richiesta di Kando, 4 nov 2026). Non modificare `data/camos.json`.
   Confronta le armi MW4 note in questa esecuzione (`catalog[].name` di `data/catalog.json`, classifica WZStats MW4,
   note di patch o di stagione ufficiali che annunciano armi nuove) con le armi di `data/camos.json`
   (`weapons[].name` e `others[][0]`; confronta senza maiuscole, spazi e punteggiatura: «SANG 9mm» = «sang9mm»).
   Per ogni arma che manca in `camos.json`, metti **all'inizio del resoconto** questo promemoria, con il nome dell'arma
   e la classe se la conosci (testo da copiare così, cambiando solo le parti tra < >):

   > Arma nuova da aggiungere al tracker mimetiche: <NOME ARMA> (<classe>). Quando l'hai sbloccata, fai questi screenshot con OBS (PS5 → Elgato, immagine intera 1920×1080):
   > 1. Crea una classe → arma <NOME ARMA> → schermata «Selezione mimetica», scheda «Progressione <NOME ARMA>»: uno screenshot così com'è, con il cursore su Militare 1.
   > 2. Cursore sulla 1ª Speciale → screenshot; poi sulla 2ª e sulla 3ª (3 screenshot in tutto).
   > 3. Solo se l'arma è di una classe nuova: cursore su Platino → screenshot, poi su Rottura armonica → screenshot.
   > Metti gli screenshot in una cartella con il nome dell'arma, comprimila (7z o zip) e mandala a Claude nel progetto Codmeta. Finché l'arma è bloccata non serve niente: Claude usa le guide.

   Ripeti il promemoria ogni giorno finché l'arma non compare in `camos.json`. Le armi già presenti in `weapons[]` o in
   `others` non danno promemoria (es. .50 GS, che resta in `others` solo finché non è online la v45).

5. **Sfide settimanali.** Nella Stagione 1 di MW4 + Warzone le sfide settimanali non esistono (note ufficiali di lancio MW4:
   «Weekly Challenges will not be available in Season 1»): la sezione `weekly` lo dice e tiene come archivio la Stagione 06,
   settimana 4. Non cercare altre settimane della Stagione 06 e non cambiare `weekly`. Se una fonte ufficiale annuncia
   che le sfide settimanali tornano (per esempio dalla Stagione 2), non pubblicare niente: segnalalo nel resoconto.

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
- per prima cosa l'eventuale promemoria screenshot del punto 4b (armi nuove da aggiungere al tracker mimetiche);
- pubblicato sì/no e con quale `release`;
- cosa è cambiato (meta Warzone, meta MW4, build, patch, sfide);
- cosa non è stato possibile verificare e perché;
- stato del sito letto al punto 1.
