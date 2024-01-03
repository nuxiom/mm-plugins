from datetime import datetime
from typing import Optional

from gatos import Gato

class Team:

    gatos: list[Gato]

    deployed_at: Optional[datetime] = None

    def __init__(self, gatos: list[Gato]):
        self.deployed_at = datetime.now()
        self.gatos = gatos
