from ariadne import QueryType, MutationType, ObjectType, EnumType, gql, make_executable_schema
from ariadne.asgi import GraphQL
import uvicorn
from enum import Enum
from math import sqrt
import uuid
from notions import NotionFrame, NotionType, NotionUnit, NotionValue, PerceptiveFrame, PerceptiveFrameInstance
import notions_legal
from notions_topology import ConfigurationManagementRelationClass, ConfigurationManagementNodeClass, init as notion_topology_init, query_arcs


#######################################
# GraphQL schema
#######################################

type_defs = gql(
    '''
    input Arg {
        key: String!
        value: String!
    }
    
    type Query {
        "Get all notion frames"
        notionFrames: [NotionFrame!]!
        "Get notion frame by id"
        notionFrame(id: ID!): NotionFrame
        "Get all perceptive frames"
        perceptiveFrames: [PerceptiveFrame!]!
        "Get perceptive frame by id"
        perceptiveFrame(id: ID!): PerceptiveFrame
        "Get all perceptive frame instances"
        perceptiveFrameInstances: [PerceptiveFrameInstance!]!
        "Get perceptive frame instances by id"
        perceptiveFrameInstance(id: ID!): PerceptiveFrameInstance
        "Get all arcs or all arcs with node id = nodeId"
        arcs(nodeId: ID): [PerceptiveFrameInstance!]!
    }

    type Mutation {
        "Create notion frame"
        createNotionFrame(id: ID!, parameter: String!, type: NotionType, unit: NotionUnit, derivedFrom: [ID!], converter: String, discriminator: String): NotionFrame
        "Create notion value"
        createNotionValue(notionValueInput: NotionValueInput, derivedFrom: [NotionValueInput!]): NotionValue
        "Create perceptive frame"
        createPerceptiveFrame(id: ID!, notionFrameIds: [ID!]!, discriminator: String): PerceptiveFrame
        "Create perceptive frame instance"
        createPerceptiveFrameInstance(perceptiveFrameInstanceInput: PerceptiveFrameInstanceInput!): PerceptiveFrameInstance
        "Create configuration management relation"
        createConfigMngRelation(id: ID, relationType: ConfigMngRelationType!, departureId: ID!, arrivalId: ID!): PerceptiveFrameInstance
        "Create 0D Node"
        createNode(id: ID!, downPortCount: Int, upPortCount: Int): [PerceptiveFrameInstance!]!
        "Create window frame"
        createWindowFrame(width: Int!, height: Int!): [PerceptiveFrameInstance!]!
    }
    
    """
    A description of how an observer evaluates sensory stimuli or measurements.
    """
    type NotionFrame {
        id: ID!
        parameter: String!
        type: NotionType
        unit: NotionUnit
        derivedFrom: [NotionFrame!]
        converter: String
        discriminator: String
    }

    """
    The value of a Notion, expressed in a Notion-Frame.
    """
    type NotionValue {
        id: ID!
        frame: NotionFrame
        derivedFrom: [NotionValue!]
        property: String
        classification: String
    }

    input NotionValueInput {
        notionFrameId: ID!
        derivedFrom: [NotionValueInput!]
        args: [Arg!]!
    }

    """
    A set of Notion Frames used by an actor to express knowledge. 
    """
    type PerceptiveFrame {
        id: ID!
        notionFrames: [NotionFrame!]!
        discriminator: String
    }

    type PerceptiveFrameInstance {
        id: ID!
        perceptiveFrame: PerceptiveFrame
        notionValues: [NotionValue!]!
        classification: String
    }

    input PerceptiveFrameInstanceInput {
        id: ID!
        perceptiveFrameId: ID
        notionValueInputs: [NotionValueInput!]!
    }
    
    enum NotionType {
        NONE
        BOOLEAN
        DATE
        DURATION
        ENUMERATION
        FLOAT
        INTEGER
        IRI
        STRING
    }
                
    enum NotionUnit {
        NONE
        DAY
        WEEK
        MONTH
        YEAR
    }

    enum ConfigMngRelationType {
        CONNECTION_CONNECTION_SELECTION
        CONNECTION_NODE_ENCLOSURE
        NODE_NODE_CONNECTION
        NODE_NODE_ENCLOSURE
        NODE_PORT_BOUNDARY
        PORT_PORT_CONNECTION
        PORT_PORT_SELECTION
        SLOT_MODULE_SELECTION
    }
    '''
)

