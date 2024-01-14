import glob
import os
import re
from collections.abc import Callable
from pathlib import Path

from pathvalidate import sanitize_filename, sanitize_filepath
from pathvalidate.error import ValidationError
from tidalapi import Album, Mix, Playlist, Track, UserPlaylist, Video


def path_base():
    if "XDG_CONFIG_HOME" in os.environ:
        return os.environ["XDG_CONFIG_HOME"]
    elif "HOME" in os.environ:
        return os.environ["HOME"]
    elif "HOMEDRIVE" in os.environ and "HOMEPATH" in os.environ:
        return os.path.join(os.environ["HOMEDRIVE"], os.environ["HOMEPATH"])
    else:
        return os.path.abspath("./")


def path_file_log():
    return os.path.join(path_base(), ".tidal-dl-ng.log")


def path_file_token():
    return os.path.join(path_base(), ".tidal-dl-ng_token.json")


def path_file_settings():
    return os.path.join(path_base(), ".tidal-dl-ng_settings.json")


def format_path_media(fmt_template: str, media: Track | Album | Playlist | UserPlaylist | Video | Mix) -> str:
    result = fmt_template

    # Search track format template for placeholder.
    regex = r"\{(.+?)\}"
    matches = re.finditer(regex, fmt_template, re.MULTILINE)
    fn_format = get_fn_format(media)

    for _matchNum, match in enumerate(matches, start=1):
        template_str = match.group()
        result_fmt = fn_format(match.group(1), media)

        if result_fmt:
            value = sanitize_filename(result_fmt)
            result = result.replace(template_str, value)

    return result


def format_str_track(name: str, media: Track) -> str | bool:
    result: str | bool = False

    if name == "track_num":
        result = str(media.track_num).rjust(2, "0")
    elif name == "artist_name":
        result = ", ".join(artist.name for artist in media.artists)
    elif name == "track_title":
        result = media.name

    return result


def format_str_album(name: str, media: Album) -> str | bool:
    result: str | bool = False

    if name == "album_title":
        result = media.name
    elif name == "artist_name":
        result = media.artist.name

    return result


def format_str_playlist(name: str, media: Playlist) -> str | bool:
    result: str | bool = False

    if name == "playlist_name":
        result = media.name

    return result


def format_str_mix(name: str, media: Mix) -> str | bool:
    result: str | bool = False

    if name == "mix_name":
        result = media.title

    return result


def format_str_video(name: str, media: Video) -> str | bool:
    result: str | bool = False

    if name == "artist_name":
        result = ", ".join(artist.name for artist in media.artists)
    elif name == "track_title":
        result = media.name

    return result


def get_fn_format(media: Track | Album | Playlist | UserPlaylist | Video | Mix) -> Callable:
    result = None

    if isinstance(media, Track):
        result = format_str_track
    elif isinstance(media, Album):
        result = format_str_album
    elif isinstance(media, Playlist | UserPlaylist):
        result = format_str_playlist
    elif isinstance(media, Mix):
        result = format_str_mix
    elif isinstance(media, Video):
        result = format_str_video

    return result


def path_file_sanitize(path_file: str, adapt: bool = False) -> (bool, str):
    # Split into path and filename
    pathname, filename = os.path.split(path_file)

    # Sanitize path
    try:
        pathname_sanitized = sanitize_filepath(
            pathname, replacement_text=" ", validate_after_sanitize=True, platform="auto"
        )
    except ValidationError:
        # If adaption of path is allowed in case of an error set path to HOME.
        if adapt:
            pathname_sanitized = Path.home()
        else:
            raise

    # Sanitize filename
    try:
        filename_sanitized = sanitize_filename(
            filename, replacement_text=" ", validate_after_sanitize=True, platform="auto"
        )
        filename_sanitized_extension = Path(filename_sanitized).suffix

        # Check if the file extension was removed by shortening the filename length
        if filename_sanitized_extension == "":
            # Add the original file extension
            file_extension = "_" + Path(path_file).suffix
            filename_sanitized = filename_sanitized[: -len(file_extension)] + file_extension
    except ValidationError as e:
        # TODO: Implement proper exception handling and logging.
        print(e)

        raise

    # Join path and filename
    result = os.path.join(pathname_sanitized, filename_sanitized)

    return result


def check_file_exists(path_file: str, extension_ignore: bool = False):
    if extension_ignore:
        path_file = Path(path_file).stem + ".*"

    # TODO: Check what happens is (no) files .
    result = bool(glob.glob(path_file))

    return result
