
from typing import Dict, Sequence
from mars.definition import Definition
import mars.proxyapi as proxyapi
from enum import Enum


class Manipulation(Enum):
    LOAD = "LOAD"
    UNLOAD = "UNLOAD"


class ToolManipulation(Definition):

    """ Class used to describe a Tool manipulation
    """
    def __init__(self, ut: int, uf: int, tool_type: str,
                 tool_ref: str, manipulation: Manipulation):
        self.__ut: int = ut
        self.__uf: int = uf
        self.__tool_ref: str = tool_ref
        self.__tool_type: str = tool_type
        self.__manip: Manipulation = manipulation

    @staticmethod
    def parse(serialise_manip: Dict) -> 'ToolManipulation':
        ut = serialise_manip['ut']
        uf = serialise_manip['uf']
        tool_type = serialise_manip['tool_type']
        tool_ref = serialise_manip['tool_reference']
        manip = Manipulation[serialise_manip['manipulation']]

        return ToolManipulation(ut,
                                uf,
                                tool_type,
                                tool_ref,
                                manip)

    def to_dict(self):
        return {
            'ut': self.__ut,
            'uf': self.__uf,
            'tool_type': self.__tool_type,
            'tool_reference': self.__tool_ref,
            'manipulation': self.__manip.value
        }

    def get_sequence(self):
        sequence = proxyapi.ihm_maniptool_request(self.__tool_type,
                                                  self.__tool_ref,
                                                  self.__manip.value)
        sequence.append(proxyapi.utuf_set_request(self.__uf, self.__ut))
        sequence.extend(proxyapi.launch_program_request(proxyapi.ProgramCode.CHANGE_UTUF))
        
        return sequence


class LoadManipulation(ToolManipulation):

    def __init__(self, ut: int, uf: int, tool_type: str, tool_ref: str):
        ToolManipulation.__init__(self, ut, uf,
                                  tool_type, tool_ref,
                                  Manipulation.LOAD)

    def get_sequence(self):
        sequence = super().get_sequence()
        sequence.append(proxyapi.utuf_set_request(self._uf, self._ut))
        sequence.extend(proxyapi
                        .launch_program_request(proxyapi
                                                .ProgramCode.CHANGE_UTUF))

        return sequence


class UnloadManipulation(ToolManipulation):
    def __init__(self, ut: int, uf: int, tool_type: str, tool_ref: str):
        ToolManipulation.__init__(self, ut, uf,
                                  tool_type, tool_ref,
                                  Manipulation.UNLOAD)

    def get_sequence(self):
        return super().get_sequence()
