from django.conf import settings


def default(var_name, value):
    if hasattr(settings, var_name):
        return getattr(settings, var_name)
    return value


GRPC_TLS_DIR = default('GRPC_TLS_DIR', 'grpc_dir')
GRPC_TLS_PORT = default('GRPC_TLS_PORT', '50051')
GRPC_TLS_SUFFIX = default('GRPC_TLS_SUFFIX', 'GRPC')
GRPC_TLS_AUTO_PACKAGE = default('GRPC_TLS_AUTO_PACKAGE', 'auto_grpc_app')
GRPC_TLS_PROTO_FILE = default('GRPC_TLS_PROTO_FILE', 'grpc_app.proto')
GRPC_TLS_MODELS_APP = default('GRPC_TLS_MODELS_APP', ['core'])

# Derived constants
GRPC_TLS_GRPC_FILE = GRPC_TLS_PROTO_FILE.replace('.proto', '_pb2_grpc.py')
GRPC_TLS_PROTO_PATH = '%s/%s' % (GRPC_TLS_DIR, GRPC_TLS_PROTO_FILE)
GRPC_TLS_GRPC_PATH = '%s/%s' % (GRPC_TLS_DIR, GRPC_TLS_GRPC_FILE)
GRPC_TLS_AUTO_MODULE = '%s/%s' % (GRPC_TLS_DIR, GRPC_TLS_AUTO_PACKAGE)
GRPC_TLS_AUTO_FILE = '%s/%s.py' % (GRPC_TLS_DIR, GRPC_TLS_AUTO_PACKAGE)

# Fields to ifnore while dictifying
GRPC_TLS_IGNORE_FIELDS = default(
    'GRPC_TLS_IGNORE_FIELDS', ['created', 'modified', 'id'])
GRPC_TLS_DISABLE_FIELD_TYPES = default(
    'GRPC_TLS_DISABLE_FIELD_TYPES', ['ManyToManyRel', 'ManyToManyField'])

# Fields to remove while generating model
GRPC_TLS_REMOVE_FIELDS = default('GRPC_TLS_REMOVE_FIELDS', [])

# Dict to translate Django fields into Protobuf fields
GRPC_TLS_FIELDS = default('GRPC_TLS_FIELDS', dict(
    CharField='string',
    DateTimeField='string',
    TimeField='string',
    DateField='string',
    BooleanField='bool',
    NullBooleanField='bool',
    EmailField='string',
    UUIDField='string',
    ManyToManyField='repeated string',
    ManyToManyRel='repeated string',
    TextField='string',
    MarkdownTextField='string',
    ImageField='string',
    FileField='string',
    SearchVectorField='string',
    FSMField='string',
    JSONField='string',
    OneToOneRel='int64',
    OneToOneField='int64',
    PositiveSmallIntegerField='int32',
    DecimalField='double',
    IntegerField='int64',
    BigIntegerField='int64',
    ForeignKey='int64',
    AutoField='int64',
))

# `GRPC_TLS_AST_MAP` basically says how to extract data
# from a given AST `Assign` object
GRPC_TLS_AST_MAP = default('GRPC_TLS_AST_MAP', dict(
    Num=lambda kw: kw.value.n,
    Str=lambda kw: kw.value.s,
    Name=lambda kw: kw.value.id,
    NameConstant=lambda kw: kw.value.value,
    Attribute=lambda kw: '%s.%s' % (kw.value.value, kw.value.attr),
))

GRPC_TLS_PROTO_HEADER = default('GRPC_TLS_PROTO_HEADER', '''
syntax = "proto3";

package grpc_app;

message Void {}

message ID {
    int64 id = 1;
}
''')
GRPC_TLS_PROTO_FOOTER = default('GRPC_TLS_PROTO_FOOTER', '')

