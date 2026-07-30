from collections.abc import Callable

import stashapi.log as log
from stashapi.stashapp import StashInterface


def log_wrapper(func: Callable):
    def wrapper(*args, **kwargs):
        quiet = kwargs.get("quiet", False)
        if not quiet:
            log.info(f"Starting {func.__name__.replace('_', ' ').capitalize()}...")
        result = func(*args, **kwargs)
        if not quiet:
            log.info(f"Completed {func.__name__.replace('_', ' ').capitalize()}.")
        return result

    return wrapper


class GraphQLUtils:
    def __init__(self, config: dict):
        self.client = StashInterface(config)

    def format_tag(self, tag: dict, category_name: str, prefix: list[str]):
        """rec sort"""
        prefix.append(tag.get("name"))
        sort_name = f"[{category_name}]{'_'.join(prefix)}"
        # path suffixes from leaf up to the full path: c, b_c, a_b_c
        computed = [
            "_".join(prefix[-length:]) for length in range(1, len(prefix) + 1)
        ]
        computed.append(sort_name)

        current = self.client.find_tag(
            tag_in=int(tag.get("id")),
            fragment="id aliases children { id name sort_name }",
        )
        # keep aliases that already existed (e.g. manually added) and merge
        existing_aliases = current.get("aliases") or []
        aliases = list(dict.fromkeys([*existing_aliases, *computed]))

        new_tag = {
            "id": int(tag.get("id")),
            "name": tag.get("name"),
            "sort_name": sort_name,
            "aliases": aliases,
        }
        self.client.update_tag(new_tag)

        children = current.get("children") or []
        try:
            for child in children:
                self.format_tag(tag=child, category_name=category_name, prefix=prefix)
        finally:
            prefix.pop()

    @log_wrapper
    def format_cosplay_tags(self, quiet: bool = False):

        root_tag_resp = self.client.find_tags(
            f={"name": {"value": "(Category) ACGN", "modifier": "EQUALS"}},
            fragment="id name children { id  name}",
        )
        if not root_tag_resp:
            return
        categories: list = root_tag_resp[0].get("children") or []
        total = len(categories)
        for i, category in enumerate(categories):
            log.progress(i / total)
            category_id = category.get("id")
            category_name = category.get("name")
            if not category_id or not category_name:
                continue
            children = (
                self.client.find_tag(
                    tag_in=int(category_id),
                    fragment="children { id name sort_name }",
                ).get("children")
                or []
            )
            for child in children:
                self.format_tag(tag=child, category_name=category_name, prefix=[])
