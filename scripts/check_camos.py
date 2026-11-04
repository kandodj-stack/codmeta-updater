#!/usr/bin/env python3
"""Controllo di data/camos.json (tracker mimetiche) prima della pubblicazione.

Uso:
    python3 scripts/check_camos.py NUOVO.json [RIFERIMENTO.json]

Applica le stesse regole di validateCamos in sync-mw4.php e dello schema Zod del sito
(app/camo-data.tsx): un file che non passa qui verrebbe rifiutato anche su Aruba.
Controlla inoltre che ogni immagine elencata esista in data/camo-img/, pesi al massimo
400 KB e sia davvero un'immagine del tipo indicato dall'estensione.
Con RIFERIMENTO (l'ultima versione pubblicata, per esempio quella in git HEAD) verifica
anche che release aumenti di 1 se il contenuto cambia.
"""
import json
import os
import re
import sys

errors = []
MAX_IMAGE = 400_000
ID_RE = re.compile(r"^[a-z0-9-]{1,60}$")
CLASS_RE = re.compile(r"^[a-z]{1,6}$")
ITEM_RE = re.compile(r"^[a-z0-9-]{1,40}$")
IMG_RE = re.compile(r"^[a-z0-9-]{1,80}\.(webp|png|jpg)$")
WIMG_KEY = re.compile(r"^(m[1-8]|s[1-3])$")
SIMG_KEY = re.compile(r"^(gold|plat|hb|divergence|wp[1-8]|(mp|dmz|wz):[a-z0-9-]{1,40}|wz-[a-z0-9-]{1,40})$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def err(msg):
    errors.append(msg)


def txt(v, n=300):
    return isinstance(v, str) and 0 < len(v) <= n


def is_int(v, lo, hi):
    return isinstance(v, int) and not isinstance(v, bool) and lo <= v <= hi


def keys(obj, path, required, optional=()):
    if not isinstance(obj, dict):
        err(f"{path}: oggetto atteso")
        return False
    missing = [k for k in required if k not in obj]
    extra = [k for k in obj if k not in required and k not in optional]
    if missing:
        err(f"{path}: campi mancanti {missing}")
    if extra:
        err(f"{path}: campi non previsti {extra}")
    return not missing


def sources(v, path):
    if not isinstance(v, list) or not 1 <= len(v) <= 8 or not all(txt(s) for s in v):
        err(f"{path}: fonti non valide")


def mode_texts(t, path, required=()):
    if keys(t, path, list(required), [k for k in ("mp", "dmz", "wz") if k not in required]):
        for k in ("mp", "dmz", "wz"):
            if k in t and t[k] is not None and not txt(t[k]):
                err(f"{path}.{k}: testo non valido")


def no_empty_objects(x, path="camos"):
    # sync-mw4.php legge il JSON come array PHP: un oggetto vuoto {} diventa [] sul server e il sito lo rifiuta.
    if isinstance(x, dict):
        if not x:
            err(f"{path}: oggetto vuoto {{}} non ammesso (sul server diventerebbe []): togli il campo")
        for k, v in x.items():
            no_empty_objects(v, f"{path}.{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            no_empty_objects(v, f"{path}[{i}]")


def check(d, base_dir):
    no_empty_objects(d)
    if not keys(d, "camos", ["schemaVersion", "release", "checkedAt", "modes", "gold", "classes", "weapons", "others", "weaponPrestige", "account", "wzExtra", "images", "sources"]):
        return
    if d["schemaVersion"] != 1 or not is_int(d["release"], 1, 2147483647):
        err("schemaVersion o release non validi")
    if not isinstance(d["checkedAt"], str) or not DATE_RE.match(d["checkedAt"]):
        err("checkedAt non valida (AAAA-MM-GG)")
    if keys(d["modes"], "modes", ["mp", "dmz", "wz"]):
        for k, m in d["modes"].items():
            if keys(m, f"modes.{k}", ["label", "live"], ["from"]):
                if not txt(m["label"]) or not isinstance(m["live"], bool) or ("from" in m and not txt(m["from"])):
                    err(f"modes.{k} non valida")
    gold = dict(d["gold"]) if isinstance(d["gold"], dict) else {}
    sources(gold.pop("src", None), "gold.src")
    mode_texts(gold, "gold")
    classes = d["classes"] if isinstance(d["classes"], dict) else {}
    if not classes:
        err("classes vuoto o non valido")
    for k, c in classes.items():
        if not CLASS_RE.match(k):
            err(f"classe non valida: {k}")
        if keys(c, f"classes.{k}", ["label", "size", "platinum", "harmonic", "src"]):
            if not txt(c["label"]) or not is_int(c["size"], 1, 20):
                err(f"classes.{k}: etichetta o numero di armi non validi")
            mode_texts(c["platinum"], f"classes.{k}.platinum")
            mode_texts(c["harmonic"], f"classes.{k}.harmonic")
            sources(c["src"], f"classes.{k}.src")
    images = []
    weapons = d["weapons"] if isinstance(d["weapons"], list) else []
    if not 1 <= len(weapons) <= 60:
        err("weapons: da 1 a 60 armi")
    ids = []
    for i, w in enumerate(weapons):
        p = f"weapons[{i}]"
        if not keys(w, p, ["id", "name", "class", "unlock", "maxLevel", "military", "special"], ["images"]):
            continue
        p = f"weapons[{w.get('id')}]"
        if not isinstance(w["id"], str) or not ID_RE.match(w["id"]) or w["id"] == "acc" or not txt(w["name"]):
            err(f"{p}: id o nome non validi")
        if w["class"] not in classes:
            err(f"{p}: classe sconosciuta {w['class']}")
        if not is_int(w["unlock"], 1, 200) or not is_int(w["maxLevel"], 1, 300):
            err(f"{p}: livelli non validi")
        mil = w["military"]
        if keys(mil, f"{p}.military", ["levels", "src"]):
            if not isinstance(mil["levels"], list) or len(mil["levels"]) != 8 or not all(is_int(x, 1, 300) for x in mil["levels"]):
                err(f"{p}: servono 8 livelli militari")
            sources(mil["src"], f"{p}.military.src")
        sp = w["special"]
        if not isinstance(sp, list) or len(sp) != 3:
            err(f"{p}: servono 3 speciali")
            sp = []
        for j, s in enumerate(sp):
            q = f"{p}.special[{j}]"
            if not keys(s, q, ["name", "level", "mp", "wz", "src"], ["altNames", "levelSrc", "dmz"]):
                continue
            if not txt(s["name"]) or not (s["level"] is None or is_int(s["level"], 1, 200)):
                err(f"{q}: nome o livello non validi")
            if "levelSrc" in s and not is_int(s["levelSrc"], 1, 9):
                err(f"{q}: levelSrc non valido")
            if "altNames" in s and (not isinstance(s["altNames"], list) or len(s["altNames"]) > 4 or not all(txt(a) for a in s["altNames"])):
                err(f"{q}: altNames non validi")
            for k in ("mp", "wz", "dmz"):
                if k in s and s[k] is not None and not txt(s[k]):
                    err(f"{q}.{k}: testo non valido")
            sources(s["src"], f"{q}.src")
        for k, f in (w.get("images") or {}).items():
            if not WIMG_KEY.match(k) or not isinstance(f, str) or not IMG_RE.match(f):
                err(f"{p}.images.{k}: nome immagine non valido")
            else:
                images.append(f)
        ids.append(w["id"])
    if len(set(ids)) != len(ids):
        err("armi duplicate")
    others = d["others"] if isinstance(d["others"], list) else None
    if others is None or len(others) > 60 or not all(isinstance(o, list) and len(o) == 2 and txt(o[0]) and isinstance(o[1], str) and CLASS_RE.match(o[1]) for o in others):
        err("others non valido")
    wp = d["weaponPrestige"] if isinstance(d["weaponPrestige"], list) else None
    if wp is None or len(wp) > 8:
        err("weaponPrestige non valido")
    for i, x in enumerate(wp or []):
        if keys(x, f"weaponPrestige[{i}]", ["name", "req", "stage", "level"]):
            if not txt(x["name"]) or not txt(x["req"]) or x["stage"] not in ("p1", "master") or not (x["level"] is None or is_int(x["level"], 1, 999)):
                err(f"weaponPrestige[{i}] non valido")
    acc = d["account"]
    if keys(acc, "account", ["divergence", "mastery"]):
        if keys(acc["divergence"], "account.divergence", ["name", "req"]) and not (txt(acc["divergence"]["name"]) and txt(acc["divergence"]["req"])):
            err("account.divergence non valida")
        if keys(acc["mastery"], "account.mastery", ["mp", "dmz", "wz"]):
            for k, lst in acc["mastery"].items():
                if not isinstance(lst, list) or len(lst) > 6:
                    err(f"account.mastery.{k} non valido")
                    continue
                for m in lst:
                    if keys(m, f"account.mastery.{k}", ["id", "name", "req"]):
                        if not (isinstance(m["id"], str) and ITEM_RE.match(m["id"]) and txt(m["name"]) and (m["req"] is None or txt(m["req"]))):
                            err(f"account.mastery.{k}: voce non valida")
    wx = d["wzExtra"]
    if keys(wx, "wzExtra", ["status", "items"]):
        if wx["status"] not in ("pending", "live") or not isinstance(wx["items"], list) or len(wx["items"]) > 20:
            err("wzExtra non valido")
        for x in wx["items"] if isinstance(wx["items"], list) else []:
            if keys(x, "wzExtra.items", ["id", "name", "req", "scope"]):
                if not (isinstance(x["id"], str) and ITEM_RE.match(x["id"]) and txt(x["name"]) and (x["req"] is None or txt(x["req"])) and x["scope"] in ("weapon", "account")):
                    err("wzExtra: voce non valida")
    if not isinstance(d["images"], dict):
        err("images: oggetto atteso")
    else:
        for k, f in d["images"].items():
            if not SIMG_KEY.match(k) or not isinstance(f, str) or not IMG_RE.match(f):
                err(f"images.{k}: nome immagine non valido")
            else:
                images.append(f)
    if not isinstance(d["sources"], list) or len(d["sources"]) > 10:
        err("sources non valido")
    for s in d["sources"] if isinstance(d["sources"], list) else []:
        if keys(s, "sources", ["label", "url", "official"]):
            if not (txt(s["label"]) and isinstance(s["url"], str) and re.match(r"^https://[^\s\"<>]+$", s["url"]) and isinstance(s["official"], bool)):
                err("sources: voce non valida")

    magic = {"webp": lambda b: b[:4] == b"RIFF" and b[8:12] == b"WEBP", "png": lambda b: b[:8] == b"\x89PNG\r\n\x1a\n", "jpg": lambda b: b[:3] == b"\xff\xd8\xff"}
    for f in sorted(set(images)):
        path = os.path.join(base_dir, "camo-img", f)
        if not os.path.isfile(path):
            err(f"immagine mancante: data/camo-img/{f}")
            continue
        size = os.path.getsize(path)
        head = open(path, "rb").read(16)
        if size > MAX_IMAGE:
            err(f"immagine troppo pesante: {f} ({size} byte, massimo {MAX_IMAGE})")
        if not magic[f.rsplit(".", 1)[1]](head):
            err(f"il file {f} non è un'immagine del tipo indicato dall'estensione")
    return len(weapons), len(set(images))


def main():
    if len(sys.argv) not in (2, 3):
        print(__doc__)
        return 2
    new = json.load(open(sys.argv[1], encoding="utf-8"))
    counts = check(new, os.path.dirname(os.path.abspath(sys.argv[1]))) or (0, 0)
    if len(sys.argv) == 3:
        ref = json.load(open(sys.argv[2], encoding="utf-8"))
        rel_new, rel_ref = new.get("release"), ref.get("release")
        if new == ref:
            pass
        elif not isinstance(rel_new, int) or not isinstance(rel_ref, int) or rel_new != rel_ref + 1:
            err(f"il contenuto è cambiato: release deve essere {rel_ref} + 1 (trovato {rel_new})")
    if errors:
        print("NON VALIDO")
        for e in errors:
            print(" -", e)
        return 1
    print(f"VALIDO: release {new.get('release')}, {counts[0]} armi con dati, {counts[1]} immagini controllate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