query = QueryType()
mutation = MutationType()
perceptive_frame = ObjectType("PerceptiveFrame")
perceptive_frame_instance = ObjectType("PerceptiveFrameInstance")
notion_frame = ObjectType("NotionFrame")
notion_value = ObjectType("NotionValue")
notion_type = EnumType(
    "NotionType",
    {
        "NONE": "NONE",
        "BOOLEAN": "BOOLEAN",
        "DATE": "DATE",
        "DURATION": "DURATION",
        "ENUMERATION": "ENUMERATION",
        "FLOAT": "FLOAT",
        "INTEGER": "INTEGER",
        "IRI": "IRI",
        "STRING": "STRING"
    }
)
notion_unit = EnumType(
    "NotionUnit",
    {
        "NONE": "NONE",
        "DAY": "DAY",
        "WEEK": "WEEK",
        "MONTH": "MONTH",
        "YEAR": "YEAR"
    }
)
config_mng_relation_type = EnumType (
    "ConfigMngRelationType",
    {
        "CONNECTION_CONNECTION_SELECTION" : 0,
        "CONNECTION_NODE_ENCLOSURE": 1,
        "NODE_NODE_CONNECTION": 2,
        "NODE_NODE_ENCLOSURE": 3,
        "NODE_PORT_BOUNDARY": 4,
        "PORT_PORT_CONNECTION": 5,
        "PORT_PORT_SELECTION": 6,
        "SLOT_MODULE_SELECTION": 7
    }
)

#######################################
# Queries
#######################################

@query.field("notionFrames")
def resolve_query_notion_frames(*_) -> list[NotionFrame]:
    return NotionFrame.get_all_notion_frames()

@query.field("notionFrame")
def resolve_query_notion_frame(*_, id: str) -> NotionFrame:
    return NotionFrame.get_notion_frame(id)

@query.field("perceptiveFrames")
def resolve_query_perceptive_frames(*_) -> list[PerceptiveFrame]:
    return PerceptiveFrame.get_all_perceptive_frames()

@query.field("perceptiveFrame")
def resolve_query_perceptive_frame(*_, id: str) -> PerceptiveFrame:
    return PerceptiveFrame.get_perceptive_frame(id)

@query.field("perceptiveFrameInstances")
def resolve_query_perceptive_frame_instances(*_) -> list[PerceptiveFrameInstance]:
    return [nv for nv in PerceptiveFrameInstance.values.values()]

@query.field("perceptiveFrameInstance")
def resolve_query_perceptive_frame_instance(*_, id: str) -> PerceptiveFrameInstance:
    return PerceptiveFrameInstance.get_perceptive_frame_instance(id)

@query.field("arcs")
def resolve_query_arcs(*_, nodeId: str = None) -> list[PerceptiveFrameInstance]:
    return query_arcs(nodeId)

@notion_frame.field("id")
def resolve_notion_frame_name(obj: NotionFrame, *_) -> str:
    return obj.id

@notion_frame.field("parameter")
def resolve_notion_frame_name(obj: NotionFrame, *_) -> str:
    return obj.parameter

@notion_frame.field("type")
def resolve_notion_frame_type(obj: NotionFrame, *_) -> NotionType:
    if isinstance(obj.unit, Enum):
        return obj.type.name
    else:    
        return obj.type

@notion_frame.field("unit")
def resolve_notion_frame_unit(obj: NotionFrame, *_) -> NotionUnit:
    if isinstance(obj.unit, Enum):
        return obj.unit.name
    else:
        return obj.unit

@notion_frame.field("derivedFrom")
def resolve_notion_frame_derived_from(obj: NotionFrame, *_) -> NotionFrame:
    return obj.derived_from.values()

@notion_frame.field("converter")
def resolve_notion_frame_converter(obj: NotionFrame, *_) -> str:
    return obj.converter_code

@notion_frame.field("discriminator")
def resolve_notion_frame_discriminator(obj: NotionFrame, *_) -> str:
    return obj.discriminator_code


@notion_value.field("derivedFrom")
def resolve_notion_value_derived_from(obj: NotionValue, *_) -> list[NotionValue]:
    return obj.get_derived_notion_values()

@notion_value.field("classification")
def resolve_notion_value_classification(obj: NotionValue, *_) -> str:
    classification = obj.classification
    if isinstance(classification, Enum):
        return classification.name
    else:
        return obj.classification

