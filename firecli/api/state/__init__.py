from typing import Dict
from rich.console import Console
from firecli.api import API


class State:
    def __init__(self, api: API, cfg: Dict, console: Console):
        self.api = api
        self.cfg = cfg
        self.console = console
        self.state = {}
