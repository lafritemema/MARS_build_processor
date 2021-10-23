
from mars.action import Action
from treelib import Tree, Node
from typing import List


class Dependencies:

    @staticmethod
    def listDependences(action):
        alist = Dependencies.__listDependences(action, action.priority)
        alist.sort(key=lambda item: item[0])
        return [a[1] for a in alist]
        # return alist

    @staticmethod
    def __listDependences(action, dn=0):
        alist = [(dn, action)]
        for a in action.upstream_dependences:
            alist.extend(Dependencies.__listDependences(a, a.priority))
        for a in action.downstream_dependences:
            alist.extend(Dependencies.__listDependences(a, 9999-a.priority))
        return alist


class ActionNode(Node):
    """ class used to represent a tree node containing an Action as data
        it inherit from treelib.Node class

    Attributes
    ----------
    priority : int
        the action priority

    """
    def __init__(self, action: Action = None) -> 'ActionNode':
        """ActionNode initializer

        Args:
            action (Action, optional): The action represented
            by the node in the tree. Defaults to None.
        """

        ''' usage of treelib.Node.__init__() with
            the action.description as Node name attribute
            action.id as Node id attribute
            and the action object as data

            if no action, 'root' as name and 0 as id.
        '''

        super(ActionNode, self)\
            .__init__(action.description if action else 'root',
                      action.id if action else 0,
                      data=action)

    def __lt__(self, node: 'ActionNode') -> bool:

        """ operator < function. compare the Action priority

        Args:
            node (ActionNode): the node to compare with

        Returns:
            bool: true if action priority is lower than the other one
        """

        return True if self.priority > node.priority else False

    def __gt__(self, node: 'ActionNode'):

        """ operator > function. compare the action priority

        Args:
            node (ActionNode): the node to compare with

        Returns:
            bool: true if action priority is upper than the other one
        """

        return True if self.priority < node.priority else False

    def __eq__(self, node):
        """ operator = function. compare the Action priority

        Args:
            node (ActionNode): the node to compare with

        Returns:
            bool: true if action priority is equal than the other one
        """
        return True if self.priority == node.priority else False

    @property
    def sort_key(self):
        return self.data.work_order

    @property
    def priority(self) -> int:
        """ get the action priority

        Returns:
            int: the action priority
        """

        if self.data:
            return self.data.priority
        else:
            return 0


class ActionTree(Tree):
    """ class used to represent a tree containing ActionNode.
        it inherit form treelib.Tree class
    """

    def __init__(self):
        """ActionTree initializer
        """
        # usage of treelib.Tree.__init__ to initialize Tree
        super(ActionTree, self).__init__()
        # add a root ActionNode in the tree
        self.add_node(ActionNode())

    def __add_action_node(self, action_node: ActionNode, parent: ActionNode):
        """ add an ActionNode in the tree if not allready exist
        (id already present)

        Args:
            action_node (ActionNode): the ActionNode to add
            parent (ActionNode): the ActionNode parent
        """

        # if the ActionNode not alread in the tree, add the ActionNode
        if not self.contains(action_node.identifier):
            self.add_node(action_node, parent=parent)

    def __add_action_nodes(self, actions: List[ActionNode]):
        """ add list of actions

        Args:
            actions (List[ActionNode]): [description]
        """

        current = self.get_node(0)
        action_nodes = [ActionNode(an) for an in actions]

        for an in action_nodes:
            parent = self.__getParent(an, current)
            self.__add_action_node(an, parent)
            current = an

    def __getParent(self, actual_node: ActionNode, previous_node: ActionNode):

        if actual_node == previous_node:
            parent = self.parent(previous_node.identifier)

        elif actual_node < previous_node:
            parent = previous_node

        else:
            parent = self.__getParent(actual_node,
                                      self.parent(previous_node.identifier))

        return parent

    def add_branch_for_action(self, branch_end: Action):
        dl = Dependencies.listDependences(branch_end)
        self.__add_action_nodes(dl)

    def get_sequence(self, ):
        expanded = self.expand_tree(key=lambda node : node.sort_key if node.sort_key else 9999)
        sequence = [self.get_node(nid).data for nid in expanded]
        sequence.remove(None)
        sequence = [d.get_sequence() for d in sequence]
        return sequence
