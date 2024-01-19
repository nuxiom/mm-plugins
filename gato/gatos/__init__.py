import importlib
import os
import sys
DIR = os.path.dirname(__file__)
sys.path.append(DIR)

# Gatos

import ABaseGato
importlib.reload(ABaseGato)

import ExampleGato, NormalGato, LNYGato, SeeleGato

importlib.reload(ExampleGato)
importlib.reload(NormalGato)
importlib.reload(LNYGato)
importlib.reload(SeeleGato)

Gato = ABaseGato.ABaseGato
ExampleGato = ExampleGato.ExampleGato
NormalGato = NormalGato.NormalGato
LNYGato = LNYGato.LNYGato
SeeleGato = SeeleGato.SeeleGato

# Consumables

import AConsumable
importlib.reload(AConsumable)

import RedPacketConsumable

importlib.reload(RedPacketConsumable)

Consumable = AConsumable.AConsumable
RedPacketConsumable = RedPacketConsumable.RedPacketConsumable

CONSUMABLES = [RedPacketConsumable]
