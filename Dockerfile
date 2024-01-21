FROM --platform=$BUILDPLATFORM python:3.9.18-alpine3.18

COPY . /singsub
RUN \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /singsub/requirements.txt

EXPOSE 5000

CMD [ "python", "/singsub/main.py" ]