@notion_value.field("property")
def resolve_notion_value_property(obj: NotionValue, *_) -> str:
    if obj.property:
        property = obj.property[obj.frame.parameter]
        if isinstance(property, Enum):
            return property.name
        elif isinstance(property, list):
            return str(property)
        else:
            return property
    return None


@perceptive_frame.field("id")
def resolve_perceptive_frame_name(obj: PerceptiveFrame, *_) -> str:
    return obj.id

@perceptive_frame.field("notionFrames")
def resolve_perceptive_frame_notion_frames(obj: PerceptiveFrame, *_) -> list[NotionFrame]:
    return [nv for nv in obj.notion_frames.values()]

@perceptive_frame.field("discriminator")
def resolve_perceptive_frame_discriminator(obj: PerceptiveFrame, *_) -> str:
    return obj.discriminator_code


@perceptive_frame_instance.field("id")
def resolve_perceptive_frame_instance_id(obj: PerceptiveFrameInstance, *_) -> str:
    return obj.id

@perceptive_frame_instance.field("perceptiveFrame")
def resolve_perceptive_frame_instance_perceptive_frame(obj: PerceptiveFrameInstance, *_) -> PerceptiveFrame: 
    return obj.perceptive_frame

@perceptive_frame_instance.field("notionValues")
def resolve_perceptive_frame_notion_values(obj: PerceptiveFrameInstance, *_) -> list[NotionValue]: 
    return obj.notion_values

@perceptive_frame_instance.field("classification")
def resolve_perceptive_frame_instance_classification(obj: PerceptiveFrameInstance, *_):
    id = obj.id
    perceptive_frame = obj.perceptive_frame.id
    notion_values = obj.notion_values
    keys = [key.frame.id for key in notion_values]
    values = [nv.frame for nv in notion_values]
    notion_frames = {key: value for key, value in zip(keys, values)}
    tmp = dict()
    if len(notion_values) > len(notion_frames):
        for nv in notion_values:
            if tmp.get(nv.frame.id):
                tmp.get(nv.frame.id).append(nv)
            else:
                tmp[nv.frame.id] = [nv]
    else:
        for nv in notion_values:
                tmp[nv.frame.id] = nv
    notion_values = tmp
    if perceptive_frame == "PF_Config_Mng_Node":
        discr = obj.perceptive_frame.discriminator(notion_frames, notion_values, id)
        if discr:
            return obj.perceptive_frame.discriminator(notion_frames, notion_values, id).name
        else:
            return None
    else:
        discr = obj.perceptive_frame.discriminator(notion_frames, notion_values)
        if discr:
            return obj.perceptive_frame.discriminator(notion_frames, notion_values).name
        else:
            return None


#######################################
# Mutations
#######################################

@mutation.field("createNotionFrame")
def resolve_mutation_create_notion_frame(*_, id: str, parameter: str, type: NotionType = None, unit: NotionUnit = None,
        derivedFrom: list[str] = None, converter: str = None, discriminator: str = None) -> NotionFrame:
    if not derivedFrom:
        derivedFrom = []

    if not converter:
        converter = """def converter_function(args):\n    return None"""
    d = {}
    exec(converter, d, d)
    converter_function = d[list(d)[-1]]
    
    if not discriminator:
        discriminator = """def discriminator_function(args):\n    return None"""
    exec(discriminator, d, d)
    discriminator_function = d[list(d)[-1]]
    
    return NotionFrame(id = id, parameter = parameter, type = type, unit = unit, 
                       derived_from = derivedFrom,
                       converter_code = converter, converter = converter_function, 
                       discriminator_code = discriminator, discriminator = discriminator_function)

@mutation.field("createNotionValue")
def resolve_mutation_create_notion_value(*_, notionValueInput: dict, derivedFrom: list[dict] = []) -> NotionValue:
    nf: NotionFrame = NotionFrame.get_notion_frame(notionValueInput["notionFrameId"])
    args = notionValueInput["args"]

    arg_keys = [arg['key'] for arg in args]
    arg_values = [arg['value'] for arg in args]        
    arg_dict = {key: value for key, value in zip(arg_keys, arg_values)}
    for key in arg_dict.keys():
        if NotionFrame.get_notion_frame(key):
            arg_dict[key] = NotionValue.get_notion_value(arg_dict[key])
    arg_dict[nf.id] = nf

    if derivedFrom:
        for item in derivedFrom:
            if not "derivedFrom" in item:
                item["derivedFrom"] = []
        keys = [item["notionFrameId"] for item in derivedFrom]
        values = [resolve_mutation_create_notion_value(notionValueInput={"notionFrameId": item["notionFrameId"],"args": item["args"]}, derivedFrom=item["derivedFrom"]) for item in derivedFrom]
        derived = {key: value for key, value in zip(keys, values)}
        if len(derived) < len(values):
            derived = {keys[0]: values}
        args = arg_dict | derived
    else:
        args = arg_dict

    return NotionValue(frame = nf, args = args)

