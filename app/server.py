import logging
import boto3
import botocore
import io
import cv2
import numpy as np

from botocore.client import Config
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from src.logger import LogHandler
from src.utils import convert_to_numpy, plot_image, resize_image_slices


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

        # Convert the file content to a numpy array
        image_np = convert_to_numpy(file_content)

        # Resize the image
        resized_image = resize_image_slices(image_np, target_width=150)

        # Convert the numpy array back to bytes
        _, image_bytes = cv2.imencode(".png", resized_image)
        image_bytes_io = io.BytesIO(image_bytes.tobytes())

        # Upload the resized image to MinIO
        file.filename = f"resized_{file.filename}"  # Optionally rename the file
        s3_client.upload_fileobj(image_bytes_io, BUCKET_NAME, file.filename)
        logger.info(f"Resized file {file.filename} uploaded to bucket '{BUCKET_NAME}'")

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


@app.get("/display-image/{file_name}")
async def display_image(file_name: str):
    try:
        # Get the file content
        file_content = s3_client.get_object(Bucket=BUCKET_NAME, Key=file_name)
        # Read the content
        image_data = file_content["Body"].read()

        # Convert the image data to a numpy array
        # img = convert_to_numpy(io.BytesIO(image_data))
        img = cv2.imdecode(np.frombuffer(image_data, np.uint8), -1)

        # Plot the image using the utility function
        buf = io.BytesIO()  # Create a buffer to hold the image bytes
        plot_image(img, buf)  # Pass the buffer to the plotting function

        # Seek to the start of the buffer
        buf.seek(0)

        # Stream the image back to the client
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        logger.warning(f"Failed to display image {file_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to display image {file_name}"
        )
