from typing import Dict
from enum import Enum
import json
import sys
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
from mars.actiontreelib import ActionTree

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

    sequence = process_tree.get_sequence()
    tree = process_tree.to_json()

    return jsonify(status='SUCCESS', sequence=sequence, tree=tree), 200


@server.route('/', methods=['GET'])
def baseHandler():
    data = request.get_json()
    print(data)
    return "ok"


def build_process_tree(cursor: Cursor):
    rootActions, dependences = extract_dependences(cursor)
    actions = Action.parseList(rootActions, dependences)
    process_tree = ActionTree()
    for a in actions:
        process_tree.add_branch_for_action(a)

    print("action tree generated")
    process_tree.show(key=lambda node : node.sort_key if node.sort_key else 9999)
    return process_tree


def extract_dependences(cmdCursor: Cursor):
    allDependences = {}
    rootActions = []
    for doc in cmdCursor:
        if 'dependences' in doc:
            for dep in doc['dependences']:
                if not dep['_id'] in allDependences:
                    allDependences[str(dep['_id'])] = dep

        del doc['dependences']
        rootActions.append(doc)

    return rootActions, allDependences


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
        "$match": match
    }

    graphlookup_operation = {
        "$graphLookup": {
            "from": "carrier",
            "startWith": "$upstream_dependences",
            "connectFromField": "upstream_dependences",
            "connectToField": "_id",
            "as": "upstreamOperations"
        }
    }

    direct_lookup_operation = {
        "$lookup": {
            "from": "carrier",
            "localField": "downstream_dependences",
            "foreignField": "_id",
            "as": "directDownstreamOperations"
        }
    }

    lookup_operation = {
        "$lookup": {
            "from": "carrier",
            "localField": "upstreamOperations.downstream_dependences",
            "foreignField": "_id",
            "as": "downstreamOperations"
        }
    }

    concat_reverse = {
        "$set": {
            "dependences": {
                "$concatArrays": [
                    "$downstreamOperations",
                    "$directDownstreamOperations",
                    "$upstreamOperations"]
            }
        }
    }

    unset_operation = {
         "$unset": [
            "downstreamOperations",
            "directDownstreamOperations",
            "upstreamOperations"]
    }

    return [match_operation,
            graphlookup_operation,
            direct_lookup_operation,
            lookup_operation,
            concat_reverse,
            unset_operation]
