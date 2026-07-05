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
        aliases = [
            "_".join(prefix[-1 * length + 1 :]) for length in range(1, len(prefix))
        ]
        aliases.append(sort_name)

        new_tag = {
            "id": int(tag.get("id")),
            "name": tag.get("name"),
            "sort_name": sort_name,
            "aliases": aliases,
        }
        if len(aliases) < len(prefix):
            self.client.update_tag(new_tag)

        children = (
            self.client.find_tag(
                tag_in=int(tag.get("id")),
                fragment="children { id name sort_name }",
            ).get("children")
            or []
        )
        for child in children:
            self.format_tag(tag=child, category_name=category_name, prefix=prefix)

    @log_wrapper
    def format_cosplay_tags(self, quiet: bool = False):

        root_tag_resp = self.client.find_tags(
            f={"name": {"value": "(Category) ACGN", "modifier": "EQUALS"}},
            fragment="id name children { id  name}",
        )
        if not root_tag_resp or len(root_tag_resp) < 0:
            return
        categories: list = root_tag_resp[0].get("children")
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
