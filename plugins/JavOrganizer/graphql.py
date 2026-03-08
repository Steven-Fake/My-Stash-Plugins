import re
from collections.abc import Callable

import stashapi.log as log
from stashapi.stashapp import StashInterface


def log_wrapper(func: Callable):
    def wrapper(*args, **kwargs):
        quiet = kwargs.get("quiet", False)
        if not quiet:
            log.info(f"Starting {func.__name__.replace("_", " ").capitalize()}...")
        result = func(*args, **kwargs)
        if not quiet:
            log.info(f"Completed {func.__name__.replace("_", " ").capitalize()}.")
        return result

    return wrapper


class GraphQLUtils:
    def __init__(self, config: dict):
        self.client = StashInterface(config)

    @log_wrapper
    def fill_scenes_title(self, quiet: bool = False):
        resp = self.client.find_scenes(
            f={"title": {"value": "", "modifier": "IS_NULL"}},
            fragment="id files { basename }"
        )
        total = len(resp)
        if not quiet:
            log.info("Found {} scenes without title".format(total))
        for i, item in enumerate(resp):
            if not quiet:
                log.progress(i / total)
            scene_id: str = item.get("id")
            for file_info in item.get("files", []):
                if filename := file_info.get("basename", ""):
                    title = filename[:filename.rindex('.')]
                    break
            else:
                continue
            self.client.update_scene({"id": scene_id, "title": title})

    @log_wrapper
    def fill_scenes_date(self, quiet: bool = False):
        self.fill_scenes_title(quiet=True)
        resp = self.client.find_scenes(
            f={
                "date": {"value": "", "modifier": "IS_NULL"},
                "title": {"value": "\\d{4}\\.\\d{2}\\.\\d{2}", "modifier": "MATCHES_REGEX"}
            },
            fragment="id title"
        )
        total = len(resp)
        if not quiet:
            log.info("Found {} scenes without date".format(total))
        for i, item in enumerate(resp):
            if not quiet:
                log.progress(i / total)
            date = re.search(r"\d{4}\.\d{2}\.\d{2}", item.get("title")).group()
            date = date.replace(".", "-")
            self.client.update_scene({"id": item.get("id"), "date": date})
