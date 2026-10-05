import time
from core.L7.parser import HTTPRequest
from collections import defaultdict

req_headers = {"User-Agent", "Accept", "Accept-Language", "Accept-Encoding"}
request_times: dict[str, list[float]] = defaultdict(list)

def is_bot_by_headers(request: HTTPRequest) -> bool:
    for header in req_headers:
        if header not in request.headers:
            return True
    return False

def is_bot_by_cadence(ip: str, max_requests: int = 10, window_seconds: int = 1) -> bool:
    now = time.time()
    request_times[ip].append(now)
    request_times[ip] = [t for t in request_times[ip] if now - t < window_seconds]
    return len(request_times[ip]) > max_requests

def is_bot_by_connection_timing(connection_time: float, request_time: float, threshold: float = 0.1):
    return (request_time - connection_time) < threshold
