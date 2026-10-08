import asyncio
import time

class HealthChecker:
    def __init__(self, backends: list[tuple[str, int]]):
        self.backends = backends
        self.healthy = {backend: True for backend in backends}

    async def probe(self, host, port):
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=2)
            writer.write(b"GET /health HTTP/1.1\r\nHost: " + host.encode() + b"\r\n\r\n")
            await writer.drain()
            response = await asyncio.wait_for(reader.read(1024), timeout=2)
            writer.close()
            await writer.wait_closed()
            return len(response) > 0
        except:
            return False

    async def run(self, interval: int = 10):
        while True:
            for host, port in self.backends:
                self.healthy[(host, port)] = await self.probe(host, port)
            await asyncio.sleep(interval)

class CircuitBreaker:
    def __init__(self, threshold: int = 3, recovery_time: int = 30):
        self.threshold = threshold
        self.recovery_time = recovery_time
        self.failure_count = 0
        self.state = "closed"
        self.opened_at = None

    def is_open(self) -> bool:
        if self.state == "open":
            if time.time() - self.opened_at > self.recovery_time:
                self.state = "half-open"
                return False
            return True
        return False

    def record_success(self):
        self.state = "closed"
        self.failure_count = 0

    def record_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.threshold:
            self.state = "open"
            self.opened_at = time.time()