GRPC_TLS_CRUD_TEMPLATE = default('GRPC_TLS_CRUD_TEMPLATE', '''
from %(app)s.models import %(model_name)s
GRPC_TLS_IGNORE_FIELDS = %(ignore_fields)s


def read_%(model_name_lower)s(*args, **kwargs):
    try:
        return %(model_name)s.objects.get(*args, **kwargs)
    except %(model_name)s.DoesNotExist:
        return None


def read_%(model_name_lower_plural)s_filter(*args, **kwargs):
    return %(model_name)s.objects.filter(*args, **kwargs)


def create_%(model_name_lower)s(*args, **kwargs):
    for ignore_field in GRPC_TLS_IGNORE_FIELDS:
        if ignore_field in kwargs:
            del kwargs[ignore_field]
    for key in list(kwargs):
        if kwargs[key] in [None, 'None', '']:
            del kwargs[key]
    return %(model_name)s.objects.create(*args, **kwargs)


def update_%(model_name_lower)s(id, *args, **kwargs):
    for ignore_field in GRPC_TLS_IGNORE_FIELDS:
        if ignore_field in kwargs:
            del kwargs[ignore_field]
    for key in list(kwargs):
        if kwargs[key] in [None, 'None', '']:
            del kwargs[key]
    return %(model_name)s.objects.filter(id=id).update(*args, **kwargs)


def delete_%(model_name_lower)s(id):
    return %(model_name)s.objects.get(id=id).delete()
''')

GRPC_TLS_RPC_METHODS = default('GRPC_TLS_RPC_METHODS', '''
from %(GRPC_TLS_DIR)s.grpc_app_pb2 import %(model_name)s, Void
from %(GRPC_TLS_DIR)s.%(app_slug)s_crud import (
    read_%(model_name_lower)s,
    delete_%(model_name_lower)s,
    create_%(model_name_lower)s,
    update_%(model_name_lower)s,
    read_%(model_name_lower_plural)s_filter,
)


def %(model_name_lower)s_to_dict(obj, is_dj_obj=False):
    # Cycle through fields directly
    d = {}
    if obj is None:
        return d
    foriegn_keys = %(foriegn_keys)s
    for field in %(fields)s:
        value = getattr(obj, field, None)
        if field in foriegn_keys and value in [0, '']:
            continue
        if field in [None, 'None']:
            continue
        d[field] = value
        if is_dj_obj and field in ['created', 'modified']:
            d[field] = value.isoformat()
    return d


class %(rpc_name)s:

    def Read%(model_name_plural)sFilter(self, void, context):
        dj_objs = read_%(model_name_lower_plural)s_filter()
        return [%(model_name)s(
            **%(model_name_lower)s_to_dict(dj_obj, is_dj_obj=True)) for dj_obj in dj_objs]

    def Read%(model_name)s(self, id, context):
        dj_obj = read_%(model_name_lower)s(id=id.id)
        return %(model_name)s(**%(model_name_lower)s_to_dict(dj_obj, is_dj_obj=True))

    def Create%(model_name)s(self, obj, context):
        dj_obj = create_%(model_name_lower)s(**%(model_name_lower)s_to_dict(obj))
        return %(model_name)s(**%(model_name_lower)s_to_dict(dj_obj, is_dj_obj=True))

    def Update%(model_name)s(self, obj, context):
        obj_dict = %(model_name_lower)s_to_dict(obj)
        del obj_dict['id']
        obj = update_%(model_name_lower)s(obj.id, **obj_dict)
        return Void()

    def Delete%(model_name)s(self, id, context):
        delete_%(model_name_lower)s(id.id)
        return Void()
''')

GRPC_TLS_RPC_CONTENT = default('GRPC_TLS_RPC_CONTENT', '''
  rpc Delete%(model_name)s(ID) returns (Void);
  rpc Update%(model_name)s(%(model_name)s) returns (Void);
  rpc Read%(model_name)s(ID) returns (%(model_name)s);
  rpc Create%(model_name)s(%(model_name)s) returns (%(model_name)s);
  rpc Read%(model_name_plural)sFilter(Void) returns (stream %(model_name)s);
''')
