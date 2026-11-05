"""Local S3 helper (needs `kubectl port-forward -n data svc/seaweedfs 8333:8333`, creds from .env).
  s3tool.py mkbuckets | put BUCKET KEY FILE | putdir BUCKET PREFIX DIR | get BUCKET KEY FILE | getdir BUCKET PREFIX DIR"""
import os, pathlib, sys, boto3
env = dict(l.strip().split("=", 1) for l in open(".env") if "=" in l)
s3 = boto3.client("s3", endpoint_url=os.environ.get("S3_ENDPOINT", "http://localhost:8333"), region_name="us-east-1",
                  aws_access_key_id=env["S3_ACCESS_KEY"], aws_secret_access_key=env["S3_SECRET_KEY"])
c, *a = sys.argv[1:]
if c == "mkbuckets":
    for b in ("datasets", "models"):
        try: s3.create_bucket(Bucket=b)
        except Exception as e: print('bucket', b, '->', type(e).__name__)
elif c == "ls":
    for b in s3.list_buckets()["Buckets"]:
        print("bucket:", b["Name"])
        for o in s3.list_objects_v2(Bucket=b["Name"]).get("Contents", []): print("   ", o["Key"], o["Size"])
elif c == "put": s3.upload_file(a[2], a[0], a[1])
elif c == "get": s3.download_file(a[0], a[1], a[2])
elif c == "putdir":
    for p in sorted(pathlib.Path(a[2]).iterdir()):
        if p.is_file(): s3.upload_file(str(p), a[0], f"{a[1].rstrip('/')}/{p.name}")
elif c == "getdir":
    pathlib.Path(a[2]).mkdir(parents=True, exist_ok=True)
    for pg in s3.get_paginator("list_objects_v2").paginate(Bucket=a[0], Prefix=a[1]):
        for o in pg.get("Contents", []):
            s3.download_file(a[0], o["Key"], str(pathlib.Path(a[2]) / pathlib.Path(o["Key"]).name))
