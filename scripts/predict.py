"""Produce predictions.jsonl for score.py.
  python scripts/predict.py hf  PATH_OR_HF_NAME OUT.jsonl     (student / untrained Pythia)
  python scripts/predict.py teacher OLLAMA_URL OUT.jsonl      (phi3.5 with the Task 1 prompt)
"""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "worker"), str(ROOT / "service")]
from validation import extract_json_line

mode, src, out = sys.argv[1:4]
val = [json.loads(l) for l in open(ROOT / "data/validation.jsonl") if l.strip()]
preds = []
if mode == "teacher":
    from common import ask_teacher, build_prompt
    tpl = (ROOT / "prompts/teacher_prompt.txt").read_text()
    for r in val:
        preds.append({"id": r["id"], "prediction": ask_teacher(build_prompt(tpl, r["text"]), src)})
else:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.manual_seed(42)
    tok = AutoTokenizer.from_pretrained(src); model = AutoModelForCausalLM.from_pretrained(src).eval()
    for r in val:
        ids = tok(f"Command: {r['text']}\nJSON:", return_tensors="pt")
        with torch.no_grad():
            o = model.generate(**ids, max_new_tokens=80, do_sample=False, pad_token_id=tok.eos_token_id)
        preds.append({"id": r["id"], "prediction": extract_json_line(tok.decode(o[0][ids["input_ids"].shape[1]:], skip_special_tokens=True))})
with open(out, "w") as f:
    for p in preds:
        f.write(json.dumps(p) + "\n")
print("wrote", out, len(preds))
