from typing import Dict, List
from enum import Enum
from copy import deepcopy


class ProgramCode(Enum):
    TRAJ_GEN = 1
    CHANGE_UTUF = 3


class Action(Enum):
    REQUEST = "REQUEST"
    WAIT = "WAIT"

class PathCode(Enum):
    JOINT = 1
    LINEAR = 2
    CIRCULAR = 3

def utuf_set_request(uf, ut):
    data = {
        "action": Action.REQUEST.value,
        "decription": "send user tool and user frame informations\
                      (NUMREG 18 et 19)",
        "definition": {
            "method": "PUT",
            "api": "/numericRegister/block",
            "query": {
                "startReg": 18,
                "blockSize": 2,
                "type": "int"
            },
            "body": {
                "data": {
                    "values": [uf, ut]
                }
            }
        }
    }

    return data


def launch_program_request(program_code: ProgramCode) -> List[Dict]:
    data = [{
                "action": Action.REQUEST.value,
                "decription": "send program to launch : {program} (NUM REG 1)"
                              .format(program=program_code.name),
                "definition": {
                    "method": "PUT",
                    "api": "/numericRegister/single",
                    "query": {
                        "reg": 1,
                        "type": "int"
                    },
                    "body": {
                        "data": {
                            "value": program_code.value
                            }
                        }
                    }
            },
            {
                "action": Action.REQUEST.value,
                "decription": "init tracker to alert for value 0\
                    on program register (NUM REG 1)",
                "definition": {
                    "method": "SUBSCRIBE",
                    "api": "/numericRegister/single",
                    "query": {
                        "reg": 1,
                        "type": "int"
                    },
                    "body": {
                        "setting": {
                            "type": "tracker",
                            "settings": {
                                "tracker": "alert",
                                "value": {
                                    "value": 0
                                },
                                "interval": 1000,
                                "id": "trackernum"
                            }
                        }
                    }
                }
            },
            {
                "action": Action.WAIT.value,
                "decription": "wait program execution end",
                "definition": {}
            }]

    return data


def __get_registers_limit(reg_type: str, action: str) -> int:
    max_reg = {
        "string": {
            "read": 5,
            "write": 5
        },
        "position": {
            "read": 10,
            "write": 10
        },
        "numeric": {
            "read": 120,
            "write": 115
        }
    }

    if reg_type in max_reg and action in ['read', 'write']:
        return max_reg[reg_type][action]
    else:
        raise Exception('error to get register limits')


def __split_register_data(register_data: List[Dict or int or str],
                          limit: int) -> List[List[Dict]]:
    sub_list = []
    i = 0
    step = 0
    while i < len(register_data):
        step += 1
        sub_list.append(register_data[i:step*limit])
        i += limit

    return sub_list


def possettings_set_request(pos_settings: List[int]) -> Dict or List[Dict]:
    data = {
        "action": Action.REQUEST.value,
        "decription": "send movement positions settings (speed, path, cnt)",
        "definition": {
            "method": "PUT",
            "api": "/numericRegister/block",
            "query": {
                "startReg": None,
                "blockSize": None,
                "type": "int"
            },
            "body": {
                "data": {
                    "values": None
                }
            }
        }
    }

    limit = __get_registers_limit("numeric", "write")
    if len(pos_settings) > limit:
        data_list = []

        pos_settings_list = __split_register_data(pos_settings, limit)
        i = 20
        for ps in pos_settings_list:
            psdata = deepcopy(data)
            psdata['definition']['query']['startReg'] = i
            psdata['definition']['query']['blockSize'] = len(ps)
            psdata['definition']['body']['data']['values'] = ps
            data_list.append(psdata)
            i += len(ps)

        return data_list
    else:
        data['definition']['query']['startReg'] = 20
        data['definition']['query']['blockSize'] = len(pos_settings)
        data['definition']['body']['data']['values'] = pos_settings
        return data


def position_set_request(position: Dict):
    data = {
            "action": Action.REQUEST.value,
            "decription": "set movement position parameters",
            "definition": {
                "method": "PUT",
                "api": "/positionRegister/single",
                "query": {
                    "reg": 1,
                    "type": position['type']
                },
                "body": {
                    "data": {
                        "position": position
                    }
                }
            }
        }

    return data


def positions_set_request(positions: List[Dict]):
    data = {
        "action": Action.REQUEST.value,
        "decription": "set movement positions parameters",
        "definition": {
            "method": "PUT",
            "api": "/positionRegister/block",
            "query": {
                "startReg": None,
                "blockSize": None,
                "type": positions[0]['type']
            },
            "body": {
                "data": {
                    "positions": None
                }
            }
        }
    }

    limit = __get_registers_limit("position", "write")
    if len(positions) > limit:
        data_list = []

        pos_settings_list = __split_register_data(positions, limit)
        i = 1
        for ps in pos_settings_list:
            psdata = deepcopy(data)
            psdata['definition']['query']['startReg'] = i
            psdata['definition']['query']['blockSize'] = len(ps)
            psdata['definition']['body']['data']['positions'] = ps
            data_list.append(psdata.copy())
            i += len(ps)

        return data_list
    else:
        data['definition']['query']['startReg'] = 1
        data['definition']['query']['blockSize'] = len(positions)
        data['definition']['body']['data']['positions'] = positions
        return data
