import hashlib
from abc import ABC, abstractmethod

class LoadBalancingAlgorithm(ABC):
    def __init__(self, backends: list[tuple[str, int]]):
        self.backends = backends
    
    @abstractmethod
    def next_backend(self, client_ip: str = None) -> tuple[str, int]:
        pass
    
    def increment(self, backend):
        pass
    def decrement(self, backend):
        pass

class RoundRobin(LoadBalancingAlgorithm):
    def __init__(self, backends):
        super().__init__(backends)
        self.index = 0
    
    def next_backend(self, client_ip=None):
        backend = self.backends[self.index % len(self.backends)]
        self.index += 1
        return backend

class LeastConnections(LoadBalancingAlgorithm):
    def __init__(self, backends):
        super().__init__(backends)
        self.connections = {b: 0 for b in backends}
    
    def next_backend(self, client_ip=None):
        return min(self.connections, key=self.connections.get)
    
    def increment(self, backend):
        self.connections[backend] += 1
    
    def decrement(self, backend):
        self.connections[backend] -= 1

class IPHash(LoadBalancingAlgorithm):
    def next_backend(self, client_ip=None):
        hash_val = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        return self.backends[hash_val % len(self.backends)]
