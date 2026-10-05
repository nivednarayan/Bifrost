from core.L7.parser import HTTPRequest

def route_request(request: HTTPRequest, routes: list[dict]) -> list[tuple[str, int]]:
    for route in routes:
        if request.path.startswith(route["path"]):
            return [(b["host"], b["port"]) for b in route["backends"]]
    return []
