import os

# Fake settings so the tests never use your real AWS account
os.environ["PRIMARY_BUCKET"] = "test-bucket"
os.environ["APP_API_KEY"] = "dev-key"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "ap-southeast-2"

import boto3
from moto import mock_aws
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
HEADERS = {"x-api-key": "dev-key"}


def make_bucket():
    boto3.client("s3", region_name="ap-southeast-2").create_bucket(
        Bucket="test-bucket",
        CreateBucketConfiguration={"LocationConstraint": "ap-southeast-2"},
    )


def test_rejects_bad_key():
    r = client.get("/files", headers={"x-api-key": "wrong"})
    assert r.status_code == 401


@mock_aws
def test_upload_then_list():
    make_bucket()
    r = client.post("/upload", files={"file": ("a.txt", b"hello")}, headers=HEADERS)
    assert r.status_code == 200
    listing = client.get("/files", headers=HEADERS).json()
    assert "student1/a.txt" in listing


@mock_aws
def test_download_returns_link_for_own_file():
    make_bucket()
    client.post("/upload", files={"file": ("a.txt", b"hello")}, headers=HEADERS)
    r = client.get("/download", params={"key": "student1/a.txt"}, headers=HEADERS)
    assert r.status_code == 200
    assert "url" in r.json()


def test_cannot_download_other_users_file():
    r = client.get("/download", params={"key": "other/a.txt"}, headers=HEADERS)
    assert r.status_code == 403