import subprocess
from platform import system
from multiprocessing import cpu_count
import stashapi.log as log
from typing import Literal


class TerminalUtils:
    # WARNING: unfinished class
    def __init__(self):
        self.image_convert_threads = cpu_count() // 2 if cpu_count() > 4 else 1
        self.os_name: Literal["Windows", "Linux"] = system()

    def check_envs(self):
        """Check: FFmpeg、ExifTool、bz(Windows)、zip(Linux)"""
        if self.os_name not in ["Windows", "Linux"]:
            log.error(f"Unsupported OS: {self.os_name}")
            raise EnvironmentError(f"Unsupported OS: {self.os_name}")

        check_commands = {
            "FFmpeg": ["ffmpeg", "-version"],
            "ExifTool": ["exiftool", "-ver"],
            "zip": ["bz"] if self.os_name == "Windows" else ["zip", "-v"]
        }
        for tool, command in check_commands.items():
            try:
                subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                log.info(f"{tool} is installed.")
            except (subprocess.CalledProcessError, FileNotFoundError):
                log.error(f"{tool} is not installed or not found in PATH.")
                raise EnvironmentError(f"{tool} is not installed or not found in PATH.")

    # TODO
