from datetime import datetime
from typing import Optional

class Team:

    gatos: list

    deployed_at: Optional[datetime] = None

    def __init__(self, gatos: list, deployed_at = datetime.now()):
        self.deployed_at = deployed_at
        self.gatos = gatos

    def to_json(self):
        return {
            "gatos": [gato.DISPLAY_NAME for gato in self.gatos],
            "deployed_at": None if self.deployed_at is None else self.deployed_at.timestamp()
        }

    @classmethod
    def from_json(cls, d: dict, nursery: list):
        gatos = [[gato for gato in nursery if gato.DISPLAY_NAME == DISPLAY_NAME][0] for DISPLAY_NAME in d["gatos"]]
        deployed_at = datetime.fromtimestamp(d["deployed_at"])
        return cls(gatos, deployed_at)
