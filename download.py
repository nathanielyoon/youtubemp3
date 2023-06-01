from typing import Any
import os
import pathlib
import datetime

import yt_dlp


def postprocessor_hook(info: dict[str, Any]) -> None:
    if info["postprocessor"] == "MoveFiles" and info["status"] == "finished":
        file_info = [
            f'{datetime.datetime.now():%Y-%m-%d %H:%M:S.%f}',
            info["info_dict"]["filepath"].split("/")[-2],
            info["info_dict"]["filepath"].split("/")[-1]
        ]
        with open("output/downloads.csv", "a") as csv_file:
            csv_file.write(f'{",".join(file_info)}\n')


PATH = pathlib.Path(__file__).parent.resolve()
YDL_OPTIONS = {
    "quiet": True,
    "format": "m4a/mp3",
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3"
    }],
    "paths": {"home": os.path.join(PATH, "output")},
    "outtmpl": {"default": "%(id)s/%(title)s"},
    "postprocessor_hooks": [postprocessor_hook]
}


def download_url(url: str) -> None:
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as downloader:
        downloader.download([url])
