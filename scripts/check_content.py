#!/usr/bin/env python3
"""Controllo prudente di data/content.json prima della pubblicazione.

Uso:
    python3 scripts/check_content.py NUOVO.json RIFERIMENTO.json

RIFERIMENTO è l'ultima versione pubblicata (per esempio quella in git HEAD).
Il controllo è volutamente più severo dello script PHP su Aruba: accetta solo
campi e tipi già presenti nel riferimento, così un file con struttura nuova
non arriva mai al sito. Se cambia lo schema, va aggiornato anche questo file.
"""
import json
import re
import sys

# Oggetti che sono mappe libere (chiave = nome arma), non strutture fisse.
FREE_MAPS = {"warzone.roleRanks", "warzone.weaponNotes.notes"}
MAX_TEXT = 2000
MAX_ATTACHMENTS = 12
DATE_RE = re.compile(r"^\d{1,2} (GEN|FEB|MAR|APR|MAG|GIU|LUG|AGO|SET|OTT|NOV|DIC) \d{4}$")

errors = []


def err(msg):
    errors.append(msg)


def norm(path):
    return re.sub(r"\[\d+\]", "[]", path)


def collect_shape(obj, path, shape):
    """Raccoglie, per ogni percorso normalizzato, tipi e chiavi ammesse."""
    p = norm(path)
    entry = shape.setdefault(p, {"types": set(), "keys": set()})
    entry["types"].add(type(obj).__name__)
    if isinstance(obj, dict):
        if p in FREE_MAPS:
            for v in obj.values():
                collect_shape(v, p + ".*", shape)
        else:
            for k, v in obj.items():
                entry["keys"].add(k)
                collect_shape(v, f"{path}.{k}" if path else k, shape)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            collect_shape(v, f"{path}[{i}]", shape)


def check_shape(obj, path, shape):
    p = norm(path)
    if p not in shape:
        err(f"campo non previsto: {path}")
        return
    t = type(obj).__name__
    if t not in shape[p]["types"]:
        err(f"tipo {t} non ammesso in {path} (atteso {sorted(shape[p]['types'])})")
        return
    if isinstance(obj, str):
        if len(obj) > MAX_TEXT:
            err(f"testo troppo lungo in {path} ({len(obj)} caratteri)")
        if path.endswith(("url", "Url")) and not obj.startswith("https://"):
            err(f"indirizzo non https in {path}: {obj}")
    if isinstance(obj, dict):
        if p in FREE_MAPS:
            for k, v in obj.items():
                check_shape(v, p + ".*", shape)
        else:
            for k, v in obj.items():
                if k not in shape[p]["keys"]:
                    err(f"campo non previsto: {path}.{k}")
                else:
                    check_shape(v, f"{path}.{k}" if path else k, shape)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            check_shape(v, f"{path}[{i}]", shape)


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    new = json.load(open(sys.argv[1], encoding="utf-8"))
    ref = json.load(open(sys.argv[2], encoding="utf-8"))

    shape = {}
    collect_shape(ref, "", shape)
    check_shape(new, "", shape)

    # Chiavi di primo livello: nessuna sezione deve sparire.
    for k in ref:
        if k not in new:
            err(f"sezione mancante: {k}")

    if new.get("schemaVersion") != ref.get("schemaVersion"):
        err("schemaVersion cambiato: serve un nuovo pacchetto del sito, non un aggiornamento dati")

    rel_new, rel_ref = new.get("release"), ref.get("release")
    if not isinstance(rel_new, int) or not isinstance(rel_ref, int) or rel_new != rel_ref + 1:
        err(f"release deve essere {rel_ref} + 1 (trovato {rel_new})")

    wz = new.get("warzone", {})
    builds = wz.get("builds", [])
    names = [b.get("name") for b in builds]
    if not builds:
        err("nessuna build Warzone")
    if len(set(names)) != len(names):
        err("nomi di build duplicati")
    for b in builds + wz.get("extraBuilds", []):
        att = b.get("attachments", [])
        if not att or len(att) > MAX_ATTACHMENTS:
            err(f"accessori non validi per {b.get('name')}: {len(att)}")
        if b.get("tier") not in ("S", "A", "B"):
            err(f"tier non valido per {b.get('name')}: {b.get('tier')}")
        if not DATE_RE.match(str(b.get("updated", ""))):
            err(f"data 'updated' non valida per {b.get('name')}: {b.get('updated')}")
    ranks = [b.get("rank") for b in builds]
    if len(set(ranks)) != len(ranks):
        err("rank duplicati nelle build")
    order = wz.get("metaOrder", [])
    if len(set(order)) != len(order):
        err("metaOrder contiene duplicati")
    if not DATE_RE.match(str(wz.get("currentBuildDate", ""))):
        err(f"currentBuildDate non valida: {wz.get('currentBuildDate')}")
    if not new.get("ticker"):
        err("ticker vuoto")

    if errors:
        print("NON VALIDO")
        for e in errors:
            print(" -", e)
        return 1
    print(f"VALIDO: release {rel_new}, {len(builds)} build Warzone, "
          f"{len(new.get('news', {}).get('items', []))} notizie, {len(new.get('ticker', []))} voci ticker")
    return 0


if __name__ == "__main__":
    sys.exit(main())
