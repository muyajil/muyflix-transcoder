# muyflix-transcoder

This is a service that will transcode my media library using a specific profile that suits my media needs.

The transcoded media files will have the following properties:
- Maximum resolution of 1080p
- If available in the source file the transcoded file will contain English and German language tracks.
- If available in the source file the transcoded file will contain AAC, AC3, DTS, and DTSHD sound tracks.
- The transcoded file will be in a mp4 container encoded with x264

The rationale behind this is to optimize streaming performance while making as little compromise on quality as possible.
These settings will easily stream on a low powered Plex server, while not using much bandwith (since symmetrical bandwith is not yet the norm in Switzerland)

## Usage

The transcoding service in principle walks through the media library and transcodes any media files found that are not transcoded yet.

It is assumed that the media library is built to be compatible with Plex.

For this the following environment variables need to be set:

- `ROOT_DIR`: Root dir of media library. If this is mounted into the container make sure the absolute paths match on the host and the container.
- `TIMEOUT_MINS`: Time to wait between transcodes
- `RADARR_API_ROOT`: Where the API endpoint is for radarr. Sonarr scans the files on disk more frequently, but radarr does not do that for movies that are already downloaded. Therefore we use the api to force radarr to check for the new file when transcoding a movie.
- `RADARR_API_KEY`: API Key for radarr.

Further the user of the container should be set if you don't want the transcoded files to be owned by root.

Last but not least specifying the `cpuset` will allow the service to only occupy specific CPUs on your system, freeing up the rest for other services. 

### Docker run command

`docker run --user=UID:GID --cpuset-cpus=0,1,2,3 -v /your/media/root:/your/media/root -e ROOT_DIR=/your/media/root -e TIMEOUT_MINS=1 -e RADARR_API_ROOT=radarr:7878/api -e RADARR_API_KEY=apikey muyajil/muyflix-transcoder`

### Docker compose configuration


```
version: "2.2"

services:
  backup:
    image: muyajil/muyflix-transcoder:latest
    user: "UID:GID"
    cpuset: 0,1,2,3
    environment:
      ROOT_DIR: /your/media/root
      TIMEOUT_MINS: 1
      RADARR_API_ROOT: radarr:7878/api
      RADARR_API_KEY: apikey
    volumes:
      - /your/media/root:/your/media/root
    restart: unless-stopped

```