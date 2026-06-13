import json
import sys

from PythonDepManager import ensure_import

from graphql import GraphQLUtils

try:
    ensure_import("stashapi:stashapp-tools")
except Exception as e:
    print(f"Error installing dependencies: {e}")

if __name__ == "__main__":
    info = json.loads(sys.stdin.read())
    mode = info.get("args", {}).get("mode")

    graphql_utils = GraphQLUtils(info.get("server_connection"))

    if mode == "jav_tags":
        graphql_utils.fill_jav_tags()
