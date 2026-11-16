import json
import sys


def walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            walk(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, f"{path}[{i}]")
    else:
        print(path, "=", obj)


walk(json.load(open(sys.argv[1], encoding="utf-8")))