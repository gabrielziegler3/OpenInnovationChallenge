FROM python:3.12-slim

RUN python --version

RUN pip install -U pip

WORKDIR /app

COPY ./requirements.txt /tmp/requirements.txt

COPY . /

RUN pip install -r /tmp/requirements.txt

RUN pip freeze

# CMD ["uvicorn", "server:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]