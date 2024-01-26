import logging
import boto3
import botocore
import io
import cv2
import numpy as np
import pandas as pd
from base64 import b64encode

from botocore.client import Config
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from src.logger import LogHandler
from src.utils import plot_image, resize_image_keep_depth, convert_to_array, get_slice


logger = logging.getLogger(__file__)
logger.setLevel("DEBUG")
logger.addHandler(LogHandler())

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory="templates")

session = boto3.session.Session()

s3_client = session.client(
    service_name="s3",
    aws_access_key_id="minio",
    aws_secret_access_key="minio123",
    endpoint_url="http://minio:9000",
    config=Config(signature_version="s3v4"),
)

BUCKET_NAME = "images"

try:
    s3_client.head_bucket(Bucket=BUCKET_NAME)
except botocore.exceptions.ClientError as e:
    logger.info(f"Creating bucket: {BUCKET_NAME}")
    s3_client.create_bucket(Bucket=BUCKET_NAME)


logger.info(f"Connected to bucket {BUCKET_NAME}")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    try:
        logger.info("Listing files at root")
        response = s3_client.list_objects(Bucket=BUCKET_NAME)
        files = [file["Key"] for file in response.get("Contents", [])]
        return templates.TemplateResponse(
            "file_selector.html", {"request": request, "files": files}
        )
    except Exception as e:
        logger.warning(f"Failed to list files in bucket '{BUCKET_NAME}' at root: {e}")
        return {"message": f"Failed to list files in bucket '{BUCKET_NAME}' at root"}


@app.post("/upload-file")
def upload_file(file: UploadFile = File(...)):
    """
    Store files as numpy arrays in MinIO.

    :param file: The file to upload.
    :return: A message indicating if the upload was successful.
    """
    try:
        # Read the file content into memory
        file_content = io.BytesIO(file.file.read())

        # Resize the image
        resized_image = resize_image_keep_depth(file_content, 150)

        csv_buffer = io.StringIO()
        resized_image.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        # Upload the CSV to MinIO
        file.filename = f"resized_{file.filename.replace('.png', '.csv')}"  # Rename the file with the correct extension
        s3_client.put_object(Bucket=BUCKET_NAME, Key=file.filename, Body=csv_buffer.getvalue())
        logger.info(f"Resized CSV {file.filename} uploaded to bucket '{BUCKET_NAME}'")

        return {"message": "File uploaded and resized successfully"}

    except Exception as e:
        logger.warning(
            f"Failed to upload and resize file {file.filename} to bucket '{BUCKET_NAME}': {e}"
        )
        return {"message": "File upload and resize failed"}


@app.get("/list-files")
def list_files():
    try:
        logger.info("Listing files")
        response = s3_client.list_objects(Bucket=BUCKET_NAME)
        files = [file["Key"] for file in response.get("Contents", [])]
        return {"files": files}
    except Exception as e:
        logger.warning(f"Failed to list files in bucket '{BUCKET_NAME}' {e}")
        return {"message": f"Failed to list files in bucket '{BUCKET_NAME}'"}


@app.get("/display-image/{file_name}", response_class=HTMLResponse)
async def display_image(request: Request, file_name: str, min_depth: float = None, max_depth: float = None):
    # Render the form initially without image data
    if min_depth is None or max_depth is None:
        return templates.TemplateResponse("image_viewer.html", {"request": request, "file_name": file_name, "img_data": None})

    try:
        # Get the file content
        file_content = s3_client.get_object(Bucket=BUCKET_NAME, Key=file_name)

        # Read content of CSV into a dataframe
        image_data = pd.read_csv(file_content['Body'])

        # Get the slice of the image based on depth
        sliced_df = get_slice(image_data, min_depth, max_depth)
        img_np = convert_to_array(sliced_df)

        # Plot the image using the utility function
        buf = io.BytesIO()
        plot_image(img_np, buf)
        buf.seek(0)

        # Convert the buffer content to a base64 string to embed in HTML
        img_data = b64encode(buf.read()).decode('utf-8')

        # Render the template with the image data
        return templates.TemplateResponse("image_viewer.html", {"request": request, "file_name": file_name, "img_data": img_data})
    except Exception as e:
        logger.warning(f"Failed to display image {file_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to display image {file_name}")
