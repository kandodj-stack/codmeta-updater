#!/usr/bin/env python3
"""Controllo di data/catalog.json (MW4) prima della pubblicazione.

Uso:
    python3 scripts/check_catalog.py NUOVO.json RIFERIMENTO.json

Replica le regole di app/catalog-sync.tsx (Zod) e di validateCatalog in
public/monitor/sync-mw4.php (v39). Se cambiano lì, va aggiornato anche questo file.
In più richiede che release sia esattamente quella del riferimento + 1.
"""
import datetime
import json
import re
import sys

errors = []


def err(msg):
    errors.append(msg)


def txt(v, mx=500):
    return isinstance(v, str) and v != "" and len(v) <= mx


def level(v):
    return isinstance(v, int) and not isinstance(v, bool) and 1 <= v <= 1000


def valid_date(v):
    if not isinstance(v, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return False
    try:
        datetime.date.fromisoformat(v)
        return True
    except ValueError:
        return False


def fields(obj, required, optional=(), where=""):
    if not isinstance(obj, dict):
        err(f"{where}: oggetto atteso")
        return False
    missing = set(required) - set(obj)
    extra = set(obj) - set(required) - set(optional)
    if missing:
        err(f"{where}: campi mancanti {sorted(missing)}")
    if extra:
        err(f"{where}: campi non previsti {sorted(extra)}")
    return not missing and not extra


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    ref = json.load(open(sys.argv[2], encoding="utf-8"))

    if not fields(d, ["schemaVersion", "release", "mw4"], where="radice"):
        return report()
    if d["schemaVersion"] != 1:
        err("schemaVersion deve essere 1")
    if not isinstance(d["release"], int) or d["release"] != ref.get("release", 0) + 1:
        err(f"release deve essere {ref.get('release')} + 1 (trovato {d['release']})")

    m = d["mw4"]
    if not fields(m, ["buildCheckedAt", "catalogCheckedAt", "catalog", "builds", "order"], where="mw4"):
        return report()
    for k in ("buildCheckedAt", "catalogCheckedAt"):
        if not valid_date(m[k]):
            err(f"{k} non è una data valida AAAA-MM-GG")

    cat = m["catalog"]
    names = []
    if not isinstance(cat, list) or not 1 <= len(cat) <= 200:
        err("catalogo vuoto o troppo lungo")
        cat = []
    for i, w in enumerate(cat):
        if fields(w, ["name", "category", "unlock", "maxLevel", "apex"], ["unlockSummary"], f"catalogo[{i}]"):
            if not (txt(w["name"]) and txt(w["category"]) and txt(w["apex"]) and level(w["unlock"]) and level(w["maxLevel"])):
                err(f"dati arma non validi: {w.get('name')}")
            if "unlockSummary" in w and not level(w["unlockSummary"]):
                err(f"unlockSummary non valido: {w.get('name')}")
            names.append(str(w["name"]).upper())
    if len(set(names)) != len(names):
        err("armi duplicate nel catalogo")

    order = m["order"]
    if not isinstance(order, list) or not 1 <= len(order) <= 200:
        err("ordine vuoto o non valido")
        order = []
    for n in order:
        if not txt(n) or n not in names:
            err(f"arma in ordine non presente nel catalogo: {n}")
    if len(set(order)) != len(order):
        err("ordine con duplicati")

    builds = m["builds"]
    if not isinstance(builds, dict) or len(builds) != len(order):
        err("le build devono essere tante quante le armi in ordine")
        builds = builds if isinstance(builds, dict) else {}
    ranks = []
    for name, b in builds.items():
        if name not in order or name not in names:
            err(f"build senza corrispondenza in ordine/catalogo: {name}")
        if not fields(b, ["rank", "category", "slug", "attachments"], where=f"build {name}"):
            continue
        if not (level(b["rank"]) and txt(b["category"]) and isinstance(b["slug"], str)
                and re.fullmatch(r"[a-z0-9-]{1,80}", b["slug"])):
            err(f"metadati non validi nella build {name}")
        ranks.append(b["rank"])
        att = b["attachments"]
        if not isinstance(att, list) or len(att) != 5:
            err(f"{name}: servono esattamente cinque accessori")
            continue
        slots = []
        for a in att:
            if not (isinstance(a, list) and len(a) == 3 and txt(a[0]) and txt(a[1]) and (a[2] is None or level(a[2]))):
                err(f"{name}: accessorio non valido {a}")
            else:
                slots.append(a[0])
        if len(set(slots)) != 5:
            err(f"{name}: slot accessori duplicati")
    # rank è la posizione dentro la categoria (es. #1 fucili d'assalto e #1 mitragliette):
    # i duplicati tra categorie diverse sono normali.
    return report(d)


def report(d=None):
    if errors:
        print("NON VALIDO")
        for e in errors:
            print(" -", e)
        return 1
    m = d["mw4"]
    print(f"VALIDO: release {d['release']}, {len(m['catalog'])} armi, {len(m['builds'])} build, ordine: {', '.join(m['order'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
