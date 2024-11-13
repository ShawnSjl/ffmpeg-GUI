SUPPORT_FILE_FORMAT = [
    "avi",
    "flv",
    "mkv",
    "mp4",
    "mov",
    "wmv"
]

SUPPORT_VIDEO_ENCODE_FORMAT = {
    "H.264": "libx264",
    "H.265": "libx265",
    "VP8": "libvpx",
    "VP9": "libvpx-vp9",
    "AV1": "libaom-av1",
    "MPEG-2": "mpeg2video",
    "ProRes": "prores",
    "CineForm": "cfhd",
    "MJPEG": "mjpeg",
    "Theora": "libtheora"
}

ENCODE_SPEED = [
    "ultrafast",
    "superfast",
    "veryfast",
    "faster",
    "fast",
    "medium",
    "slow",
    "slower",
    "veryslow",
    "placebo"
]

DEFAULT_FFMPEG_PATH = "./ffmpeg/ffmpeg"