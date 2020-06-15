FROM jlesage/handbrake:latest

RUN apk add --no-cache --update python3 libmediainfo

RUN pip3 install --upgrade pip

RUN pip3 install pymediainfo requests retry

COPY transcode_library.py /transcode_library.py

ENTRYPOINT [ "python3", "/transcode_library.py" ]