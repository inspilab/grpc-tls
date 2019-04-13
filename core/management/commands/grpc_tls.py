from __future__ import absolute_import

import os
import re
from ast import parse
from pathlib import Path
from inspect import getsource
from importlib import import_module
from pkg_resources import resource_filename

from inflect import engine
from grpc_tools import protoc

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand

from grpc_tls.constants import GRPC_TLS_SUFFIX, GRPC_TLS_FIELDS, GRPC_TLS_AST_MAP, \
    GRPC_TLS_IGNORE_FIELDS, GRPC_TLS_RPC_METHODS, GRPC_TLS_CRUD_TEMPLATE, \
    GRPC_TLS_RPC_CONTENT, GRPC_TLS_REMOVE_FIELDS, GRPC_TLS_DIR, GRPC_TLS_GRPC_PATH, \
    GRPC_TLS_PROTO_HEADER, GRPC_TLS_PROTO_FOOTER, GRPC_TLS_PROTO_PATH, \
    GRPC_TLS_AUTO_FILE, GRPC_TLS_DISABLE_FIELD_TYPES, GRPC_TLS_MODELS_APP

plural = engine().plural


def ensure_data():
    '''
    Ensure that the gRPC directory and files
    '''
    if not os.path.exists(GRPC_TLS_DIR):
        os.makedirs(GRPC_TLS_DIR)
    Path('%s/__init__.py' % GRPC_TLS_DIR).touch()


def extract(ast, attrib):
    d = {}

    # This is a Hacky, Hacky solution for some invalid standard format model.
    if ast.__class__.__name__ != "Assign":
        return d
    if ast.value.__class__.__name__ == "List":
        return d
    if ast.value and not hasattr(ast.value, 'keywords'):
        return d

    for kw in ast.value.keywords:
        if kw.arg != attrib:
            continue
        klass = kw.value.__class__.__name__
        if klass in ['Dict', 'List', 'Call']:
            continue
        d[ast.targets[0].id] = GRPC_TLS_AST_MAP[klass](kw)
    return d


def process(model, attrib):
    d = {}
    ast = parse(getsource(model))
    ast = ast.body[0]
    for sub_ast in ast.body:
        d.update(extract(sub_ast, attrib))
    return d


def get_inflections(model_name):
    return dict(
        model_name=model_name,
        model_name_lower=model_name.lower(),
        model_name_plural=plural(model_name),
        model_name_lower_plural=plural(model_name.lower()),
        rpc_name=model_name + GRPC_TLS_SUFFIX,
    )


def hacky_m2one_name(field):
    '''
    This is a Hacky, Hacky method to get name.
    field.related_model.__class__.__name__ somehow returns `BaseModel`
    which is not somethig we want
    '''
    return str(field.related_model).split(".")[-1].split("'")[0]


def process_model(model):
    fields = {}
    many_fields = {}
    foriegn_keys = []
    defaults = process(model, 'default')
    inflections = get_inflections(model.__name__)
    for field in model._meta.get_fields():
        f_name = field.__class__.__name__
        if f_name == 'ManyToOneRel':
            many_fields[field.name] = hacky_m2one_name(field)
        elif f_name == 'ForeignKey':
            name = '%s_id' % field.name
            fields[name] = f_name
            foriegn_keys.append(name)
        else:
            fields[field.name] = f_name
    return dict(
        fields=fields, defaults=defaults,
        inflections=inflections, foriegn_keys=foriegn_keys,
        many_fields=many_fields)


def process_app(app):
    models = {}
    for model in app.get_models():
        models[model.__name__] = process_model(model)
    return models


def process_apps():
    app_models = {}
    for item in GRPC_TLS_MODELS_APP:
        app = apps.get_app_config(item)
        models = process_app(app)
        if len(models.keys()) != 0:
            app_models[app.name] = models
    return app_models


def get_rpc_type(field, fields, many_fields):
    if field in many_fields:
        return 'repeated string'  # ManyToOneRel fields
    dj_field_type = fields[field]
    return GRPC_TLS_FIELDS[dj_field_type]


def generate_model(model_name, model):
    fields = model['fields']
    many_fields = model['many_fields']

    fields_declaration = ''
    field_names = list(fields.keys()) + list(many_fields.keys())
    for idx, field in enumerate(sorted(field_names)):
        if field in many_fields:
            continue
        if field in fields and fields[field] in GRPC_TLS_DISABLE_FIELD_TYPES:
            continue

        field_type = get_rpc_type(field, fields, many_fields)
        fields_declaration += '\n    %s %s = %s;' % (field_type, field, idx + 1)
    defnition = '\nmessage %s {%s\n}\n' % (
        model_name, fields_declaration)
    return defnition


def generate_app(app, models):
    app_defnition = ''
    for model_name, model in models.items():
        app_defnition += generate_model(model_name, model)
    return app_defnition


