# muyflix-transcoder

This is a service that will transcode my media library using a specific profile that suits my media needs.

## Usage

The transcoding service in principle walks through the media library and transcodes any media files found that are not transcoded yet.

It is assumed that the media library is built to be compatible with Plex.

For this the following environment variables need to be set:

- `ROOT_DIR`: Root dir of media library. If this is mounted into the container make sure the absolute paths match on the host and the container.
- `TIMEOUT_MINS`: Time to wait between transcodes
- `LOG_FILE_PATH`: Path to log file. The service writes some data to this file when starting/finishing a transcode such as file size etc.
- `RADARR_API_ROOT`: Where the API endpoint is for radarr. Sonarr scans the files on disk more frequently, but radarr does not do that for movies that are already downloaded. Therefore we use the api to force radarr to check for the new file when transcoding a movie.
- `RADARR_API_KEY`: API Key for radarr.


### Docker run command

`docker run -v /your/media/root:/your/media/root -v /path/to/logfile:/logs.csv -e ROOT_DIR=/your/media/root -e TIMEOUT_MINS=1 -e LOG_FILE_PATH=/logs.csv -e RADARR_API_ROOT=radarr:7878/api -e RADARR_API_KEY=apikey muyajil/muyflix-transcoder`

### Docker compose configuration


```
version: "3.5"

services:
  backup:
    image: muyajil/muyflix-transcoder:latest
    environment:
      ROOT_DIR: /your/media/root
      TIMEOUT_MINS: 1
      LOG_FILE_PATH: /logs.csv
      RADARR_API_ROOT: radarr:7878/api
      RADARR_API_KEY: apikey
    volumes:
      - /your/media/root:/your/media/root
      - /path/to/logfile:/logs.csv
    restart: unless-stopped

```