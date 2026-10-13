from core.L7.parser import HTTPRequest

def route_request(request: HTTPRequest, routes: list[dict]) -> dict | None:
    for route in routes:
        if request.path.startswith(route["path"]):
            return route
    return None