def generate_model_proto(app_models):
    model_protos = ''
    for app, models in app_models.items():
        model_protos += generate_app(app, models)
    return model_protos


def sluggify(app):
    return re.sub('[^0-9a-zA-Z]+', '_', app)


def write_to_file(app, kind, content, extention='py'):
    app = sluggify(app)
    comment_prefix = '//'
    if extention in ['py']:
        comment_prefix = '#'
    with open("%s/%s_%s.%s" % (GRPC_TLS_DIR, app, kind, extention), "w") as f:
        print('writing to %s ...' % f.name)
        f.write('# DO NOT EDIT THIS FILE MANUALLY\n')
        f.write('# THIS FILE IS AUTO-GENERATED\n')
        f.write('# MANUAL CHANGES WILL BE DISCARDED\n')
        f.write('# PLEASE READ GRPC DOCS\n')
        f.write(content.strip())


def codify_model(app, model_name, model_defnition):
    fields = sorted(model_defnition['fields'].keys())
    foriegn_keys = sorted(model_defnition['foriegn_keys'])
    for field in model_defnition['fields'].keys():
        if field in GRPC_TLS_REMOVE_FIELDS:
            fields.remove(field)
        if model_defnition['fields'] and field in model_defnition['fields'] \
                and model_defnition['fields'][field] in GRPC_TLS_DISABLE_FIELD_TYPES:
            fields.remove(field)

    ctx = dict(
        app=app, app_slug=sluggify(app), fields=fields, GRPC_TLS_DIR=GRPC_TLS_DIR,
        foriegn_keys=foriegn_keys, ignore_fields=GRPC_TLS_IGNORE_FIELDS)
    ctx.update(model_defnition['inflections'])
    return GRPC_TLS_CRUD_TEMPLATE % ctx, GRPC_TLS_RPC_METHODS % ctx


def codify_app(app, models):
    crud_contents = ''
    rpc_contents = ''
    for model in models.keys():
        crud_content, rpc_content = codify_model(app, model, models[model])
        crud_contents += crud_content
        rpc_contents += rpc_content
    write_to_file(app, 'rpc', rpc_contents)
    write_to_file(app, 'crud', crud_contents)


def generate_rpc_code(app_models):
    for app in app_models.keys():
        codify_app(app, app_models[app])


def generate_app_rpc(app_models):
    content = ''
    for app in app_models:
        models = app_models[app]
        for model in models:
            content += GRPC_TLS_RPC_CONTENT % models[model]['inflections']

    return content


def generate_auto_grpc_app(app_models):
    content = ''
    models = []
    for app in app_models:
        _models = [
            '%s%s' % (model, GRPC_TLS_SUFFIX)
            for model in app_models[app].keys()]
        models += _models
        _models = ", ".join(_models)
        app = sluggify(app)
        content += '\nfrom %s.%s_rpc import %s' % (GRPC_TLS_DIR, app, _models)
    models = ", ".join(models)
    content += '\n\nclass AutoGRPC(%s):\n    pass' % models
    with open(GRPC_TLS_AUTO_FILE, "w") as f:
        print('writing to %s' % f.name)
        f.write(content)


def protoc_arguments():
    '''
    Construct protobuf compiler arguments
    '''
    proto_include = resource_filename('grpc_tools', '_proto')
    return [
        protoc.__file__, '-I', GRPC_TLS_DIR, '--python_out=%s' % GRPC_TLS_DIR,
        '--grpc_python_out=%s' % GRPC_TLS_DIR, GRPC_TLS_PROTO_PATH,
        '-I%s' % proto_include]


def fix_grpc_import():
    '''
    Snippet to fix the gRPC import path
    '''
    with open(GRPC_TLS_GRPC_PATH, 'r') as f:
        filedata = f.read()
    filedata = filedata.replace(
        'import grpc_app_pb2 as grpc__app__pb2',
        'from %s import grpc_app_pb2 as grpc__app__pb2' % GRPC_TLS_DIR)
    with open(GRPC_TLS_GRPC_PATH, 'w') as f:
        f.write(filedata)


class Command(BaseCommand):
    help = 'Generate proto files'

    def handle(self, *args, **options):
        ensure_data()
        app_models = process_apps()
        generate_rpc_code(app_models)
        generate_auto_grpc_app(app_models)
        MODELS_PROTO = generate_model_proto(app_models)
        GRPC_TLS_RPC = "service GRPCAPP{%s}" % generate_app_rpc(app_models)
        with open(GRPC_TLS_PROTO_PATH, 'w') as f:
            print('writing to %s ...' % f.name)
            content = '''
%s
%s
%s
%s
                    ''' % (GRPC_TLS_PROTO_HEADER, MODELS_PROTO, GRPC_TLS_RPC, GRPC_TLS_PROTO_FOOTER)
            f.write(content.strip())
        protoc.main(protoc_arguments())
        fix_grpc_import()
