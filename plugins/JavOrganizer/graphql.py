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
    def fill_jav_tags(self, quiet: bool = False):
        uncensored_search = self.client.find_tags(
            f={"aliases": {"value": "Uncensored", "modifier": "EQUALS"}}
        )
        uncensored_crack_search = self.client.find_tags(
            f={"aliases": {"value": "Uncensored Crack", "modifier": "EQUALS"}}
        )
        censored_search = self.client.find_tags(
            f={"aliases": {"value": "Censored", "modifier": "EQUALS"}}
        )

        uncensored_tag_id = uncensored_search[0].get("id") if uncensored_search else None
        uncensored_crack_tag_id = uncensored_crack_search[0].get("id") if uncensored_crack_search else None
        censored_tag_id = censored_search[0].get("id") if censored_search else None
        if not (uncensored_tag_id and uncensored_crack_tag_id and censored_tag_id):
            log.warning("No related tags found")
            return

        resp = self.client.find_scenes(
            f={"path": {"value": "/Jav/", "modifier": "INCLUDES"}},
            fragment="id files { basename } tags { id }"
        )

        total = len(resp)
        if not quiet:
            log.info("Found {} Jav to add tags".format(total))
        for i, item in enumerate(resp):
            if not quiet:
                log.progress(i / total)
            name: str = item.get("files")[0].get("basename").split(".")[0]
            old_tags = [t.get("id") for t in item.get("tags")]
            if name.endswith("-UC-C") or name.endswith("-UC"):
                if uncensored_crack_tag_id not in old_tags:
                    old_tags.append(uncensored_crack_tag_id)
            elif name.endswith("-U-C") or name.endswith("-U"):
                if uncensored_tag_id not in old_tags:
                    old_tags.append(uncensored_tag_id)
            else:
                if censored_tag_id not in old_tags:
                    old_tags.append(censored_tag_id)
            self.client.update_scene({"id": item.get("id"), "tag_ids": old_tags})
