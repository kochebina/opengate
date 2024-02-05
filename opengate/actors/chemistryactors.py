import opengate_core as g4
from .base import ActorBase


class ChemistryActor(g4.GateChemistryActor, ActorBase):
    """
    """

    type_name = "ChemistryActor"

    def set_default_user_info(user_info):
        ActorBase.set_default_user_info(user_info)

    def __init__(self, user_info):
        ActorBase.__init__(self, user_info)
        g4.GateChemistryActor.__init__(self, user_info.__dict__)

    def __str__(self):
        u = self.user_info
        s = f'ChemistryActor "{u.name}": dim={u.size} spacing={u.spacing} {u.output} tr={u.translation}'
        return s

    def __getstate__(self):
        # superclass getstate
        ActorBase.__getstate__(self)
        return self.__dict__

    def initialize(self, volume_engine=None):
        super().initialize(volume_engine)

    def StartSimulationAction(self):
        pass

    def EndSimulationAction(self):
        pass
