import asyncio
from collections import defaultdict

class SYNFloodDetector:
    def __init__(self, threshold: int = 10, block_duration: int = 60):
        self.half_open = defaultdict(int)
        self.blocked = {}
        self.threshold = threshold
        self.block_duration = block_duration

    def connection_received(self, ip: str):
        self.half_open[ip] += 1

    def connection_completed(self, ip: str):
        self.half_open[ip] = max(0, self.half_open[ip] - 1)

    def is_blocked(self, ip: str) -> bool:
        if ip in self.blocked:
            if asyncio.get_event_loop().time() < self.blocked[ip]:
                return True
            else:
                self.half_open[ip] = 0
                del self.blocked[ip]
        if self.half_open[ip] >= self.threshold:
            self.blocked[ip] = asyncio.get_event_loop().time() + self.block_duration
            return True
        return False
