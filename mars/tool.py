
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
        self._ut: int = ut
        self._uf: int = uf
        self._tool_ref: str = tool_ref
        self._tool_type: str = tool_type
        self._manip: Manipulation = manipulation

    @staticmethod
    def parse(serialise_manip: Dict) -> 'ToolManipulation':
        ut = serialise_manip['ut']
        uf = serialise_manip['uf']
        tool_type = serialise_manip['tool_type']
        tool_ref = serialise_manip['tool_reference']
        manip = Manipulation[serialise_manip['manipulation']]

        if manip == Manipulation.LOAD:
            return LoadManipulation(ut,
                                    uf,
                                    tool_type,
                                    tool_ref)
        elif manip == Manipulation.UNLOAD:
            return UnloadManipulation(ut,
                                      uf,
                                      tool_type,
                                      tool_ref)
        else:
            raise Exception("Error : tool manipulation {manip} unknow !".format(manip = serialise_manip['manipulation']))

    def to_dict(self):
        return {
            'ut': self._ut,
            'uf': self._uf,
            'tool_type': self._tool_type,
            'tool_reference': self._tool_ref,
            'manipulation': self._manip.value
        }
    '''
    def __get_sequence(self):
        sequence = proxyapi.ihm_maniptool_request(self.__tool_type,
                                                  self.__tool_ref,
                                                  self.__manip.value)
        
        return sequence
    '''

class LoadManipulation(ToolManipulation):

    def __init__(self, ut: int, uf: int, tool_type: str, tool_ref: str):
        super(LoadManipulation, self).__init__(ut, uf,
                                  tool_type, tool_ref,
                                  Manipulation.LOAD)

    def get_sequence(self):
        sequence = proxyapi.ihm_maniptool_request(self._tool_type,
                                                  self._tool_ref,
                                                  self._manip.value)
        sequence.append(proxyapi.utuf_set_request(self._uf, self._ut))
        sequence.extend(proxyapi
                        .launch_program_request(proxyapi
                                                .ProgramCode.CHANGE_UTUF))

        return sequence


class UnloadManipulation(ToolManipulation):
    def __init__(self, ut: int, uf: int, tool_type: str, tool_ref: str):
        super(UnloadManipulation, self).__init__(ut, uf,
                                  tool_type, tool_ref,
                                  Manipulation.UNLOAD)

    def get_sequence(self):
        sequence = proxyapi.ihm_maniptool_request(self._tool_type,
                                                  self._tool_ref,
                                                  self._manip.value)
        sequence.append(proxyapi.utuf_set_request(self._uf, self._ut))
        sequence.extend(proxyapi
                        .launch_program_request(proxyapi
                                                .ProgramCode.CHANGE_UTUF))
        return sequence
