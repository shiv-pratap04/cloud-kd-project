"""Sharded teacher labelling worker.

Env: SHARD_INDEX (from 0), SHARD_COUNT, S3_ENDPOINT, AWS_* (Secret), OLLAMA_HOST.
Takes commands whose 0-based line number % SHARD_COUNT == SHARD_INDEX and writes
datasets/teacher/shard-<i>.jsonl. Checkpoints every CHECKPOINT records and resumes.
"""
import json
import os
import pathlib

from common import ask_teacher, build_prompt, s3_client

CHECKPOINT = 25


def shard_lines(lines, index, count):
    return [(n, l) for n, l in enumerate(lines) if n % count == index]


def main():
    index = int(os.environ["SHARD_INDEX"])
    count = int(os.environ["SHARD_COUNT"])
    host = os.environ.get("OLLAMA_HOST", "http://host.k3d.internal:11434")
    template = pathlib.Path(os.environ.get("PROMPT_FILE", "/app/teacher_prompt.txt")).read_text()
    s3 = s3_client()
    key = f"teacher/shard-{index}.jsonl"

    pool = s3.get_object(Bucket="datasets", Key="commands_pool.jsonl")["Body"].read().decode().splitlines()
    mine = shard_lines([l for l in pool if l.strip()], index, count)

    done = {}
    try:
        old = s3.get_object(Bucket="datasets", Key=key)["Body"].read().decode()
        for l in old.splitlines():
            r = json.loads(l)
            done[r["id"]] = r
        print(f"resuming with {len(done)} done", flush=True)
    except s3.exceptions.NoSuchKey:
        pass

    def flush():
        body = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in done.values())
        s3.put_object(Bucket="datasets", Key=key, Body=body.encode())

    for i, (_, line) in enumerate(mine, 1):
        rec = json.loads(line)
        if rec["id"] in done:
            continue
        raw = ask_teacher(build_prompt(template, rec["text"]), host)
        done[rec["id"]] = {"id": rec["id"], "text": rec["text"], "teacher_raw": raw}
        if len(done) % CHECKPOINT == 0:
            flush()
            print(f"shard {index}: {len(done)}/{len(mine)}", flush=True)
    flush()
    print(f"shard {index} complete: {len(done)} records", flush=True)


if __name__ == "__main__":
    main()
