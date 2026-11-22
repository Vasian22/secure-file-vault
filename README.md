# Secure File Vault

A small Python (FastAPI) API for storing and retrieving files in a private AWS S3 bucket. I built it to learn cloud security basics hands-on: least-privilege access, private storage, short-lived access links and audit logging.

## What it does

| Endpoint | Purpose |
|---|---|
| `POST /upload` | Saves a file into the caller's own folder in the bucket |
| `GET /files` | Lists only the caller's files |
| `GET /download?key=...` | Returns a presigned link that expires after 60 seconds |

Requests are authenticated with an `x-api-key` header. The key maps to a username, and that username becomes the user's folder prefix in S3 (for example `student1/report.pdf`).

## Architecture

```
Client (browser / curl)
        |
        v
FastAPI app (Python, boto3)
        |
        v
Private S3 bucket (ap-southeast-2)  ---- access logs ---->  Separate S3 log bucket
```

## Security design

- **Private by default:** Block Public Access is on, so no object is ever publicly readable.
- **Encryption:** server-side encryption at rest (SSE-S3), and a bucket policy that denies any request not made over HTTPS.
- **Least privilege:** the IAM user the app runs as can only put, get and list objects in this one bucket. It cannot delete objects or touch any other resource.
- **Short-lived access:** downloads use presigned URLs that expire after 60 seconds, so there are no permanent links.
- **Per-user isolation:** every user's files live under their own prefix. Requests for another user's key are rejected with `403`, and unknown API keys with `401`.
- **Safe filenames:** uploaded filenames are stripped of path components so a crafted name cannot write outside the user's folder.
- **Audit trail:** S3 server access logging writes to a separate bucket, so access can be reviewed later.
- **No secrets in code:** the bucket name comes from an environment variable and AWS credentials come from the AWS CLI configuration. Neither is committed to the repo.
- **Versioning** is enabled on the bucket, so overwritten or deleted objects can be recovered.

## Tech stack

Python 3.13, FastAPI, Uvicorn, boto3, pytest, moto, AWS S3 and IAM.

## Run it locally

Prerequisites: Python 3, an AWS account with an S3 bucket, and the AWS CLI configured (`aws configure`) with a user that can read, write and list that bucket.

```
git clone https://github.com/YOUR-USERNAME/secure-file-vault.git
cd secure-file-vault
python -m venv venv
venv\Scripts\activate          # on macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
set PRIMARY_BUCKET=your-bucket-name     # on macOS/Linux: export PRIMARY_BUCKET=your-bucket-name
uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000/docs`, choose an endpoint, click **Try it out**, and enter `dev-key` in the `x-api-key` field.

The default API key is `dev-key`. Set the `APP_API_KEY` environment variable to use a different one.

## Tests

```
python -m pytest -v
```

The tests use [moto](https://github.com/getmoto/moto) to mock S3, so they run without touching a real AWS account. They cover:

- rejecting an invalid API key (401)
- uploading a file and then seeing it in the listing
- getting a download link for your own file
- being blocked from downloading another user's file (403)

## Limitations

- This is a single-user prototype. Authentication is a simple API-key placeholder, and the app runs locally rather than being deployed.
- There are no file type or file size checks yet.
- There is no delete endpoint. The app's IAM user deliberately has no delete permission.

## Possible next steps

- Add file type and size validation.
- Add a delete endpoint with a matching, narrowly scoped IAM permission.
- Deploy the app (for example on AWS Lambda) and replace the API key with a proper identity service.
- Add a second bucket in another region with replication and failover.

## What I learned

This was my first hands-on AWS project. I learned how IAM users and policies work and why giving the app only the permissions it needs is safer than broad access. Locking the bucket down and then serving files through presigned links showed me how private storage can still be shared in a controlled, temporary way. Debugging the project taught me to read Python tracebacks from the bottom up, for example fixing a `KeyError` caused by a missing environment variable, and to understand HTTP status codes like 401, 403 and 422. I also learned to test AWS code without a real account by mocking S3 with moto.
