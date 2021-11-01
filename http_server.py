from typing import Dict
from enum import Enum
import json

import pathlib
# flask imports for server implementation
from flask import Flask, request, jsonify

# pymongo imports for mongodb utilisation
from pymongo import MongoClient
from pymongo.collection import Collection, Cursor
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure

# config import for configuration
from config import Config

# fastjsonschema import for json schema validation
import fastjsonschema

from mars.action import Action
from mars.actiontreelib import ActionTree, ActionNode

file_folder = pathlib.Path(__file__).parent.absolute()
print(file_folder)


class ActionType(Enum):
    station = 'MOVE.STATION.WORK'
    approach = 'MOVE.ARM.APPROACH'
    work = 'MOVE.ARM.WORK'


# try:
    # validation schema
with open(str(file_folder)+'/validation_schema.json', 'r') as schfile:
    schstr = schfile.read()
    validation_schema = json.loads(schstr)
# except:
    # print("error on schema validation loading")
    # sys.exit(1)


# get the server configuration
server_config = Config(str(file_folder) + '/server.cfg')

# instanciate flask server
server = Flask(__name__)
# instanciate mongoclient get host and port from config
mongoClient: MongoClient = MongoClient(
    server_config['mongodb.host'],
    server_config['mongodb.port'])

# get the wanted collection
carrier: Collection = mongoClient\
    .get_database(server_config['mongodb.database'])\
    .get_collection('carrier')


# ressource not found error handling
@server.errorhandler(404)
def errorHandler(error):
    return jsonify(status='FAIL', error=str(error)), 404


@server.errorhandler(400)
def badRequestErrorHandler(error):
    return jsonify(status='FAIL', error=str(error)), 400


# jsonschema error handling
@server.errorhandler(fastjsonschema.JsonSchemaException)
def processingErrorHandler(error):
    return jsonify(status='FAIL', error=str(error)), 407


# mongodb error handling
# ENHANCE: enhance mongodb error handling
@server.errorhandler(ServerSelectionTimeoutError)
@server.errorhandler(OperationFailure)
def mongodbErrorHandler(error: Exception):
    return jsonify(status='FAIL', error=str(error))


# sequence/move ressource handler
@server.route("/sequence/move", methods=['GET'])
def seqMoveHandler():
    # get the request body
    body = request.get_json()

    # check if the body is in accordance with the schema
    # if not raise a ValidationError
    validate = fastjsonschema.compile(validation_schema)
    validate(body)

    pipeline = build_aggregation_pipeline(body)

    cursor: Cursor = carrier.aggregate(pipeline)

    process_tree = build_process_tree(cursor)

    sequence, tree = process_tree.get_sequence()
    return jsonify(status='SUCCESS', sequence=sequence, tree=tree), 200


@server.route('/', methods=['GET'])
def baseHandler():
    data = request.get_json()
    print(data)
    return "ok"


def build_process_tree(cursor: Cursor):
    # extract dependences from cursor
    root_actions, dependences, global_actions = extract_actions(cursor)
    actions = [Action.parse(ra, dependences) for ra in root_actions]
    # actions = Action.parseList(rootActions, dependences)

    process_tree = ActionTree()
    for a in actions:
        process_tree.add_branch_for_action(a)

    print("action tree generated")

    # create and insert global actions
    # create global actions
    go_load_tool_pos = Action.parse(global_actions['load_tool_position'], dependences)
    go_home = Action.parse(global_actions['home'], dependences)

    # insert go load tool position action before load and unload actions
    # list of targeted actions
    lul_action_types = ['LOAD.EFFECTOR', 'UNLOAD.EFFECTOR']
    # filter the tree to localize the actions => return a filter generator
    load_unload_nodes = process_tree.filter_nodes(lambda node: node.action_type in lul_action_types)
    # transform the filter to list
    load_unload_nodes = list(load_unload_nodes)

    # iteration to insert go load tool position action
    for lul_node in load_unload_nodes:
        # get the targeted node
        tnode = process_tree.get_node(lul_node.identifier)
        # get its parent
        tnode_parent = process_tree.parent(lul_node.identifier)
        # create the go to load tool position action as a global action
        load_tool_node = ActionNode(go_load_tool_pos, is_global=True)
        # insert the node in the tree as a tnode_parent children
        process_tree.add_action_node(load_tool_node, parent=tnode_parent)
        #move the targeted node as a go load tool children
        process_tree.move_node(tnode.identifier, load_tool_node.identifier)

    # insert a go home and return home node
    # get the root node
    root_node = process_tree.get_node(0)
    # get the root node children
    root_node_children = process_tree.children(0)
    # create a go home and return home action node
    go_home_node = ActionNode(go_home, is_global=True)
    return_home_node = ActionNode(go_home, is_global=True)

    # insert the go home node in root
    process_tree.add_action_node(go_home_node, parent=root_node)

    # move all the root children in go_home node
    for ch in root_node_children:
        process_tree.move_node(ch.identifier, go_home_node.identifier)

    # insert the return home node in root
    process_tree.add_action_node(return_home_node, parent=root_node)

    process_tree.show(key=lambda node : node.sort_key if node.sort_key else 9999)
    return process_tree


def extract_actions(cmdCursor: Cursor):

    global_ids = ['home', 'load_tool_position']

    dependences = {}
    global_actions = {}
    root_actions = []
    for doc in cmdCursor:
        if doc['_id'] in global_ids:
            global_actions[doc['_id']] = doc
        else:
            if 'graphLookUp' in doc:
                for dep in doc['graphLookUp']:
                    if not dep['_id'] in dependences:
                        dependences[str(dep['_id'])] = dep
            del doc['graphLookUp']
            root_actions.append(doc)

    return root_actions, dependences, global_actions


def build_aggregation_pipeline(reqbody: Dict):

    match = {
        "type": ActionType[reqbody['actionType']].value,
        'product_reference.designation': reqbody['element']
    }

    id = reqbody.get('id')
    reference = reqbody.get('reference')
    location = reqbody.get('location')

    if id:
        match["product_reference.id"] = {'$in': id}
    if reference:
        match["product_reference.reference"] = {'$in': reference}
    if location:
        match["product_reference.parent.designation"] = location['element']
        match["product_reference.parent.id"] = {"$in": location['id']}

    match_operation = {
        "$match": {'$or': [
                match, {
                    '_id':{
                        '$in': ['home', 'load_tool_position']
                    }
                }
            ]
        }
    }

    graphlookup_operation = {
        "$graphLookup": {
            "from": "carrier",
            "startWith": "$dependences.action",
            "connectFromField": "dependences.action",
            "connectToField": "_id",
            "as": "graphLookUp"
        }
    }

    
    return [match_operation, graphlookup_operation]
