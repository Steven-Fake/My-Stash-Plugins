from collections.abc import Callable
from typing import Literal

from stashapi.stashapp import StashInterface
import re
import stashapi.log as log
from pathlib import Path
from my_types import PluginConfig


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

    def get_plugin_config(self) -> PluginConfig:
        resp = self.client.get_configuration(
            fragment="plugins"
        )
        config: dict = resp.get("plugins", {}).get("GalleryOrganizer", {})
        video_hwaccel: str = config.get("video_hwaccel", "CPU")
        if video_hwaccel not in ["CPU", "NVENC", "QSV", "VAAPI"]:
            video_hwaccel: Literal["CPU", "NVENC", "QSV", "VAAPI"] = "CPU"

        return PluginConfig(
            video_hwaccel=video_hwaccel
        )

    @log_wrapper
    def fill_galleries_title(self, quiet: bool = False):
        resp = self.client.find_galleries(
            f={
                "title": {"value": "", "modifier": "IS_NULL"}
            },
            fragment="""
                id
                files { basename }
                folder { path }
                """
        )
        total = len(resp)
        if not quiet:
            log.info("Found {} galleries without title".format(total))
        for i, item in enumerate(resp):
            if not quiet:
                log.progress(i / total)
            gallery_id: str = item.get("id")
            if (item.get("folder") or {}).get("path", ""):
                title = Path(item.get("folder").get("path")).name
            elif len(item.get("files", [])) > 0:
                zip_name = item.get("files", [])[0].get("basename", "")
                title = zip_name[:zip_name.rindex('.')]
            else:
                continue
            self.client.update_gallery({"id": gallery_id, "title": title})

    @log_wrapper
    def fill_galleries_date(self, quiet: bool = False):
        self.fill_galleries_title(quiet=True)
        resp = self.client.find_galleries(
            f={
                "date": {"value": "", "modifier": "IS_NULL"},
                "title": {"value": "\\d{4}\\.\\d{2}\\.\\d{2}", "modifier": "MATCHES_REGEX"}
            },
            fragment="""
            id
            title
            """
        )
        total = len(resp)
        if not quiet:
            log.info("Found {} galleries without date".format(total))
        for i, item in enumerate(resp):
            if not quiet:
                log.progress(i / total)
            date = re.search(r"\d{4}\.\d{2}\.\d{2}", item.get("title")).group()
            date = date.replace(".", "-")
            self.client.update_gallery({"id": item.get("id"), "date": date})

    @log_wrapper
    def add_galleries_performers(self, quiet: bool = False):
        self.fill_galleries_title(quiet=True)
        resp = self.client.find_galleries(
            f={
                "performer_count": {"value": 0, "modifier": "EQUALS"}
            },
            fragment="""
                id
                title
                """
        )
        total = len(resp)
        if not quiet:
            log.info("Found {} galleries without performers".format(total))
        for i, item in enumerate(resp):
            if not quiet:
                log.progress(i / total)
            gallery_id: str = item.get("id")
            performer_names = [name.strip() for name in item.get("title").split("_")[-1].split(",")]
            performer_ids = []
            for name in performer_names:
                performer_resp = self.client.find_performers(q=name, fragment="""id name alias_list""")
                if performer_resp:
                    for performer in performer_resp:
                        if name == performer.get("name") or name in performer.get("alias_list", []):
                            performer_ids.append(performer.get("id"))
            if performer_ids:
                self.client.update_gallery({"id": gallery_id, "performer_ids": performer_ids})

    @log_wrapper
    def add_galleries_tags(self, quiet: bool = False):
        def extract_tags_from_title(title: str) -> list[str]:
            category = re.search(r'\[.+\]', title).group()[1:-1]
            tags = []
            for part in title.removeprefix(f"[{category}]").split("_")[:-1]:
                tags.extend([tag.strip() for tag in part.split(",")])
            return [category] + tags

        self.fill_galleries_title(quiet=True)
        resp = self.client.find_galleries(
            f={
                "title": {"value": "^\\[(杂图|写真)\\]", "modifier": "NOT_MATCHES_REGEX"},
                "tag_count": {"value": 2, "modifier": "LESS_THAN"},
            },
            fragment="id title tags { id name aliases }"
        )
        tags_cache_map: dict[str, str] = {}  # tag_name: tag_id
        unknown_tags: dict[str, int] = {}  # tag_name: count

        total = len(resp)
        if not quiet:
            log.info("Found {} galleries to add tags".format(total))
        for i, item in enumerate(resp):
            if not quiet:
                log.progress(i / total)

            title: str = item.get("title", "")
            for tag in item.get("tags", []):  # update cache
                tags_cache_map[tag.get("name")] = tag.get("id")

            curr_tag_map = {}
            tag_names = extract_tags_from_title(title)
            for name in tag_names:
                if name in tags_cache_map.keys():
                    curr_tag_map[name] = tags_cache_map[name]
                else:  # from database
                    tag_resp = self.client.find_tag(name, fragment="id name aliases")
                    if tag_resp and (name == tag_resp.get("name") or name in tag_resp.get("aliases", [])):
                        tags_cache_map[name] = tag_resp.get("id")
                        curr_tag_map[name] = tag_resp.get("id")
                    else:
                        unknown_tags[name] = unknown_tags.get(name, 0) + 1
            self.client.update_gallery({"id": item.get("id"), "tag_ids": list(curr_tag_map.values())})
        if unknown_tags:
            sorted_unknown = sorted(unknown_tags.items(), key=lambda kv: kv[1], reverse=True)
            log.warning(", ".join([k for k, v in sorted_unknown if v >= 2]))

    def get_galleries_paths(self) -> list[Path]:
        resp = self.client.get_configuration(
            fragment="""
            general {
              stashes {
                path
                excludeVideo
                excludeImage
              }
            }"""
        )
        items = resp.get("general", {}).get("stashes", [])
        return [
            Path(item.get("path"))
            for item in items if item.get("excludeImage") == False
        ]
