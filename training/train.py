"""Sequence-level distillation: fine-tune Pythia-70M on 'Command: ...\nJSON: <teacher reply>'."""
import argparse
import csv
import json
import os
import pathlib
import random

import numpy as np
import torch
import yaml
from transformers import AutoModelForCausalLM, AutoTokenizer


def seed_everything(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def build_text(rec):
    return f"Command: {rec['text']}\nJSON:", " " + rec["teacher_raw"].strip()


def encode(tok, rec, max_len):
    prompt, target = build_text(rec)
    p = tok(prompt)["input_ids"]
    t = tok(target)["input_ids"] + [tok.eos_token_id]
    ids = (p + t)[:max_len]
    labels = ([-100] * len(p) + t)[:max_len]   # loss only on the teacher's reply
    return ids, labels


def collate(batch, pad_id):
    n = max(len(i) for i, _ in batch)
    ids = torch.full((len(batch), n), pad_id); lab = torch.full((len(batch), n), -100)
    att = torch.zeros((len(batch), n), dtype=torch.long)
    for k, (i, l) in enumerate(batch):
        ids[k, :len(i)] = torch.tensor(i); lab[k, :len(l)] = torch.tensor(l); att[k, :len(i)] = 1
    return ids, att, lab


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="training/config.yaml")
    ap.add_argument("--subset", type=int, default=0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--epochs", type=int, default=None)
    a = ap.parse_args()
    cfg = yaml.safe_load(open(a.config))
    seed = a.seed if a.seed is not None else cfg["seed"]
    epochs = a.epochs if a.epochs is not None else cfg["epochs"]
    seed_everything(seed)
    torch.set_num_threads(max(1, os.cpu_count() or 1))

    recs = [json.loads(l) for l in open(cfg["train_file"]) if l.strip()][: cfg["max_examples"]]
    if a.subset:
        recs = recs[: a.subset]
    print(f"training on {len(recs)} records, {epochs} epochs, seed {seed}")

    tok = AutoTokenizer.from_pretrained(cfg["base_model"])
    tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(cfg["base_model"])
    data = [encode(tok, r, cfg["max_seq_length"]) for r in recs]
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["learning_rate"])
    gen = torch.Generator().manual_seed(seed)

    rows = []
    model.train()
    for ep in range(1, epochs + 1):
        order = torch.randperm(len(data), generator=gen).tolist()
        total, steps = 0.0, 0
        for s in range(0, len(order), cfg["batch_size"]):
            ids, att, lab = collate([data[i] for i in order[s:s + cfg["batch_size"]]], tok.pad_token_id)
            loss = model(input_ids=ids, attention_mask=att, labels=lab).loss
            loss.backward(); opt.step(); opt.zero_grad()
            total += loss.item(); steps += 1
        rows.append((ep, total / steps))
        print(f"epoch {ep}: mean loss {total / steps:.4f}", flush=True)

    out = pathlib.Path(a.out or cfg["output_dir"]); out.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(out, safe_serialization=True); tok.save_pretrained(out)
    (out / "VERSION.json").write_text(json.dumps({"base_model": cfg["base_model"], "seed": seed,
        "epochs": epochs, "records": len(recs), "library_versions": cfg["library_versions"]}, indent=2))
    lossfile = pathlib.Path(cfg["loss_csv"] if not a.subset else cfg["loss_csv"].replace(".csv", "_subset.csv"))
    lossfile.parent.mkdir(parents=True, exist_ok=True)
    with open(lossfile, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["epoch", "train_loss"]); w.writerows(rows)
    print("saved", out)


if __name__ == "__main__":
    main()
