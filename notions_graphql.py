from ariadne import QueryType, MutationType, ObjectType, EnumType, ScalarType, gql, make_executable_schema
from ariadne.asgi import GraphQL
import uvicorn
from enum import IntEnum, Enum

#######################################
# Notion classes
#######################################

class NotionType(IntEnum):
    GENDER = 0
    BOOLEAN = 1
    DATE = 2
    INTEGER = 3
    FLOAT = 4

class NotionUnit(IntEnum):
    NONE = 0
    DAY = 1
    WEEK = 2
    MONTH = 3
    YEAR = 4

class NotionFrame:
    frames = dict()

    def __init__(self, name: str, type: NotionType, unit: NotionUnit, converter_code: str, converter: callable, discriminator_code: str, discriminator: callable) -> None:
        self.name = name
        self.type = type
        self.unit = unit
        self.converter_code = converter_code
        self.converter = converter
        self.discriminator_code = discriminator_code
        self.discriminator = discriminator
        NotionFrame.frames[name] = self

    def get_notion_frame(name: str) -> object:
        return NotionFrame.frames[name]
    
    
class NotionValue:
    values = dict()

    def __init__(self, id: str, frame: NotionFrame, args: dict) -> None:
        self.id = id
        self.frame = frame
        self.property = self.frame.converter(args)
        self.classification = self.frame.discriminator(self.property)
        NotionValue.values[id] = self

    def get_notion_value(id: str) -> object:
        return NotionValue.values.get(id)


class PerceptiveFrame:
    frames = dict()

    def __init__(self, name: str, notion_frame_names: list[str], discriminator_code: str, discriminator: callable) -> None:
        self.name = name
        nfs = [NotionFrame.get_notion_frame(nf_name) for nf_name in notion_frame_names]
        keys = [nf.name for nf in nfs]
        values = [nf for nf in nfs]
        self.notion_frames = {key: value for key, value in zip(keys, values)}
        self.discriminator_code = discriminator_code
        self.discriminator = discriminator
        PerceptiveFrame.frames[name] = self
    
    def get_perceptive_frame(name: str) -> object:
        return PerceptiveFrame.frames[name]


class PerceptiveFrameInstance:
    values = dict()

    def __init__(self, id: str, perceptive_frame_name: str, notion_value_ids: list[str]) -> None:
        self.id = id,
        self.perceptive_frame = PerceptiveFrame.get_perceptive_frame(perceptive_frame_name)
        nvs = [NotionValue.get_notion_value(id) for id in notion_value_ids]
        keys = [nv.frame.name for nv in nvs]
        values = [nv for nv in nvs]
        self.notion_values = {key: value for key, value in zip(keys, values)}
        PerceptiveFrameInstance.values[id] = self

    def get_perceptive_frame_instance(id: str) -> object:
        return PerceptiveFrameInstance.values.get(id)


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
        "Get notion frame by name"
        notionFrame(name: String!): NotionFrame
        "Get all notion values"
        notionValues: [NotionValue!]!
        "Get notion value by id"
        notionValue(id: ID!): NotionValue
        "Get all perceptive frames"
        perceptiveFrames: [PerceptiveFrame!]!
        "Get perceptive frame by name"
        perceptiveFrame(name: String!): PerceptiveFrame
        "Get all perceptive frame instances"
        perceptiveFrameInstances: [PerceptiveFrameInstance!]!
        "Get perceptive frame instances by id"
        perceptiveFrameInstance(id: ID!): PerceptiveFrameInstance
    }

    type Mutation {
        "Create notion frame"
        createNotionFrame(name: String!, type: NotionType, unit: NotionUnit, converter: String, discriminator: String): NotionFrame
        "Create notion value"
        createNotionValue(id: ID!, frame: String!, args: [Arg!]!): NotionValue
        "Create perceptive frame"
        createPerceptiveFrame(name: String!, notionFrameNames: [String!]!, discriminator: String): PerceptiveFrame
        "Create perceptive frame instance"
        createPerceptiveFrameInstance(id: ID!, perceptiveFrameName: String!, notionValueIds: [ID!]!): PerceptiveFrameInstance
    }
    
    """
    A description of how an observer evaluates sensory stimuli or measurements.
    """
    type NotionFrame {
        name: ID!
        type: NotionType
        unit: NotionUnit
        converter: String
        discriminator: String
    }

    """
    The value of a Notion, expressed in a Notion-Frame.
    """
    type NotionValue {
        id: ID!
        frame: NotionFrame
        property: String
        classification: String
    }

    """
    A set of Notion Frames used by an actor to express knowledge. 
    """
    type PerceptiveFrame {
        name: String!
        notionFrames: [NotionFrame!]!
        discriminator: String
    }

    type PerceptiveFrameInstance {
        id: ID!
        perceptiveFrame: PerceptiveFrame
        notionValues: [NotionValue!]!
        classification: String
    }
    
    enum NotionType {
        GENDER
        BOOLEAN
        DATE
        INTEGER
        FLOAT
    }
                
    enum NotionUnit {
        NONE
        DAY
        WEEK
        MONTH
        YEAR
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
        "GENDER": 0,
        "BOOLEAN": 1,
        "DATE": 2,
        "INTEGER": 3,
        "FLOAT" : 4,
    }
)
notion_unit = EnumType(
    "NotionUnit",
    {
        "NONE": 0,
        "DAY": 1,
        "WEEK": 2,
        "MONTH": 3,
        "YEAR" : 4,
    }
)

