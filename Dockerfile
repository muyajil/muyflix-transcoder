FROM jlesage/handbrake:latest

RUN apk add --no-cache --update py3-pip python3 libmediainfo

RUN pip3 install --upgrade pip

RUN pip3 install pymediainfo requests retry

COPY transcode_library.py /transcode_library.py

ENTRYPOINT [ "python3", "-u", "/transcode_library.py" ]
