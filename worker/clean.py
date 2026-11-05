"""Clean the teacher shards -> datasets/v1/train.jsonl (+ train.sha256).

Usage: python clean.py            (reads/writes S3, env as in worker.py)
       python clean.py --local DIR_WITH_SHARDS OUT_DIR   (offline; used by tests)
Rejection order is a, b, c, d on every record; duplicates are counted only among
records that passed a-d, so input = a+b+c+d+duplicates+kept.
"""
import argparse
import hashlib
import json
import pathlib
import sys

KEYS = {"intent", "date", "time", "place"}
INTENTS = {"alarm_set", "alarm_query", "calendar_set", "calendar_query",
           "calendar_remove", "weather_query", "datetime_query", "recommendation_events"}


def classify(rec):
    """Return None if the record is good, else 'a'|'b'|'c'|'d'."""
    try:
        obj = json.loads(rec["teacher_raw"])
    except (ValueError, TypeError):
        return "a"
    if not isinstance(obj, dict):
        return "a"
    if set(obj.keys()) != KEYS:
        return "b"
    if obj["intent"] not in INTENTS:
        return "c"
    cmd = rec["text"].lower()
    for k in ("date", "time", "place"):
        v = obj[k]
        if v is None:
            continue
        if not isinstance(v, str) or v.lower() not in cmd:
            return "d"
    return None


def clean(records):
    counts = {"input": len(records), "a": 0, "b": 0, "c": 0, "d": 0, "duplicates": 0, "kept": 0}
    good = []
    for r in sorted(records, key=lambda r: r["id"]):
        bad = classify(r)
        if bad:
            counts[bad] += 1
        else:
            good.append(r)
    seen, kept = set(), []
    for r in good:  # id order, so the smallest id of a duplicate survives
        if r["text"] in seen:
            counts["duplicates"] += 1
            continue
        seen.add(r["text"])
        kept.append(r)
    counts["kept"] = len(kept)
    assert counts["input"] == sum(counts[k] for k in ("a", "b", "c", "d", "duplicates", "kept"))
    return kept, counts


def serialise(kept):
    return "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in kept).encode()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", nargs=2, metavar=("SHARD_DIR", "OUT_DIR"))
    a = ap.parse_args()
    records = []
    if a.local:
        for p in sorted(pathlib.Path(a.local[0]).glob("shard-*.jsonl")):
            records += [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    else:
        from common import s3_client
        s3 = s3_client()
        pages = s3.get_paginator("list_objects_v2").paginate(Bucket="datasets", Prefix="teacher/")
        for pg in pages:
            for o in pg.get("Contents", []):
                body = s3.get_object(Bucket="datasets", Key=o["Key"])["Body"].read().decode()
                records += [json.loads(l) for l in body.splitlines() if l.strip()]
    kept, counts = clean(records)
    data = serialise(kept)
    digest = hashlib.sha256(data).hexdigest()
    if a.local:
        out = pathlib.Path(a.local[1]); out.mkdir(parents=True, exist_ok=True)
        (out / "train.jsonl").write_bytes(data)
        (out / "train.sha256").write_text(f"{digest}  train.jsonl\n")
    else:
        s3.put_object(Bucket="datasets", Key="v1/train.jsonl", Body=data)
        s3.put_object(Bucket="datasets", Key="v1/train.sha256", Body=f"{digest}  train.jsonl\n".encode())
    print(json.dumps(counts, indent=2))
    print("sha256", digest)


if __name__ == "__main__":
    sys.exit(main())
