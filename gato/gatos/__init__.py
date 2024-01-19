import importlib
import os
import sys
DIR = os.path.dirname(__file__)
sys.path.append(DIR)

# Gatos

import ABaseGato
importlib.reload(ABaseGato)

import SwedeGato
import ExampleGato, LNYGato
import SeeleGato
import QingqueGato
import NormalGato

importlib.reload(SwedeGato)
importlib.reload(LNYGato)
importlib.reload(ExampleGato)
importlib.reload(SeeleGato)
importlib.reload(QingqueGato)
importlib.reload(NormalGato)

Gato = ABaseGato.ABaseGato
SwedeGato = SwedeGato.SwedeGato
LNYGato = LNYGato.LNYGato
ExampleGato = ExampleGato.ExampleGato
SeeleGato = SeeleGato.SeeleGato
QingqueGato = QingqueGato.QingqueGato
NormalGato = NormalGato.NormalGato

## Items

import ABaseItem
importlib.reload(ABaseItem)
Item = ABaseItem.ABaseItem

# Consumables

import AConsumable
importlib.reload(AConsumable)

import RedPacketConsumable, TrashConsumable, MedikitConsumable

importlib.reload(RedPacketConsumable)
importlib.reload(TrashConsumable)
importlib.reload(MedikitConsumable)

Consumable = AConsumable.AConsumable
RedPacketConsumable = RedPacketConsumable.RedPacketConsumable
TrashConsumable = TrashConsumable.TrashConsumable
MedikitConsumable = MedikitConsumable.MedikitConsumable

CONSUMABLES = [RedPacketConsumable, TrashConsumable, MedikitConsumable]
