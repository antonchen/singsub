FROM --platform=$BUILDPLATFORM python:3.12.11-slim-bullseye

COPY . /singsub
WORKDIR /singsub
RUN \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /singsub/requirements.txt

EXPOSE 5000
CMD [ "gunicorn", "-c", "gunicorn.conf.py", "main:app"]