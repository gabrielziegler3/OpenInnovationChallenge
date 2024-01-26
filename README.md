# OpenInnovationChallenge

Server for uploading and visualizing 3d images that are stored in a MinIO server after having their width resized to 150.


## Tests

The project contains a few tests, but ideally, the whole `src/` and `server.py` would be tested and run in a CI/CD pipeline.

To run tests, run from the project root:

```
pytest
```

## Running

### Spin up the containers

```
docker-compose up
```

This will spin up the MinIO server and the FastAPI server.

### Upload images

Go to `http://localhost:80` and upload a csv file like the one provided. The image will be parsed, resized and will be available to be viewed from `http://localhost:80`.

### View images

Go to `http://localhost:80` and click on the image you want to view. The image will displayed in the browser using the colormap inferno.

## Next steps

- Add more tests
- Add CI/CD pipeline
- Add the ability to choose colormap and interactive
- Add the ability to choose the width
- Move from MinIO to AWS S3
- Check if CSV is the best format for the image (perhaps HDF5 or some other format would be better)
- This server could be running on an ECS cluster, with a load balancer in front of it. We could easily move it to the cloud using Terraform or CloudFormation.
