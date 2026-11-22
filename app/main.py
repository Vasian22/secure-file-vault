import os
import boto3
from fastapi import FastAPI, UploadFile,Header, HTTPException
BUCKET = os.environ["PRIMARY_BUCKET"]
REGION = "ap-southeast-2"
API_KEYS = {os.environ.get("APP_API_KEY", "dev-key"): "student1"}

app = FastAPI()
s3 = boto3.client("s3", region_name=REGION)

def auth(key: str) -> str:
    user = API_KEYS.get(key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user

@app.post("/upload")
async def upload(file: UploadFile, x_api_key: str = Header(...)):
    user = auth(x_api_key)
    key = f"{user}/{os.path.basename(file.filename)}"
    s3.upload_fileobj(file.file, BUCKET, key)
    return {"key": key}

@app.get("/files")
def list_files(x_api_key: str = Header(...)):
    user = auth(x_api_key)
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=f"{user}/")
    return [o["Key"] for o in resp.get("Contents", [])]

@app.get("/download")
def download(key: str, x_api_key: str = Header(...)):
    user = auth(x_api_key)
    if not key.startswith(f"{user}/"):
        raise HTTPException(status_code=403, detail="Not your file")
    url = s3.generate_presigned_url(
        "get_object", Params={"Bucket": BUCKET, "Key": key}, ExpiresIn=60)
    return {"url": url}