@mutation.field("createPerceptiveFrame")
def resolve_mutation_create_perceptive_frame(*_, id: str, notionFrameIds: list[str], discriminator: str = None) -> PerceptiveFrame:
    if not discriminator:
        discriminator = """def discriminator_function(notion_frames, notion_values):\n    return None"""
    d = {}
    exec(discriminator, d, d)
    discriminator_function = d[list(d)[-1]]
    return PerceptiveFrame(id = id, notion_frame_names = notionFrameIds, discriminator_code = discriminator, discriminator = discriminator_function)

@mutation.field("createPerceptiveFrameInstance")
def resolve_mutation_create_perceptive_frame_instance(*_, perceptiveFrameInstanceInput: list[dict]) -> PerceptiveFrameInstance:
    if "perceptiveFrameId" not in perceptiveFrameInstanceInput:
        perceptiveFrameInstanceInput["perceptiveFrameId"] = None
    for item in perceptiveFrameInstanceInput["notionValueInputs"]:
            if not "derivedFrom" in item:
                item["derivedFrom"] = []
    nvs: list[NotionValue] = []
    for nvi in perceptiveFrameInstanceInput["notionValueInputs"]:
        nvs.append(resolve_mutation_create_notion_value(notionValueInput=nvi, derivedFrom=nvi["derivedFrom"]))
    return PerceptiveFrameInstance(id = perceptiveFrameInstanceInput["id"], perceptiveFrameId = perceptiveFrameInstanceInput["perceptiveFrameId"], notion_values = nvs)

