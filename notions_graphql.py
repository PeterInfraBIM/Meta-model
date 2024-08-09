from ariadne import QueryType, MutationType, ObjectType, EnumType, ScalarType, gql, make_executable_schema
from ariadne.asgi import GraphQL
import uvicorn
from enum import IntEnum
from datetime import datetime
import dateutil
import inspect

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

class AgeClass(IntEnum):
    CHILD = 1
    ADULT = 2

class Gender(IntEnum):
    MALE = 1
    FEMALE = 2

class BiologicalGender(IntEnum):
    XX = 1
    XY = 2

class Person(IntEnum):
    WOMAN = 1
    MAN = 2
    GIRL = 3
    BOY = 4

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
        # self.notion_frames = [NotionFrame.get_notion_frame(nf_name) for nf_name in notion_frame_names]
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

    def get_perceptive_frame_instance_value(id: str) -> object:
        return NotionValue.values.get(id)


# nf_legal_age = NotionFrame(
#     name = "legal_age",
#     type = NotionType.INTEGER,
#     unit = NotionUnit.YEAR,
#     converter_code = """lambda args: int((args['actual_date'] - args['birth_date']).days//365.24)""",
#     converter = lambda args: int((args['actual_date'] - args['birth_date']).days//365.24),
#     discriminator_code = """lambda age: AgeClass.CHILD if age < 18 else AgeClass.ADULT""",
#     discriminator = lambda age: AgeClass.CHILD if age < 18 else AgeClass.ADULT
# )

# nf_legal_gender = NotionFrame(
#     name = "legal_gender",
#     type = NotionType.GENDER,
#     unit = NotionUnit.NONE,
#     converter_code = """lambda args: args['gender']""",
#     converter = lambda args: args['gender'],
#     discriminator_code = """lambda gender: gender""",
#     discriminator = lambda gender: gender
# )

# nf_biological_gender = NotionFrame(
#     name = "biological_gender",
#     type = NotionType.GENDER,
#     unit = NotionUnit.NONE,
#     converter_code = """lambda arg: arg['dna'].name""",
#     converter = lambda arg: arg['dna'].name,
#     discriminator_code = """lambda arg: Gender.FEMALE.name if arg == BiologicalGender.XX.name else Gender.MALE.name""",
#     discriminator = lambda arg: Gender.FEMALE.name if arg == BiologicalGender.XX.name else Gender.MALE.name
# )

# def legal_discr(gender, age):
#     nf = NotionFrame.get_notion_frame("legal_age")
#     age_class = nf.discriminator(age)
#     if gender == Gender.FEMALE:
#         if age_class == AgeClass.ADULT:
#             return Person.WOMAN
#         return Person.GIRL
#     else:
#         if age_class == AgeClass.ADULT:
#             return Person.MAN
#         return Person.BOY

# legal_discr_function_string = """
# def legal_discr(gender, age):
#     nf = NotionFrame.get_notion_frame("legal_age")
#     age_class = nf.discriminator(age)
#     if gender == Gender.FEMALE:
#         if age_class == AgeClass.ADULT:
#             return Person.WOMAN
#         return Person.GIRL
#     else:
#         if age_class == AgeClass.ADULT:
#             return Person.MAN
#         return Person.BOY
# """
# exec(legal_discr_function_string)



#######################################
# GraphQL schema
#######################################

