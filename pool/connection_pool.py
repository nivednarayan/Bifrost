import time
import asyncio

class ConnectionPool:
    def __init__(self, host: str, port: int, max_pool_size: int, ttl: int):
        self.pool = [] #list of (reader, writer, created_at) tuples
        self.host = host
        self.port = port
        self.max_pool_size = max_pool_size
        self.ttl = ttl

    async def acquire(self):
        if self.pool:
            reader, writer, created_at = self.pool.pop()
            if (time.time() - created_at) < self.ttl:
                return reader, writer, created_at
            else:
                writer.close()

        reader, writer = await asyncio.open_connection(self.host, self.port)
        return reader, writer, time.time()

    def release(self, reader, writer, created_at):
        if (time.time() - created_at) > self.ttl or len(self.pool) >= self.max_pool_size:
            writer.close()
        else:
            self.pool.append((reader, writer, created_at))
