import argparse
import json
from datetime import datetime
from pathlib import Path

from .chart import build_chart


def main() -> None:
    p = argparse.ArgumentParser(description="Vedic birth chart to JSON")
    p.add_argument("--datetime", required=True, help="Local birth time, e.g. 1998-05-14T08:30")
    p.add_argument("--place", help="Birth place, e.g. 'Ahmedabad, India' (needs internet)")
    p.add_argument("--lat", type=float)
    p.add_argument("--lon", type=float)
    p.add_argument("--name")
    p.add_argument("--out", help="Write JSON to this file instead of stdout")
    a = p.parse_args()

    data = build_chart(datetime.fromisoformat(a.datetime), a.place, a.lat, a.lon, a.name)
    text = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text)


if __name__ == "__main__":
    main()