from enum import Enum, EnumMeta
from typing import List, Optional


class EnumLevelInterface(EnumMeta):

    """
    Enumerator Level interface
    """
    def __getitem__(self, name: str):
        """
        overload __getitem__() function
        """

        dot = name.find('.')
        if dot != -1:
            cindex = name[:dot]
            oindex = name[(dot+1):]
            e = super().__getitem__(cindex).value
            return e.__getitem__(oindex)
        else:
            e = super().__getitem__(name)
            if EnumPriorityInterface in e.__class__.__bases__:
                return e
            else:
                return e.value


class EnumPriorityInterface(Enum, metaclass=EnumLevelInterface):
    """"
    Enumerator Priority interface
    """
    def __init__(self, priority: int, name: str):
        """ EnumPriorityInterface enumerator initializer

        Args:
            priority (int): action type priority
            name (str): action type name
        """
        self.__priority: int = priority
        self.__name: str = name

    @property
    def priority(self) -> int:
        """ get action type priority

        Returns:
            int: action type priority
        """
        return self.__priority

    @property
    def name(self) -> str:
        """get action type name

        Returns:
            str:action type name
        """
        return self.__name


class ActionArmMove(EnumPriorityInterface, metaclass=EnumLevelInterface):
    # enumeration MOVE.ARM with 3 modes : APPROACH CLEARANCE WORK
    APPROACH = (50, 'MOVE.ARM.APPROACH')
    CLEARANCE = (50, 'MOVE.ARM.CLEARANCE')
    WORK = (60, 'MOVE.ARM.WORK')


class ActionStationMove(EnumPriorityInterface, metaclass=EnumLevelInterface):
    # enumeration MOVE.STATION with 2 modes : WORK HOME
    WORK = (40, 'MOVE.STATION.WORK')
    HOME = (40, 'MOVE.STATION.HOME')


class ActionWork(EnumPriorityInterface, metaclass=EnumLevelInterface):
    # enumeration WORK with 2 modes : DRILL FASTEN
    DRILL = (70, 'WORK.DRILL')
    FASTEN = (80, 'WORK.FASTEN')


class ActionLoad(EnumPriorityInterface, metaclass=EnumLevelInterface):
    # enumeration LOAD with 2 elements EFFECTOR TOOL
    EFFECTOR = (20, 'LOAD.EFFECTOR')
    TOOL = (30, 'LOAD.TOOL')


class ActionUnload(EnumPriorityInterface, metaclass=EnumLevelInterface):
    # enumeration UNLOAD with 2 elements EFFECTOR TOOL
    EFFECTOR = (20, 'UNLOAD.EFFECTOR')
    TOOL = (30, 'UNLOAD.TOOL')


class ActionMove(Enum, metaclass=EnumLevelInterface):
    # sous enumeration MOVE avec 2 element ARM et station
    ARM = ActionArmMove
    STATION = ActionStationMove


class ActionType(Enum, metaclass=EnumLevelInterface):
    # enumeration racine with 3 actions LOAD UNLOAD MOVE WORK
    LOAD = ActionLoad
    UNLOAD = ActionUnload
    MOVE = ActionMove
    WORK = ActionWork


# action object
class Action:

    """Class used to represent a robot basic action.

    Attributes
    ----------
    id : str
        the action id
    dependencies : List[Action]
        list of dependencies actions
    next : List[Action]
        list of next actions
    definition : object
        definition object. read only
    priority : int
        action priority. read only
    description : str
        action description
    type : str
        action type name. read only

    Methods
    -------
    add_dependences(action)
        add a new action in the dependences list

    add_next(action)
        add a new action in the next list

    """

    def __init__(self, id: str,
                 atype: ActionType,
                 definition: object,
                 description: str,
                 upstream_dependences: Optional[List["Action"]] = [],
                 downstream_dependences: Optional[List["Action"]] = []):

        """Action object initializer

        Args:
            id (str): unique action id
            atype (ActionType): action type enumerator
            definition (object): action definition according action type
            description (str): human readable description
            upstream_dependences (list[Action], optional): action must done
            before the action. Defaults to [].
            downstream_dependences (list[Action], optional): action done
            after the action. Defaults to [].
        """

        self.__id: str = id
        self.__type: ActionType = atype
        self.__definition: object = definition
        self.__upstream_dependences: List["Action"] = upstream_dependences
        self.__downstream_dependences: List["Action"] = downstream_dependences
        self.__description: str = description

    # getter and setters
    @property
    def id(self) -> str:
        """ get the action id

        Returns:
            str: action id
        """
        return self.__id

    @id.setter
    def id(self, nid: str):
        """ function to avoid id redefinition
        """
        raise ValueError("id redefinition forbidden")

    @property
    def upstream_dependences(self) -> List['Action']:
        """ get the list of upstream_dependences actioins

        Returns:
            List[Action]: the action list of dependencies
        """
        return self.__upstream_dependences

    @upstream_dependences.setter
    def upstream_dependences(self, dl: List['Action']):
        """ set the list of upstream_dependences actions

        Args:
            dl (List[Action]): new dependences action list
        """
        self.__upstream_dependences = dl

    @property
    def downstream_dependences(self) -> List['Action']:
        """ get the list of downstream_dependences actions

        Returns:
            List[Action]: list of next actions
        """
        return self.__downstream_dependences

    @downstream_dependences.setter
    def downstream_dependences(self, nl: List['Action']):
        """ set the list of downstream_dependences actions

        Args:
            nl (List[Action]): new dependences actions list
        """
        self.__downstream_dependences = nl

    @property
    def type(self) -> str:
        """ get the action type name

        Returns:
            str :  type name
        """
        return self.__type.name

    @type.setter
    def type(self, ntype: ActionType):
        """function to avoid type redefinition
        """
        raise ValueError("type redefinition forbidden")

    @property
    def definition(self) -> object:
        """ get the definition object

        Returns:
            object: action definition
        """
        return self.__definition

    @definition.setter
    def definition(self, ndef: object):
        """ function to avoid definition redefinition
        """
        raise ValueError("definition redefinition forbidden")

    @property
    def priority(self) -> int:
        """ get the action priority according to the type of action

        Returns:
            int: action priority
        """
        return self.__type.priority

    @priority.setter
    def priority(self, npriority: int):
        """ function to avoid priority redefinition
        """
        raise ValueError("priority redefinition forbidden")

    @property
    def description(self) -> str:
        """ get the action description

        Returns:
            str: action description
        """

        return self.__description

    @description.setter
    def description(self, ndesc: str):
        """ set the action description

        Args:
            ndesc (str): new action description
        """

    # methods
    def add_upstream_dependence(self, action: 'Action'):
        """ add a new action in the upstream_dependence list

        Args:
            action (Action): new action
        """
        self.__upstream_dependences.append(action)

    def add_downstream_dependence(self, action: 'Action'):
        """ add a new action in the downstream_dependence list

        Args:
            action (Action): new action
        """
        self.__downstream_dependences.append(action)

    def __repr__(self) -> str:
        """ overload the __repr__ function
        Returns:
            str: human readeable representation of Action
        """
        return self.__description
