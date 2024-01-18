import os
import shutil
import logging
import boto3
import botocore

from botocore.client import Config
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.logger import LogHandler


logger = logging.getLogger(__file__)
logger.setLevel("DEBUG")
logger.addHandler(LogHandler())

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

session = boto3.session.Session()

s3_client = session.client(
    service_name='s3',
    aws_access_key_id='minio',
    aws_secret_access_key='minio123',
    endpoint_url='http://minio:9000',
    config=Config(signature_version='s3v4'),
)

BUCKET_NAME = "images"

try:
    s3_client.head_bucket(Bucket=BUCKET_NAME)
except botocore.exceptions.ClientError as e:
    logger.info(f"Creating bucket: {BUCKET_NAME}")
    s3_client.create_bucket(Bucket=BUCKET_NAME)


logger.info(f"Connected to bucket {BUCKET_NAME}")


@app.post("/upload-file")
def upload_file(file: UploadFile = File(...)):
    try:
        logger.info(f"Received file {file.filename} at /upload-file")
        s3_client.upload_fileobj(file.file, BUCKET_NAME, file.filename)
        logger.info("File inserted to bucket 'audios'")

        return {"message": "File uploaded successfully"}

    except Exception as e:
        logger.warning(f"Failed to upload file {file.filename} to bucket 'audios' {e}")
        return {"message": "File upload failed"}


@app.get("/list-files")
def list_files():
    try:
        logger.info("listing files")
        files = s3_client.list_objects(Bucket=BUCKET_NAME)
        return {"files": files}

    except Exception as e:
        logger.warning(f"Failed to list files in bucket 'audios' {e}")
        return {"message": "Failed to list files in bucket 'audios'"}