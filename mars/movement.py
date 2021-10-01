
from enum import Enum
import numpy as np
from typing import Dict, List


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


class Position:

    """Class used to represent a TCP position"""

    def __init__(self, pvector: np.array,
                 ptype: PositionType,
                 e1: int,
                 config: Configuration = None) -> 'Position':
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
            .__init__(pvector, PositionType.CARTESIAN, e1, config)

    def to_dict(self) -> Dict:
        """ get a dictionnary describing the cartesian position object

        Returns:
            Dict: dictionnary with Position object informations
        """
        vector_keys = ['x', 'y', 'z', 'w', 'p', 'r']
        tl = [(vector_keys[i], float(val))
              for i, val in enumerate(self._vector.tolist())]

        p_dict = dict((key.replace('_Position', ''), val)
                      for (key, val) in self.__dict__.copy().items())
        p_dict['_vector'] = dict(tl)
        return p_dict


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

        super(PositionJoint, self).__init__(pvector, PositionType.JOINT, e1)

    def to_dict(self) -> Dict:
        """ get a dictionnary describing the cartesian position object

        Returns:
            Dict: dictionnary with Position object informations
        """
        vector_keys = ['j1', 'j2', 'j3', 'j4', 'j5', 'j6']
        tl = [(vector_keys[i], float(val))
              for i, val in enumerate(self._vector.tolist())]

        p_dict = dict((key.replace('_Position', ''), val)
                      for (key, val) in self.__dict__.copy().items())
        p_dict['_vector'] = dict(tl)
        return p_dict


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
        self.__position: Path = position
        self.__path: Position = path

    @property
    def position(self):
        return self.__position


class Movement:

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
