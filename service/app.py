"""Command-parser inference service. Config only via env vars:
MODEL_URI (s3://bucket/prefix/), MODEL_VERSION, S3_ENDPOINT, MAX_NEW_TOKENS, FAULT_INJECT.
S3 credentials: AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY, injected from a Kubernetes Secret."""
import os
import tempfile
import threading
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from validation import extract_json_line, validate

app = FastAPI()
STATE = {"model": None, "tok": None}
LOCK = threading.Lock()
POD = os.environ.get("HOSTNAME", "unknown")   # Pod name inside Kubernetes


class Req(BaseModel):
    text: str


def load_model():
    import boto3
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.set_num_threads(int(os.environ.get("TORCH_THREADS", "1")))
    u = urlparse(os.environ["MODEL_URI"])
    bucket, prefix = u.netloc, u.path.lstrip("/").rstrip("/") + "/"
    s3 = boto3.client("s3", endpoint_url=os.environ["S3_ENDPOINT"], region_name="us-east-1",
                      aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
                      aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"])
    d = tempfile.mkdtemp()
    for pg in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix):
        for o in pg.get("Contents", []):
            name = o["Key"][len(prefix):]
            if name and "/" not in name and name != "model.sha256":
                s3.download_file(bucket, o["Key"], os.path.join(d, name))
                print("downloaded", o["Key"], flush=True)
    STATE["tok"] = AutoTokenizer.from_pretrained(d)
    STATE["model"] = AutoModelForCausalLM.from_pretrained(d).eval()
    print("model ready", flush=True)


@app.on_event("startup")
def startup():
    threading.Thread(target=load_model, daemon=True).start()


@app.get("/healthz")
def healthz():
    return {"status": "alive"}


@app.get("/readyz")
def readyz():
    ok = STATE["model"] is not None
    return JSONResponse({"ready": ok}, status_code=200 if ok else 503)


def generate(text):
    import torch
    tok, model = STATE["tok"], STATE["model"]
    ids = tok(f"Command: {text}\nJSON:", return_tensors="pt")
    with LOCK, torch.no_grad():
        out = model.generate(**ids, max_new_tokens=int(os.environ.get("MAX_NEW_TOKENS", "80")),
                             do_sample=False, pad_token_id=tok.eos_token_id)
    return extract_json_line(tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True))


@app.post("/parse")
def parse(req: Req):
    if STATE["model"] is None:
        return JSONResponse({"error": "model_not_ready"}, status_code=503)
    raw = generate(req.text)
    if os.environ.get("FAULT_INJECT") == "1":
        raw = "not json"
    obj = validate(raw)
    headers = {"X-Model-Version": os.environ.get("MODEL_VERSION", "unknown"), "X-Served-By": POD}
    if obj is None:
        return JSONResponse({"error": "invalid_model_output"}, status_code=500, headers=headers)
    return JSONResponse(obj, headers=headers)