#######################################
# Queries
#######################################

@query.field("notionFrames")
def resolve_notion_frames(*_) -> list[NotionFrame]:
    return [nf for nf in NotionFrame.frames.values()]

@query.field("notionFrame")
def resolve_notion_frame(*_, name: str) -> NotionFrame:
    return NotionFrame.get_notion_frame(name)

@query.field("notionValues")
def resolve_notion_values(*_) -> list[NotionValue]:
    return [nv for nv in NotionValue.values.values()]

@query.field("notionValue")
def resolve_notion_value(*_, id: str) -> NotionValue:
    return NotionValue.get_notion_value(id)

@query.field("perceptiveFrames")
def resolve_perceptive_frames(*_) -> list[PerceptiveFrame]:
    return [pf for pf in PerceptiveFrame.frames.values()]

@query.field("perceptiveFrame")
def resolve_perceptive_frame(*_, name: str) -> PerceptiveFrame:
    return PerceptiveFrame.get_perceptive_frame(name)

@query.field("perceptiveFrameInstances")
def resolve_perceptive_frame_instances(*_) -> list[PerceptiveFrameInstance]:
    return [nv for nv in PerceptiveFrameInstance.values.values()]

@query.field("perceptiveFrameInstance")
def resolve_perceptive_frame_instance(*_, id: str) -> PerceptiveFrameInstance:
    return PerceptiveFrameInstance.get_perceptive_frame_instance(id)


@notion_frame.field("name")
def resolve_notion_frame_name(obj: NotionFrame, *_) -> str:
    return obj.name

@notion_frame.field("type")
def resolve_notion_frame_type(obj: NotionFrame, *_) -> NotionType:
    return obj.type

@notion_frame.field("unit")
def resolve_notion_frame_unit(obj: NotionFrame, *_) -> NotionUnit:
    return obj.unit

@notion_frame.field("converter")
def resolve_notion_frame_converter(obj: NotionFrame, *_) -> str:
    return obj.converter_code

@notion_frame.field("discriminator")
def resolve_notion_frame_discriminator(obj: NotionFrame, *_) -> str:
    return obj.discriminator_code


@notion_value.field("classification")
def resolve_notion_value_classification(obj: NotionValue, *_) -> str:
    classification = obj.classification
    if isinstance(classification, Enum):
        return classification.name
    else:
        return obj.classification

