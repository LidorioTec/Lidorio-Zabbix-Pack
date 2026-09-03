"""LT Samba FS - LLD JSON output."""
import json
from . import shares


def discover_shares_json():
    data = shares.discover()
    return json.dumps({"data": [{"{#SHARE}": s["{#SHARE}"]}
                                 for s in data["shares"]],
                        "method": data["method"],
                        "count": data["count"]})
