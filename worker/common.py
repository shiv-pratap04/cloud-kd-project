"""Shared helpers: S3 client from environment, teacher prompt, Ollama call."""
import json
import os
import urllib.request


def s3_client():
    import boto3
    return boto3.client(
        "s3",
        endpoint_url=os.environ["S3_ENDPOINT"],
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name="us-east-1",
    )


def build_prompt(template: str, command: str) -> str:
    # str.replace (not format) because the template contains JSON braces
    return template.replace("{COMMAND}", command)


def ask_teacher(prompt: str, host: str, model: str = "phi3.5") -> str:
    body = json.dumps({
        "model": model, "prompt": prompt, "stream": False,
        "options": {"temperature": 0, "seed": 42, "num_predict": 100},
    }).encode()
    req = urllib.request.Request(host.rstrip("/") + "/api/generate", body,
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())["response"]