@notion_value.field("property")
def resolve_notion_value_classification(obj: NotionValue, *_) -> str:
    property = obj.property
    if isinstance(property, IntEnum):
        return property.name
    else:
        return obj.property


@perceptive_frame.field("name")
def resolve_perceptive_frame_name(obj: PerceptiveFrame, *_) -> str:
    return obj.name

@perceptive_frame.field("notionFrames")
def resolve_perceptive_frame_notion_frames(obj: PerceptiveFrame, *_) -> list[NotionFrame]:
    return [nv for nv in obj.notion_frames.values()]

@perceptive_frame.field("discriminator")
def resolve_perceptive_frame_discriminator(obj: PerceptiveFrame, *_) -> str:
    return obj.discriminator_code


@perceptive_frame_instance.field("id")
def resolve_perceptive_frame_instance_id(obj: PerceptiveFrameInstance, *_) -> str:
    return obj.id[0]

@perceptive_frame_instance.field("perceptiveFrame")
def resolve_perceptive_frame_instance_perceptive_frame(obj: PerceptiveFrameInstance, *_) -> PerceptiveFrame: 
    return obj.perceptive_frame

@perceptive_frame_instance.field("notionValues")
def resolve_perceptive_frame_notion_values(obj: PerceptiveFrameInstance, *_) -> list[NotionValue]: 
    return obj.notion_values.values()

@perceptive_frame_instance.field("classification")
def resolve_perceptive_frame_instance_classification(obj: PerceptiveFrameInstance, *_):
    notion_values = obj.notion_values
    keys = [key for key in notion_values.keys()]
    values = [nv.frame for nv in notion_values.values()]
    notion_frames = {key: value for key, value in zip(keys, values)}
    return obj.perceptive_frame.discriminator(notion_frames, notion_values).name

#######################################
# Mutations
#######################################

@mutation.field("createNotionFrame")
def resolve_mutation_create_notion_frame(*_, name: str, type: NotionType, unit: NotionUnit, converter: str, discriminator: str) -> NotionFrame:
    d = {}
    exec(converter, d, d)
    converter_function = d[list(d)[-1]]
    
    exec(discriminator, d, d)
    discriminator_function = d[list(d)[-1]]
    return NotionFrame(name = name, type = type, unit = unit, 
                       converter_code = converter, converter = converter_function, 
                       discriminator_code = discriminator, discriminator = discriminator_function)

@mutation.field("createNotionValue")
def resolve_mutation_create_notion_value(*_, id: str, frame: str, args: list) -> NotionValue:
    nf = NotionFrame.get_notion_frame(frame)
    keys = [arg['key'] for arg in args]
    values = [arg['value'] for arg in args]
    args = {key: value for key, value in zip(keys, values)}
    return NotionValue(id = id, frame = nf, args = args)

@mutation.field("createPerceptiveFrame")
def resolve_mutation_create_perceptive_frame(*_, name: str, notionFrameNames: list[str], discriminator: str) -> PerceptiveFrame:
    d = {}
    exec(discriminator, d, d)
    discriminator_function = d[list(d)[-1]]
    return PerceptiveFrame(name = name, notion_frame_names = notionFrameNames, discriminator_code = discriminator, discriminator = discriminator_function)

@mutation.field("createPerceptiveFrameInstance")
def resolve_mutation_create_perceptive_frame_instance(*_, id: str, perceptiveFrameName: str, notionValueIds: list[str]) -> PerceptiveFrameInstance:
    return PerceptiveFrameInstance(id = id, perceptive_frame_name = perceptiveFrameName, notion_value_ids = notionValueIds)


schema = make_executable_schema(
    type_defs, query, mutation, perceptive_frame, perceptive_frame_instance, notion_frame, notion_type, notion_unit, notion_value
)

app = GraphQL(schema, debug=True)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)