type_defs = gql(
    '''
    scalar Datetime

    input LegalAgeInput {
        birthDate: Datetime!
        actualDate: Datetime!
    }

    input LegalGenderInput {
        gender: Gender!
    }

    input Arg {
        key: String!
        value: String!
    }
    
    type Query {
        notionFrames: [NotionFrame!]!
        notionFrame(name: String!): NotionFrame
        notionValues: [NotionValue!]!
        perceptiveFrames: [PerceptiveFrame!]!
#        legalAge(birthDate: Datetime!, actualDate: Datetime!): NotionValue!
#        legalGender(gender: Gender!): NotionValue!
#        biologicalGender(dna: BiologicalGender!): NotionValue!
#        legal(legalAge: LegalAgeInput!, legalGender: LegalGenderInput!): PerceptiveFrame!
    }

    type Mutation {
        createNotionFrame(name: String!, type: NotionType, unit: NotionUnit, converter: String, discriminator: String): NotionFrame
        createNotionValue(id: ID!, frame: String!, args: [Arg!]!): NotionValue
        createPerceptiveFrame(name: String!, notionFrameNames: [String!]!, discriminator: String): PerceptiveFrame
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

    enum AgeClass {
        CHILD
        ADULT
    }

    enum Gender {
        MALE
        FEMALE
    }

    enum BiologicalGender {
        XX
        XY
    }

    enum Person {
        WOMAN
        MAN
        GIRL
        BOY
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
age_class = EnumType(
    "AgeClass",
    {
        "CHILD": 1,
        "ADULT": 2,
    }
)
gender = EnumType(
    "Gender",
    {
        "MALE": 1,
        "FEMALE": 2,
    }
)
biological_gender = EnumType(
    "BiologicalGender",
    {
        "XX": 1,
        "XY": 2,
    }
)
person = EnumType(
    "Person",
    {
        "WOMAN": 1,
        "MAN": 2,
        "GIRL": 3,
        "BOY":  4,
    }
)
datetime_scalar = ScalarType("Datetime")

@datetime_scalar.serializer
def serialize_datetime(value):
    return value.isoformat()

@datetime_scalar.value_parser
def parse_datetime_value(value):
    # dateutil is provided by python-dateutil library
    if value:
        return dateutil.parser.parse(value)

@datetime_scalar.literal_parser
def parse_datetime_literal(ast):
    value = str(ast.value)
    return parse_datetime_value(value)  # reuse logic from parse_value

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

@query.field("perceptiveFrames")
def resolve_perceptive_frames(*_) -> list[PerceptiveFrame]:
    return [pf for pf in PerceptiveFrame.frames.values()]

# @query.field("legal")
# def resolve_legal(*_, legalAge: dict, legalGender: dict):
#     args = dict()
#     args["birth_date"] = parse_datetime_value(legalAge['birthDate'])
#     args["actual_date"] = parse_datetime_value(legalAge['actualDate'])
#     return PerceptiveFrame(
#         name = "legal", 
#         notion_values = [resolve_legal_age(birthDate = legalAge['birthDate'], actualDate = legalAge['actualDate']),
#                          resolve_legal_gender(gender = legalGender['gender'])],
#                          discriminator = legal_discr)    

# @query.field("legalAge")
# def resolve_legal_age(*_, birthDate: str, actualDate: str):
#     nf = NotionFrame.get_notion_frame("legal_age")
#     args = dict()
#     args["birth_date"] = parse_datetime_value(birthDate)
#     args["actual_date"] = parse_datetime_value(actualDate)
#     return NotionValue("id", nf, args)
    
# @query.field("legalGender")
# def resolve_legal_gender(*_, gender: int):
#     nf = NotionFrame.get_notion_frame("legal_gender")
#     args = dict()
#     args["gender"] = Gender(gender)
#     return NotionValue("id", nf, args)

# @query.field("biologicalGender")
# def resolve_biological_gender(*_, dna: int):
#     nf = NotionFrame.get_notion_frame("biological_gender")
#     args = dict()
#     args["dna"] = BiologicalGender(dna)
#     return NotionValue("id", nf, args)

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
    # return obj.get_callable_as_string(obj.converter)

@notion_frame.field("discriminator")
def resolve_notion_frame_discriminator(obj: NotionFrame, *_) -> str:
    return obj.discriminator_code
    # return obj.get_callable_as_string(obj.discriminator)

@notion_value.field("classification")
def resolve_notion_value_classification(obj: NotionValue, *_) -> str:
    classification = obj.classification
    if isinstance(classification, IntEnum):
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
    type_defs, query, mutation, perceptive_frame, perceptive_frame_instance, notion_frame, notion_type, notion_unit, 
    notion_value, age_class, gender, biological_gender, person
)

app = GraphQL(schema, debug=True)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)