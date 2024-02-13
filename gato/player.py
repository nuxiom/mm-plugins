import importlib

import discord

import team
importlib.reload(team)


class PullsStatus:

    pities: dict[str, dict[int, int]]
    fiftyfifties: dict[str, dict[int, bool]]

    def __init__(self, **kwargs) -> None:
        self.pities = {
            "limited": {
                5: 0,
                4: 0
            },
            "permanent": {
                5: 0,
                4: 0
            }
        }
        self.fiftyfifties = {
            "limited": {
                5: True,
                4: True
            }
        }

        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_json(self):
        return {
            "pities": self.pities,
            "fiftyfifties": self.fiftyfifties
        }

    @classmethod
    def from_json(cls, d: dict):
        return cls(**d)


class Transactions:

    currency: float = 0.0
    add_items: list[str]
    rm_items: list[str]

    def __init__(self, **kwargs) -> None:
        self.add_items = []
        self.rm_items = []

        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_json(self):
        return {
            "currency": self.currency,
            "add_items": self.add_items,
            "rm_items": self.rm_items
        }

    @classmethod
    def from_json(cls, d: dict):
        return cls(**d)


class Player:

    nursery: list
    pulls_status: PullsStatus
    deployed_team: team.Team
    transactions: Transactions
    
    command_channel: int
    ping: bool
    user_id: int

    currency: float = 0
    inventory: list

    _pull_view: discord.ui.View


    def __init__(self, **kwargs) -> None:
        self.nursery = []
        self.pulls_status = PullsStatus()
        self.deployed_team = None
        self.transactions = Transactions()
        self.command_channel = None
        self.ping = True

        self._pull_view = None
        self.inventory = []

        for k, v in kwargs.items():
            setattr(self, k, v)


    def to_json(self):
        return {
            "nursery": [gato.to_json() for gato in self.nursery],
            "pulls_status": self.pulls_status.to_json(),
            "deployed_team": self.deployed_team.to_json(),
            "transactions": self.transactions,
            "command_channel": self.command_channel,
            "user_id": self.user_id,
            "ping": self.ping
        }

    @classmethod
    def from_json(cls, plyr: dict, curr: dict):
        plyr["nursery"] = [eval(g["type"]).from_json(g) for g in plyr["nursery"]]
        plyr["pulls_status"] = PullsStatus.from_json(plyr["pulls_status"])
        plyr["deployed_team"] = team.Team.from_json(plyr["deployed_team"], plyr["nursery"])
        plyr["transactions"] = Transactions.from_json(plyr["transactions"])
        return cls(**plyr)
