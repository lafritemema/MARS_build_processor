
import abc
from enum import Enum
import numpy as np
from typing import Dict, List
from mars.definition import Definition
import mars.proxyapi as proxyapi


class Path(Enum):
    """Path type enumeration

    Args:
        Enum (char): fanuc path code
    """

    CIRCULAR = 'C'
    LINEAR = 'L'
    JOINT = 'J'


class PositionType(Enum):

    """tcp position representation type enumeration

    Args:
        Enum (str): fanuc tcp position representation type
    """
    JOINT = 'jnt'
    CARTESIAN = 'crt'


class WristConfig(Enum):
    """wrist configuration enumerator

    Args:
        Enum (char): fanuc wrist config code
    """
    FLIP = 'F'
    NOFLIP = 'N'


class ForeArmConfig(Enum):
    """ForeArm configuration enumerator

    Args:
        Enum (char): fanuc forearm config code
    """
    UP = 'U'
    DOWN = 'D'


class ArmConfig(Enum):
    """Arm configuration enumerator

    Args:
        Enum (char): fanuc arm config code
    """
    TOWARD = 'T'
    BACKWARD = 'D'


class Configuration:
    """Class used to represent the arm configuration
    """
    def __init__(self, wrist: WristConfig,
                 forearm: ForeArmConfig,
                 arm: ArmConfig,
                 j4: int = 0,
                 j5: int = 0,
                 j6: int = 0) -> 'Configuration':
        """Configuration object initializer

        Args:
            wrist (WristConfig): wrist configuration enumeration (FLIP|NOFLIP)
            forearm (ForeArmConfig): forearm configuration
                enumeration (UP|DOWN)
            arm (ArmConfig): arm configuration
                enumeration (TOWARD|BACKWARD)
            j4 (int, optional) : max rotation code for j4, default 0
            j5 (int, optional) : max rotation code for j5, default 0
            j6 (int, optional) : max rotation code for j6, default 0
        """
        self.__wrist: WristConfig = wrist
        self.__forearm: ForeArmConfig = forearm
        self.__arm: ArmConfig = arm
        self.__j4: int = 0
        self.__j5: int = 0
        self.__j6: int = 0

    @staticmethod
    def parse(serialize_config: Dict) -> 'Configuration':
        wrist = WristConfig[serialize_config['wrist']]
        forearm = ForeArmConfig[serialize_config['forearm']]
        arm = ArmConfig[serialize_config['arm']]
        j4 = serialize_config['j4']
        j5 = serialize_config['j5']
        j6 = serialize_config['j6']

        return Configuration(wrist, forearm, arm, j4, j5, j6)

    def to_dict(self):
        return {
            "wrist": self.__wrist.name,
            "forearm": self.__forearm.name,
            "arm": self.__arm.name,
            "j4": self.__j4,
            "j5": self.__j5,
            "j6": self.__j6
        }


class Position:

    """Class used to represent a TCP position"""

    __metaclass__ = abc.ABCMeta

    def __init__(self,
                 pvector: np.array,
                 ptype: PositionType,
                 e1: int,
                 vector_keys: List[str],
                 config: Configuration = None,
                 ut: int = 0,
                 uf: int = 0) -> 'Position':
        """
        Position object initializer

        Args:
            pvector (np.array): tcp position vector
            ptype (PositionType): position type enumeration
            e1 (int): 7 axis position
            config (Configuration): Arm configuration
        """

        self._vector: np.array = pvector
        self.__type: PositionType = ptype
        self.__config: Configuration = config
        self.__e1: int = e1
        self.__vector_keys = vector_keys
        self.__ut = ut
        self.__uf = uf

    @property
    def vector(self):
        return self._vector

    @vector.setter
    def vector(self, nvector):
        self._vector = nvector

    @property
    def e1(self):
        return self.__e1

    @e1.setter
    def e1(self, ne1):
        self.__e1 = ne1

    @property
    def type(self):
        return self.__type

    @staticmethod
    def parse(serialize_position) -> 'Position':
        type = serialize_position['type']
        if type == 'CARTESIAN':
            return PositionCrt.parse(serialize_position)
        elif type == 'JOINT':
            return PositionJoint.parse(serialize_position)
        else:
            raise Exception('position parsing default')

    def to_dict(self) -> Dict:
        """ get a dictionnary describing the cartesian position object

        Returns:
            Dict: dictionnary with Position object informations
        """

        return {
            "ut": self.__ut,
            "uf": self.__uf,
            "type": self.__type.name,
            "e1": self.__e1,
            "vector": self.__vector_to_dict(),
            "config": self.__config.to_dict() if self.__config else None
        }

    def get_sequence(self):
        return {
            "ut": self.__ut,
            "uf": self.__uf,
            "type": self.__type.value,
            "e1": self.__e1,
            "vector": self.__vector_to_dict(),
            "config": self.__config.to_dict() if self.__config else None
        }

    def __vector_to_dict(self):
        tl = [(self.__vector_keys[i], float(val))
              for i, val in enumerate(self._vector.tolist())]
        return dict(tl)


