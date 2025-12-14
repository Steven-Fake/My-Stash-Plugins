from typing import TypedDict, Literal


class PluginConfig(TypedDict):
    video_hwaccel: Literal["QSV", "NVENC", "CPU", "VAAPI"]