@mutation.field("createConfigMngRelation")
def resolve_create_config_mng_relation(*_, id: str = None, relationType: ConfigurationManagementRelationClass, departureId: str, arrivalId: str) -> PerceptiveFrameInstance:
    if not id:
        id = f"{uuid.uuid4()}"

    match relationType:
        case ConfigurationManagementRelationClass.CONNECTION_CONNECTION_SELECTION.name:
            pass
        case ConfigurationManagementRelationClass.CONNECTION_NODE_ENCLOSURE.name:
            departure_enclosure = resolve_mutation_create_notion_value(
                notionValueInput = {
                    "notionFrameId": "NF_Enclosure",
                    "args": [
                        {"key": "enclosure", "value": "IS_ENCLOSED_BY"}
                    ]},
                derivedFrom = [{
                    "notionFrameId":  "NF_Orientation",
                    "args": [{
                        "key": "orientation", "value": "DEPARTURE"}],
                    "derivedFrom": [{
                        "notionFrameId":  "NF_Link", 
                        "args": [{
                            "key": "link", "value": f"{departureId}"}]
                    }]}])
            arrival_enclosure = resolve_mutation_create_notion_value(
                notionValueInput = {
                    "notionFrameId": "NF_Enclosure",
                    "args": [
                        {"key": "enclosure", "value": "ENCLOSES"}
                    ]},
                derivedFrom = [ {
                    "notionFrameId":  "NF_Orientation",
                    "args": [{
                        "key": "orientation", "value": "ARRIVAL"}],
                    "derivedFrom": [{
                        "notionFrameId":  "NF_Link", 
                        "args": [{
                            "key": "link", "value": f"{arrivalId}"}]
                    }]}])
            return PerceptiveFrameInstance(id = id, perceptiveFrameId = "PF_Config_Mng_Relation", notion_values = [departure_enclosure, arrival_enclosure])
        case ConfigurationManagementRelationClass.NODE_NODE_CONNECTION.name:
            departure_connection = resolve_mutation_create_notion_value(
                notionValueInput = {
                    "notionFrameId": "NF_Connection",
                    "args": [
                        {"key": "connection", "value": "DOWN"}
                    ]},
                derivedFrom = [{
                    "notionFrameId":  "NF_Orientation",
                    "args": [{
                        "key": "orientation", "value": "DEPARTURE"}],
                    "derivedFrom": [{
                        "notionFrameId":  "NF_Link", 
                        "args": [{
                            "key": "link", "value": f"{departureId}"}]
                    }]}])
            arrival_connection = resolve_mutation_create_notion_value(
                notionValueInput = {
                    "notionFrameId": "NF_Connection",
                    "args": [
                        {"key": "connection", "value": "UP"}
                    ]},
                derivedFrom = [ {
                    "notionFrameId":  "NF_Orientation",
                    "args": [{
                        "key": "orientation", "value": "ARRIVAL"}],
                    "derivedFrom": [{
                        "notionFrameId":  "NF_Link", 
                        "args": [{
                            "key": "link", "value": f"{arrivalId}"}]
                    }]}])
            return PerceptiveFrameInstance(id = id, perceptiveFrameId = "PF_Config_Mng_Relation", notion_values = [departure_connection, arrival_connection])
        case ConfigurationManagementRelationClass.PORT_PORT_CONNECTION.name:
            departure_connection = resolve_mutation_create_notion_value(
                notionValueInput = {
                    "notionFrameId": "NF_Connection",
                    "args": [
                        {"key": "connection", "value": "DOWN"}
                    ]},
                derivedFrom = [ {
                    "notionFrameId":  "NF_Orientation",
                    "args": [{
                        "key": "orientation", "value": "DEPARTURE"}],
                    "derivedFrom": [{
                        "notionFrameId":  "NF_Link", 
                        "args": [{
                            "key": "link", "value": f"{departureId}"}]
                    }]}])
            arrival_connection = resolve_mutation_create_notion_value(
                notionValueInput = {
                    "notionFrameId": "NF_Connection",
                    "args": [
                        {"key": "connection", "value": "UP"}
                    ]},
                derivedFrom = [ {
                    "notionFrameId":  "NF_Orientation",
                    "args": [{
                        "key": "orientation", "value": "ARRIVAL"}],
                    "derivedFrom": [{
                        "notionFrameId":  "NF_Link", 
                        "args": [{
                            "key": "link", "value": f"{arrivalId}"}]
                    }]}])
            return PerceptiveFrameInstance(id = id, perceptiveFrameId = "PF_Config_Mng_Relation", notion_values = [departure_connection, arrival_connection])
        case ConfigurationManagementRelationClass.PORT_PORT_SELECTION.name:
            pass
        case ConfigurationManagementRelationClass.NODE_NODE_ENCLOSURE.name:
            departure_enclosure = resolve_mutation_create_notion_value(
                notionValueInput = {
                    "notionFrameId": "NF_Enclosure",
                    "args": [
                        {"key": "enclosure", "value": "IS_ENCLOSED_BY"}
                    ]},
                derivedFrom = [{
                    "notionFrameId":  "NF_Orientation",
                    "args": [{
                        "key": "orientation", "value": "DEPARTURE"}],
                    "derivedFrom": [{
                        "notionFrameId":  "NF_Link", 
                        "args": [{
                            "key": "link", "value": f"{departureId}"}]
                    }]}])
            arrival_enclosure = resolve_mutation_create_notion_value(
                notionValueInput = {
                    "notionFrameId": "NF_Enclosure",
                    "args": [
                        {"key": "enclosure", "value": "ENCLOSES"}
                    ]},
                derivedFrom = [{
                    "notionFrameId":  "NF_Orientation",
                    "args": [{
                        "key": "orientation", "value": "ARRIVAL"}],
                    "derivedFrom": [{
                        "notionFrameId":  "NF_Link", 
                        "args": [{
                            "key": "link", "value": f"{arrivalId}"}]
                        }]}])
            return PerceptiveFrameInstance(id = id, perceptiveFrameId = "PF_Config_Mng_Relation", notion_values = [departure_enclosure, arrival_enclosure])
        case ConfigurationManagementRelationClass.NODE_PORT_BOUNDARY.name:
            departure__boundary = resolve_mutation_create_notion_value(
                notionValueInput = {
                    "notionFrameId": "NF_Boundary",
                    "args": [
                        {"key": "boundary", "value": "IS_BOUNDED_BY"}
                    ]},
                derivedFrom = [{
                    "notionFrameId":  "NF_Orientation",
                    "args": [{
                        "key": "orientation", "value": "DEPARTURE"}],
                    "derivedFrom": [{
                        "notionFrameId":  "NF_Link", 
                        "args": [{
                            "key": "link", "value": f"{departureId}"}]
                    }]}])
            arrival_boundary = resolve_mutation_create_notion_value(
                notionValueInput = {
                    "notionFrameId": "NF_Boundary",
                    "args": [
                        {"key": "boundary", "value": "BOUNDS"}
                    ]},
                derivedFrom = [{
                    "notionFrameId":  "NF_Orientation",
                    "args": [{
                        "key": "orientation", "value": "ARRIVAL"}],
                    "derivedFrom": [{
                        "notionFrameId":  "NF_Link", 
                        "args": [{
                            "key": "link", "value": f"{arrivalId}"}]
                    }]}])
            return PerceptiveFrameInstance(id = id, perceptiveFrameId = "PF_Config_Mng_Relation", notion_values = [departure__boundary, arrival_boundary])
        case ConfigurationManagementRelationClass.SLOT_MODULE_SELECTION.name:
            pass
    return None