class PositionCrt(Position):

    """ Class used to represent a Position in cartesian representation
    Inherit from Position Class"""

    def __init__(self, pvector: np.array,
                 e1: int,
                 config: Configuration) -> 'PositionCrt':
        """PositionCrt object initializer

        Args:
            pvector (np.array): tcp position vector
            e1 (int): 7 axis position
            config (Configuration): Arm configuration
        """
        # initialize Position Object with CARTESIAN position type

        super(PositionCrt, self)\
            .__init__(pvector, PositionType.CARTESIAN,
                      e1, ['x', 'y', 'z', 'w', 'p', 'r'], config)

    @staticmethod
    def parse(serialize_crtpos: Dict) -> 'PositionCrt':
        e1 = serialize_crtpos['e1']
        config = Configuration.parse(serialize_crtpos['config'])

        svector = serialize_crtpos['vector']
        vector_keys = ['x', 'y', 'z', 'w', 'p', 'r']
        vector_array = [svector[key] for key in vector_keys]
        vector = np.array(vector_array)

        return PositionCrt(vector, e1, config)


class PositionJoint(Position):

    """ Class used to represent a Position in joint representation
    Inherit from Position Class"""

    def __init__(self, pvector: np.array, e1: int):
        """[summary]

        Args:
            pvector (np.array): tcp position vector
            e1 (int): 7 axis position
        """

        # initialize Position Object with JOINT position type.
        # no Configuration need for JOINT position type

        super(PositionJoint, self)\
            .__init__(pvector, PositionType.JOINT, e1,
                      ['j1', 'j2', 'j3', 'j4', 'j5', 'j6'])

    @staticmethod
    def parse(serialize_jntpos: Dict) -> 'PositionJoint':
        e1 = serialize_jntpos['e1']

        svector = serialize_jntpos['vector']
        vector_keys = ['j1', 'j2', 'j3', 'j4', 'j5', 'j6']
        vector_array = [svector[key] for key in vector_keys]
        vector = np.array(vector_array)

        return PositionJoint(vector, e1)


class Point:

    """ Class used to represent a movement passing point
    """
    def __init__(self, cnt: int,
                 speed: int,
                 path: Path,
                 position: Position) -> 'Point':
        """Point object initializer

        Args:
            cnt (int): passing accuracy from the point
            speed (int): movement speed
            path (Path): trajectory shape
            position (Position): tcp position
        """
        self.__cnt: int = cnt
        self.__speed: int = speed
        self.__position: Position = position
        self.__path: Path = path

    @property
    def position(self):
        return self.__position

    @staticmethod
    def parse(serialize_point: Dict) -> 'Point':
        cnt = serialize_point['cnt']
        path = Path[serialize_point['path']]
        speed = serialize_point['speed']
        position = Position.parse(serialize_point['position'])

        return Point(cnt, speed, path, position)

    def to_dict(self):
        return {
            "cnt": self.__cnt,
            "speed": self.__speed,
            "position": self.__position.to_dict(),
            "path": self.__path.name
        }

    def get_sequence(self) -> Dict:

        path = proxyapi.PathCode[self.__path.name].value

        return {
            "settings": [path, self.__speed, self.__cnt],
            "position": self.__position.get_sequence()
        }


class Movement(Definition):

    """ Class used to represent a Movement
    """
    def __init__(self, uf: int, ut: int, points: List[Point]):
        """Movement object initializer

        Args:
            uf (int): user frame id
            ut (int): user tool id
            points (List[Point]): list of points describing the movement
        """
        self._uf: int = uf
        self._ut: int = ut
        self._points: List[Point] = points

    @staticmethod
    def parse(serialize_movement: Dict) -> 'Movement':
        ut = serialize_movement['ut']
        uf = serialize_movement['uf']
        points = []

        for sp in serialize_movement['points']:
            points.append(Point.parse(sp))

        return Movement(uf, ut, points)

    def to_dict(self):
        return {
            "uf": self._uf,
            "ut": self._ut,
            "points": [p.to_dict() for p in self._points]
        }

    def get_sequence(self):
        # first info in setting -> nbr of pos register write
        points_settings = [len(self._points)]
        points_parameters = []

        for p in self._points:
            p_para = p.get_sequence()
            points_parameters.append(p_para['position'])
            points_settings.extend(p_para['settings'])

        # if only one point -> position_set_request else positions_set_request
        if len(points_parameters) > 1:
            position_set_request = proxyapi\
                .positions_set_request(points_parameters)
        else:
            position_set_request = proxyapi\
                .position_set_request(points_parameters[0])

        possettings_set_request = proxyapi\
            .possettings_set_request(points_settings)

        sequence = []

        # first stage set uf and ut
        sequence.append(proxyapi.utuf_set_request(self._uf, self._ut))

        # second stage set num reg 1 to launch change UTUF program
        # and wait for program end
        # return list so sequence extend
        sequence.extend(proxyapi
                        .launch_program_request(proxyapi
                                                .ProgramCode.CHANGE_UTUF))

        # third stage set numeric register 20 to X
        # update position settings (speed, path ...)
        if (type(possettings_set_request) == list):
            sequence.extend(possettings_set_request)
        else:
            sequence.append(possettings_set_request)

        # fourth stage set position register 20 to X
        # update position settings (speed, path ...)
        if(type(position_set_request) == list):
            sequence.extend(position_set_request)
        else:
            sequence.append(position_set_request)

        # fifth stage set num reg 1 to launch change TRAJ_GEN program
        sequence.extend(proxyapi
                        .launch_program_request(proxyapi.ProgramCode.TRAJ_GEN))

        return sequence
