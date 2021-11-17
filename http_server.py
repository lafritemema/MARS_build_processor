from typing import Dict
from enum import Enum
import json
import sys

import pathlib
# flask imports for server implementation
from flask import Flask, request, jsonify, logging

# pymongo imports for mongodb utilisation
from pymongo import MongoClient
from pymongo.collection import Collection, Cursor
from pymongo.database import Database
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure

# config import for configuration
from config import Config, KeyNotFoundError as KeyConfigError

# fastjsonschema import for json schema validation
import fastjsonschema

from mars.action import Action
from mars.actiontreelib import ActionTree, ActionNode

# get the application absolute path
file_folder = pathlib.Path(__file__).parent.absolute()
# get the validation schemas file path
valschemas_file_path = str(file_folder)+'/validation_schema.json'
# get the application config file path
config_file_path = str(file_folder)+'/server.cfg'


class ActionType(Enum):
    station = 'MOVE.STATION.WORK'
    approach = 'MOVE.ARM.APPROACH'
    work = 'MOVE.ARM.WORK'

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# instanciate flask server
server = Flask(__name__)

# try to read configuration
try:
    print(bcolors.WARNING + "test de plus")
    # read the validation schema from json file
    with open(valschemas_file_path, 'r') as schfile:
        schstr = schfile.read()
        validation_schema = json.loads(schstr)
    # read the server configuration from configuration files
    server_config = Config(config_file_path)

    mongo_host = server_config['mongodb.host']
    mongo_port = server_config['mongodb.port']
    mongo_db = server_config['mongodb.database']
    mongo_collection = server_config['mongodb.collection']
    server_port = server_config['server.port']
    server_host = server_config['server.host']
except FileNotFoundError as error:
    if error.filename == valschemas_file_path:
        print("validation schema error")
    elif error.filename == config_file_path:
        print("configuration error")
    sys.exit(1)
except KeyConfigError as error:
    print("One or several keys are missing in configuration file.")
    print(error.args[0])
    sys.exit(1)

try:
    print("Connection to mongodb server ...")
    # instanciate the mongodb client
    mongoClient: MongoClient = MongoClient(
        mongo_host,
        mongo_port,
        serverSelectionTimeoutMS=10)

    # get the mongodb version to check the connection
    mongo_version = mongoClient.server_info()['version']

    # get the mongodb collection
    carrier: Collection = mongoClient\
    
    if mongo_db in mongoClient.list_database_names():
        mars: Database = mongoClient.get_database(mongo_db)
        if mongo_collection in mars.list_collection_names():
            carrier: Collection = mars.get_collection(mongo_collection)
        else:
            raise KeyError({"target": 'collection', "key": mongo_collection})
    else:
        raise KeyError({"target": 'database', "key": mongo_db})

    print()
except ServerSelectionTimeoutError:
    print('MongoDB error : no mongo server listening on url {host}:{port}'.format(host=mongo_host, port=mongo_port))
    sys.exit(1)
except KeyError as mongoerror:
    keyargs = mongoerror.args[0]
    print("MongoDB error : {target} with name {key} not exists".format(target=keyargs['target'], key=keyargs['key']))
    sys.exit(1)


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
    server.logger.info('test logger info')
    # get the request body
    body = request.get_json()

    # check if the body is in accordance with the schema
    # if not raise a ValidationError
    validate = fastjsonschema.compile(validation_schema)
    validate(body)

    pipeline = build_aggregation_pipeline(body)

    cursor: Cursor = carrier.aggregate(pipeline)

    process_tree = build_process_tree(cursor)
    sequence = process_tree.get_sequence()
    tree = generate_desc(sequence)

    return jsonify(status='SUCCESS', sequence=sequence, tree=tree), 200


@server.route('/', methods=['GET'])
def baseHandler():
    data = request.get_json()
    print(data)
    return "ok"


def generate_desc(sequence:list):
    # suppression du la premier et dernier element (home)
    final_sequence = []
    seq = sequence[1:-1]
    load_tool_filter = filter(lambda a: a['type'] == 'MOVE.STATION.TOOL', seq)

    if len(list(load_tool_filter)) > 0:
        gen = sequence_gen(seq[1:])

        for extract_seq in gen:
            desc = [{"id": action['id'], "description": action["description"]} for action in extract_seq]
            final_sequence.append(desc)

        return final_sequence
    else:
        return seq

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

    prev_node_actype = None
    prev_loadtool_node_id = None

    # iteration to insert go load tool position action
    for lul_node in load_unload_nodes:
        # get the targeted node
        # tnode = process_tree.get_node(lul_node.identifier)
        if lul_node.action_type == 'LOAD.EFFECTOR':
            if prev_node_actype:
                if not prev_node_actype == 'UNLOAD.EFFECTOR':
                    load_tool_id = insert_load_pos_action(process_tree, lul_node.identifier, go_load_tool_pos)
                    prev_loadtool_node_id = load_tool_id
                else:
                    process_tree.move_node(lul_node.identifier, prev_loadtool_node_id)
            else:
                load_tool_id = insert_load_pos_action(process_tree, lul_node.identifier, go_load_tool_pos)
                prev_loadtool_node_id = load_tool_id
        else:
            load_tool_id = insert_load_pos_action(process_tree, lul_node.identifier, go_load_tool_pos)
            prev_loadtool_node_id = load_tool_id
        
        prev_node_actype = lul_node.action_type


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

    process_tree.show(key=lambda node: node.sort_key if node.sort_key else 9999)
    return process_tree

def insert_load_pos_action(tree: ActionTree, target_action_id: int, go_tool_pos: Action)-> int:
    node = tree.get_node(target_action_id)
    node_parent = tree.parent(target_action_id)
    # create the go to load tool position action as a global action
    load_tool_node = ActionNode(go_tool_pos, is_global=True)
    # insert the node in the tree as a tnode_parent children
    tree.add_action_node(load_tool_node, parent=node_parent)
    # move the targeted node as a go load tool children
    tree.move_node(target_action_id, load_tool_node.identifier)
    return load_tool_node.identifier


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
    area = reqbody.get('area')
    side = reqbody.get('side')
    position = reqbody.get('position')

    if id:
        match["product_reference.id"] = {'$in': id}

    if reference:
        match["product_reference.reference"] = {'$in': reference}

    if location:
        match["product_reference.parent.designation"] = location['element']
        match["product_reference.parent.id"] = {"$in": location['id']}
    
    if area:
        match["targeted_area.area"] = {"$in": area}
    
    if side:
        match["targeted_area.side"] = {"$in": side}
    
    if position:
        match["targeted_area.position"] = {"$in": position}

    print(match)
    match_operation = {
        "$match": {'$or': [
                    match, {
                    '_id': {
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

def sequence_gen(sequence):
    li = 0
    seq_list = sequence

    while(li < len(sequence)):
        for index, val in enumerate(seq_list):
            li += 1
            if val['type'] == 'MOVE.STATION.TOOL':
                yield seq_list[:index]
                seq_list = seq_list[index+1:]
                break
    yield seq_list


if __name__ == '__main__':
    server.run(host=server_host, port=server_port)