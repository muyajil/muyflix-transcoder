import os
from datetime import datetime
from socket import timeout
import subprocess
import shutil
from pymediainfo import MediaInfo
import time
import requests
import json
from retry import retry


def get_file_size_gb(path):
    num_bytes = os.path.getsize(path)
    return num_bytes / (2 ** 30)


def get_absolute_paths(root_dir):
    for dirpath, _, filenames in os.walk(root_dir):
        for f in filenames:
            yield os.path.abspath(os.path.join(dirpath, f))


def is_video(file_path):
    fileInfo = MediaInfo.parse(file_path)
    for track in fileInfo.tracks:
        if track.track_type == "Video":
            return True
    return False


def is_info_file(file_path):
    return file_path.endswith(("jpg", "nfo", "transcodelog", "istranscoded"))


def get_quality_tag(file_path):
    fileInfo = MediaInfo.parse(file_path)
    for track in fileInfo.tracks:
        if track.track_type == "Video":
            if track.height <= 360:
                return " - DVD"
            elif 360 < track.height <= 460:
                return " - SDTV"
            elif 460 < track.height <= 480:
                return " - WEB-DL-480p"
            elif 480 < track.height <= 720:
                return " - WEB-DL-720p"
            elif 720 < track.height <= 1080:
                return " - WEB-DL-1080p"
            else:
                return " - WEB-DL-2160p"
    return ""


def get_tag_file_path(file_path, ending):
    quality_tag = get_quality_tag(file_path)
    if quality_tag in file_path:
        return os.path.splitext(file_path)[0] + "." + ending
    return os.path.splitext(file_path)[0] + quality_tag + "." + ending


def is_transcoded(file_path):
    return os.path.isfile(
        get_tag_file_path(file_path, "istranscoded")
    ) and os.path.isfile(get_tag_file_path(file_path, "mp4"))


def get_relevant_file_paths(root_dir):
    file_paths = get_absolute_paths(root_dir)
    file_paths = filter(lambda f: "/movies/" in f or "/tv/" in f, file_paths)
    file_paths = filter(lambda f: "partial" not in f, file_paths)

    return file_paths


def get_properties(file_path):
    parts = file_path.split("/")
    for idx, part in enumerate(parts):
        if part in ("tv", "movies"):
            item_type = part
            folder_name = parts[idx + 1]
            break
    item_name = parts[-1]
    return item_type, folder_name, item_name


@retry(subprocess.CalledProcessError, delay=60)
def transcode_single(file_path, root_dir):
    new_file_path = get_tag_file_path(file_path, "mp4")
    new_file_path = new_file_path.replace("tmp", root_dir)

    temp_file_name = os.path.basename(new_file_path)

    if "movies" in new_file_path:
        width, height = "3840", "2160"
    else:
        width, height = "1920", "1080"

    command = ["HandBrakeCLI"]
    command.extend(["-i", file_path])
    command.extend(["-o", "/tmp/{}".format(temp_file_name)])
    command.extend(
        [
            "-f",
            "av_mp4",
            "-e",
            "x264",
            "-q",
            "23",
            "--audio-lang-list",
            "eng,ger,und",
            "--vfr",
            "-E",
            "copy:ac3,copy:aac,copy:dts,copy:dtshd",
            "-Y",
            height,
            "-X",
            width,
            "--optimize",
        ]
    )

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result.check_returncode()

    os.remove(file_path)

    shutil.move("/tmp/{}".format(temp_file_name), new_file_path)

    with open(os.path.splitext(new_file_path)[0] + ".istranscoded", "w"):
        pass

    return new_file_path


def get_movie_filename(movie_id):
    response = requests.get(
        "{}/movie/{}?apikey={}".format(
            os.environ.get("RADARR_API_ROOT"),
            movie_id,
            os.environ.get("RADARR_API_KEY"),
        )
    )
    movie = response.json()
    if "movieFile" in movie:
        return movie["movieFile"]["relativePath"]
    else:
        return ""


def update_movie_radarr(old_file_name, new_file_name):
    response = requests.get(
        "{}/movie?apikey={}".format(
            os.environ.get("RADARR_API_ROOT"), os.environ.get("RADARR_API_KEY")
        , timeout=180)
    )

    for movie in response.json():
        if movie["hasFile"]:
            if movie["movieFile"]["relativePath"] == old_file_name:
                tries = 0
                while get_movie_filename(movie["id"]) != new_file_name and tries < 5:
                    data = {"name": "RefreshMovie", "movieIds": [movie["id"]]}
                    _ = requests.post(
                        "{}/command?apikey={}".format(
                            os.environ.get("RADARR_API_ROOT"),
                            os.environ.get("RADARR_API_KEY"),
                        ),
                        data=json.dumps(data),
                        headers={"Content-Type": "application/json"},
                    )
                    time.sleep(10)
                    tries += 1
                return


def transcode_library_complete(root_dir, timeout_mins):
    transcoded_files = 0

    file_paths = get_relevant_file_paths(root_dir)

    for file_path in file_paths:
        transcode_start = datetime.now()
        item_type, folder_name, item_name = get_properties(file_path)

        try:
            if (
                not is_info_file(file_path)
                and not is_transcoded(file_path)
                and is_video(file_path)
            ):

                print("--------------------------------------------------------------------------", flush=True)
                print(
                    "Started Transcoding!\n\tCurrent Time: {}\n\tFile: {}\n\tSize: {:.2f}GB".format(
                        datetime.now().isoformat(" ", "seconds"),
                        item_name,
                        get_file_size_gb(file_path)
                    ),
                    flush=True
                )

                new_file_path = transcode_single(file_path, root_dir)

                if item_type == "movies":
                    update_movie_radarr(
                        os.path.basename(file_path), os.path.basename(new_file_path)
                    )

                elapsed_time = datetime.now() - transcode_start
                print(
                    "Finished Transcoding!\n\tCurrent Time: {}\n\tFile: {}\n\tSize: {:.2f}GB\n\tTranscoding Time: {}".format(
                        datetime.now().isoformat(" ", "seconds"),
                        os.path.basename(new_file_path),
                        get_file_size_gb(new_file_path),
                        elapsed_time,
                    ),
                    flush=True
                )
                print("--------------------------------------------------------------------------", flush=True)

                time.sleep(timeout_mins * 60)
                transcoded_files += 1
        except FileNotFoundError:
            continue

    return transcoded_files


if __name__ == "__main__":
    print('Starting transcoding process...', flush=True)
    while True:
        transcoded_files = transcode_library_complete(
            os.environ.get('ROOT_DIR'),
            int(os.environ.get('TIMEOUT_MINS'))
        )
        if transcoded_files == 0:
            print('No files were transcoded, waiting for new files...', flush=True)
            time.sleep(5 * 3600)
