FROM jlesage/handbrake:latest

RUN apk add --no-cache --update python3 libmediainfo

RUN pip install --upgrade pip

RUN pip install pymediainfo requests retry

COPY transcode_library.py /transcode_library.py

ENTRYPOINT [ "python3", "-u", "/transcode_library.py" ]
