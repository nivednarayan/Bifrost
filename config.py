from dataclasses import dataclass
from typing import List, Tuple
import yaml

@dataclass
class Config:
    listen_port: int
    backends: List[Tuple[str, int]]
    algorithm: str
    syn_flood_threshold: int
    syn_flood_block_duration: int
    route: list[dict]
    l7_port: int

def load_config(path: str) -> Config:
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        return Config(
            listen_port=data["listen_port"],
            backends=[(b["host"], b["port"]) for b in data["backends"]],
            algorithm=data["algorithm"],
            syn_flood_threshold=data["syn_flood_threshold"],
            syn_flood_block_duration=data["syn_flood_block_duration"],
            route=data["routes"],
            l7_port=data["l7_port"],
        )
    except yaml.YAMLError as err:
        print(err)
        return None
