from datetime import datetime

from gatos import Gato

class Team:

    gatos: list[Gato]

    deployed_at: datetime = None

    def __init__(self, gatos: list[Gato]):
        deployed_at = datetime.now()
