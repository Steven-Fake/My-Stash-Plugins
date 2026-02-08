import json
import sys

from PythonDepManager import ensure_import

from graphql import GraphQLUtils

ensure_import("stashapi:stashapp-tools")
ensure_import("bs4:beautifulsoup4")

if __name__ == "__main__":
    info = json.loads(sys.stdin.read())
    mode = info.get("args", {}).get("mode")

    graphql_utils = GraphQLUtils(info.get("server_connection"))

    if mode == "galleries_date":
        graphql_utils.fill_galleries_date()
    elif mode == "galleries_title":
        graphql_utils.fill_galleries_title()
    elif mode == "galleries_performers":
        graphql_utils.add_galleries_performers()
    elif mode == "galleries_tags":
        graphql_utils.add_galleries_tags()

    elif mode == "sort_jvid_galleries":
        graphql_utils.sort_jvid_galleries()