@mutation.field("createNode")
def resolve_create_node(*_, id:str, downPortCount:int = 0, upPortCount:int = 0) -> list[PerceptiveFrameInstance]:
    pfis: list[PerceptiveFrameInstance] = []
    for dp in range(downPortCount):
        pfis.append(resolve_create_config_mng_relation(id=f"{uuid.uuid4()}", relationType=ConfigurationManagementRelationClass.NODE_PORT_BOUNDARY.name, departureId=id, arrivalId=id+f"_down{dp}"))
    for up in range(upPortCount):
        pfis.append(resolve_create_config_mng_relation(id=f"{uuid.uuid4()}", relationType=ConfigurationManagementRelationClass.NODE_PORT_BOUNDARY.name, departureId=id, arrivalId=id+f"_up{up}"))
    return pfis

@mutation.field("createWindowFrame")
def resolve_create_window_frame(*_, width: int, height: int) -> list[PerceptiveFrameInstance]:
    
    def get_port_other_side(this_port: str, arcs: list[PerceptiveFrameInstance]) -> str:
        for arc in arcs:
            for nv in arc.notion_values:
                if nv.frame.id == "NF_Connection":
                    port = nv.args.get("NF_Orientation").args.get("NF_Link").args.get("link")
                    if port != this_port:
                        return port
        return None
    
    def get_port_node(this_port: str, arcs: list[PerceptiveFrameInstance]) -> str:
        for arc in arcs:
            for nv in arc.notion_values:
                if nv.frame.id == "NF_Boundary":
                    port = nv.args.get("NF_Orientation").args.get("NF_Link").args.get("link")
                    if port != this_port:
                        return port
        return None       


    # Create "dimension" notion frame
    resolve_mutation_create_notion_frame(
        id="NF_Dimension", 
        parameter="dimension", 
        type=NotionType.INTEGER, 
        unit=NotionUnit.NONE,
        converter= """
def converter_function(args):
    return {"dimension": args['dimension']}
"""
        )

     # Create "coordinate" notion frame
    resolve_mutation_create_notion_frame(
        id="NF_Coordinate", 
        parameter="coordinate", 
        type=NotionType.INTEGER, 
        unit=NotionUnit.MM,
        converter= """
def converter_function(args):
    return {"coordinate": args['coordinate']}
"""
        )
       
    # Create "location" notion frame
    resolve_mutation_create_notion_frame(
        id="NF_Location", 
        parameter="location", 
        type=NotionType.INTEGER, 
        unit=NotionUnit.MM,
        derivedFrom=["NF_Coordinate"],
        converter= """
def converter_function(args):
    nfc = args['NF_Coordinate']
    return {"location": [int(nfc[0].args["coordinate"]), int(nfc[1].args["coordinate"]), int(nfc[2].args["coordinate"])]}
"""
        )
    
    # Create "length" notion frame
    resolve_mutation_create_notion_frame(
        id="NF_Length",
        parameter="length",
        type=NotionType.INTEGER,
        unit=NotionUnit.MM,
        derivedFrom=["NF_Location","NF_Coordinate"],
        converter= """
def converter_function(args):
    from math import sqrt

    loc0: list[float] = []
    loc1: list[float] = []
    for loc in args['NF_Location']:
        if len(loc0) == 0:
            loc0 = [float(c.args['coordinate']) for c in loc.args['NF_Coordinate']]
        else:
            loc1 = [float(c.args['coordinate']) for c in loc.args['NF_Coordinate']]

    length = sqrt((loc1[0] - loc0[0]) * (loc1[0] - loc0[0]) + (loc1[1] - loc0[1]) * (loc1[1] - loc0[1]) + (loc1[2] - loc0[2]) * (loc1[2] - loc0[2]))

    return {"length": length}
        """
    )

    # Create "shrink" notion frame
    resolve_mutation_create_notion_frame(
        id="NF_Shrink", 
        parameter="shrink", 
        type=NotionType.INTEGER, 
        unit=NotionUnit.MM,
        converter= """
def converter_function(args):
    return {"shrink": args['shrink']}
"""
        )
    
    # Create "cut" notion frame
    resolve_mutation_create_notion_frame(
        id="NF_Cut", 
        parameter="cut", 
        type=NotionType.INTEGER, 
        unit=NotionUnit.DEGREE,
        converter= """
def converter_function(args):
    return {"cut": args['cut']}
"""
        )
    
    pfis: list[PerceptiveFrameInstance] = []

    window_module = resolve_mutation_create_perceptive_frame_instance(
        perceptiveFrameInstanceInput={
            "id": f"fixed window({width}x{height})",
            "perceptiveFrameId": "PF_Config_Mng_Node",
            "notionValueInputs": []
        }
    )
    pfis.append(window_module)

    d0_slots: list[str] = [
        "Verbinding_LB",
        "Verbinding_RB",
        "Verbinding_RO",
        "Verbinding_LO"
        ]
    for node in d0_slots:
        pfis.append(resolve_mutation_create_perceptive_frame_instance(
            perceptiveFrameInstanceInput={
                "id": f"{node}",
                "perceptiveFrameId": "PF_Config_Mng_Node",
                "notionValueInputs": [{
                    "notionFrameId": "NF_Dimension",
                    "args": [{"key": "dimension", "value": "0"}]
                },{
                    "notionFrameId": "NF_Location",
                    "args": [],
                    "derivedFrom": [{
                        "notionFrameId": "NF_Coordinate",
                        "args": [{"key": "coordinate", "value": f"{0 if node[-2]=='L' else width}" }]
                    },{
                        "notionFrameId": "NF_Coordinate",
                        "args": [{"key": "coordinate", "value": "0" }]
                    },{
                        "notionFrameId": "NF_Coordinate",
                        "args": [{"key": "coordinate", "value": f"{0 if node[-1]=='O' else height}" }]
                    }]
                }]
            }
        ))
        pfis.append(resolve_create_config_mng_relation(       
            id=f"{uuid.uuid4()}", 
            relationType=ConfigurationManagementRelationClass.NODE_NODE_ENCLOSURE.name, 
            departureId=f"{PerceptiveFrameInstance.get_perceptive_frame_instance(node).id}",
            arrivalId=f"{window_module.id}"
        ))

    d1_slots: list[str] = [
        "Bovendorpel",
        "Stijl_R",
        "Onderdorpel",
        "Stijl_L"
    ]
    for node in d1_slots:
        pfis.append(resolve_mutation_create_perceptive_frame_instance(
            perceptiveFrameInstanceInput={
                "id": f"{node}",
                "perceptiveFrameId": "PF_Config_Mng_Node",
                "notionValueInputs": [{
                    "notionFrameId": "NF_Dimension",
                    "args": [{"key": "dimension", "value": "1"}]
                }]
            }
        ))
    d2_slots: list[str] = ["Glas"]
    for node in d2_slots:
        pfis.append(resolve_mutation_create_perceptive_frame_instance(
            perceptiveFrameInstanceInput={
                "id": f"{node}",
                "perceptiveFrameId": "PF_Config_Mng_Node",
                "notionValueInputs": [{
                    "notionFrameId": "NF_Dimension",
                    "args": [{"key": "dimension", "value": "2"}]
                }]
            }
        ))
    
    for item in range(4):
        pfis.append(resolve_mutation_create_perceptive_frame_instance(
            perceptiveFrameInstanceInput={
                "id": f"{d2_slots[0]}_down{item}",
                "perceptiveFrameId": "PF_Config_Mng_Node",
                "notionValueInputs": [{
                    "notionFrameId": "NF_Shrink",
                    "args": [{"key": "shrink", "value": "37"}]
                }]
            }))
        pfis.append(resolve_mutation_create_perceptive_frame_instance(
            perceptiveFrameInstanceInput={
                "id": f"{d0_slots[item]}_up0",
                "perceptiveFrameId": "PF_Config_Mng_Node",
                "notionValueInputs": [{
                    "notionFrameId": "NF_Cut",
                    "args": [{"key": "cut", "value": "45"}]
                }]
            }))
        pfis.append(resolve_mutation_create_perceptive_frame_instance(
            perceptiveFrameInstanceInput={
                "id": f"{d0_slots[item]}_up1",
                "perceptiveFrameId": "PF_Config_Mng_Node",
                "notionValueInputs": [{
                    "notionFrameId": "NF_Cut",
                    "args": [{"key": "cut", "value": "45"}]
                }]
            }))

    for node in d0_slots:
        pfis.extend(resolve_create_node(id=node, upPortCount=2))
    for node in d1_slots:
        pfis.extend(resolve_create_node(id=node, downPortCount=2, upPortCount=1))
    for node in d2_slots:
        pfis.extend(resolve_create_node(id=node, downPortCount=4))

    for item in range(4):
        pfis.append(resolve_create_config_mng_relation(
            id=f"{uuid.uuid4()}", 
            relationType=ConfigurationManagementRelationClass.NODE_NODE_CONNECTION.name, 
            departureId=f"Glas_down{item}", 
            arrivalId=f"{d1_slots[item]}_up0"))
    for item in range(4):
        pfis.append(resolve_create_config_mng_relation(
            id=f"{uuid.uuid4()}", 
            relationType=ConfigurationManagementRelationClass.NODE_NODE_CONNECTION.name, 
            departureId=f"{d1_slots[item]}_down0",
            arrivalId=f"{d0_slots[item]}_up1"))
        pfis.append(resolve_create_config_mng_relation(
            id=f"{uuid.uuid4()}", 
            relationType=ConfigurationManagementRelationClass.NODE_NODE_CONNECTION.name, 
            departureId=f"{d1_slots[item]}_down1",
            arrivalId=f"{d0_slots[(item+1)%4]}_up0"))
        
    for node in d1_slots:
        loc0 = []
        loc1 = []
        pf_node = PerceptiveFrameInstance.get_perceptive_frame_instance(node)
        arcs_node_down0 = query_arcs(nodeId=f"{node}_down0")
        other_port = get_port_other_side(this_port =f"{node}_down0", arcs=arcs_node_down0)
        other_arcs = query_arcs(other_port)
        other_node_id = get_port_node(this_port=other_port, arcs=other_arcs)
        other_node = PerceptiveFrameInstance.get_perceptive_frame_instance(other_node_id)
        for nv in other_node.notion_values:
            if nv.frame.id == "NF_Location":
                loc0 = nv.property["location"]
    
        arcs_node_down1 = query_arcs(nodeId=f"{node}_down1")
        other_port = get_port_other_side(this_port =f"{node}_down1", arcs = arcs_node_down1)
        other_arcs = query_arcs(other_port)
        other_node_id = get_port_node(this_port=other_port, arcs=other_arcs)
        other_node = PerceptiveFrameInstance.get_perceptive_frame_instance(other_node_id)
        for nv in other_node.notion_values:
            if nv.frame.id == "NF_Location":
                loc1 = nv.property["location"]
        nv_length = resolve_mutation_create_notion_value(
            notionValueInput={"notionFrameId": "NF_Length",
                    "args": []}, 
            derivedFrom=[{
                "notionFrameId": "NF_Location", 
                "args": [], 
                "derivedFrom": [{
                    "notionFrameId": "NF_Coordinate",
                    "args": [{"key": "coordinate", "value": f"{loc0[0]}" }]
                }, {
                    "notionFrameId": "NF_Coordinate",
                    "args": [{"key": "coordinate", "value": f"{loc0[1]}" }]
                }, {
                    "notionFrameId": "NF_Coordinate",
                    "args": [{"key": "coordinate", "value": f"{loc0[2]}" }]        
                }]}, {
                "notionFrameId": "NF_Location", 
                "args": [], 
                "derivedFrom": [{
                    "notionFrameId": "NF_Coordinate",
                    "args": [{"key": "coordinate", "value": f"{loc1[0]}" }]
                }, {
                    "notionFrameId": "NF_Coordinate",
                    "args": [{"key": "coordinate", "value": f"{loc1[1]}" }]
                }, {
                    "notionFrameId": "NF_Coordinate",
                    "args": [{"key": "coordinate", "value": f"{loc1[2]}" }]        
                }]}])

        pf_node.notion_values.append(nv_length)

    return pfis


schema = make_executable_schema(
type_defs, query, mutation, perceptive_frame, perceptive_frame_instance, notion_frame, notion_type, notion_unit, notion_value)

app = GraphQL(schema, debug=True)

def main():
    print("start notions graphql")

    # Notion Frames
    notion_topology_init()
    notions_legal.init()



    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    main()
