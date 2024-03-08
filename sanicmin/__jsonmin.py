from json import dumps
from json import loads


def json_min(content: str) -> str:
    try:
        return dumps(loads(s=content), separators=(",", ":"))
    
    except:
        return content
