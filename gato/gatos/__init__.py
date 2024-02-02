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
import HertaGato
import FuxuanGato
import ClaraGato
import BladeGato
import GuinaifenGato
import NormalGato

importlib.reload(SwedeGato)
importlib.reload(LNYGato)
importlib.reload(ExampleGato)
importlib.reload(SeeleGato)
importlib.reload(QingqueGato)
importlib.reload(HertaGato)
importlib.reload(FuxuanGato)
importlib.reload(ClaraGato)
importlib.reload(BladeGato)
importlib.reload(GuinaifenGato)
importlib.reload(NormalGato)

Gato = ABaseGato.ABaseGato
SwedeGato = SwedeGato.SwedeGato
LNYGato = LNYGato.LNYGato
ExampleGato = ExampleGato.ExampleGato
SeeleGato = SeeleGato.SeeleGato
QingqueGato = QingqueGato.QingqueGato
HertaGato = HertaGato.HertaGato
FuxuanGato = FuxuanGato.FuxuanGato
ClaraGato = ClaraGato.ClaraGato
BladeGato = BladeGato.BladeGato
GuinaifenGato = GuinaifenGato.GuinaifenGato
NormalGato = NormalGato.NormalGato

## Items

import ABaseItem
importlib.reload(ABaseItem)
Item = ABaseItem.ABaseItem

# Consumables

import AConsumable
importlib.reload(AConsumable)

import RedPacketConsumable, TrashConsumable, MedkitConsumable

importlib.reload(RedPacketConsumable)
importlib.reload(TrashConsumable)
importlib.reload(MedkitConsumable)

Consumable = AConsumable.AConsumable
RedPacketConsumable = RedPacketConsumable.RedPacketConsumable
TrashConsumable = TrashConsumable.TrashConsumable
MedkitConsumable = MedkitConsumable.MedkitConsumable

CONSUMABLES = [RedPacketConsumable, TrashConsumable, MedkitConsumable]
