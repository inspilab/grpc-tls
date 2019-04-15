# gRPC tools
This is tool for auto generating *.proto and mapping django model with protobuf.

## Requirements
- Python (2.7, 3.4, 3.5, 3.6, 3.7)
- Django (1.11, 2.0, 2.1, 2.2)

## Installation
Install using pip
```
pip install grpc-tls
```

Add 'grpc_tls' to your INSTALLED_APPS setting.
```
INSTALLED_APPS = (
    ...
    'grpc_tls',
)
```

Update list apps your want migrate to protobuf:
`GRPC_TLS_MODELS_APP=['core']`

Update proto file name:
`GRPC_TLS_BASE_PROTO='app_name'`.

*Note*: This name must be unique if your app run multiple *.proto file

## Usage
Generate *.proto file
```
python manage.py grpc_tls
```

All files will be generated in `grpc_dir/*`

## Example
Let's take a look at a quick example of running gRPC server.

First generate proto files by running command line above.

Then create a django command line: `run_grpc.py`.
```
import grpc
from concurrent import futures
from django.core.management.base import BaseCommand

from grpc_dir import auto_grpc_app, grpc_app_pb2_grpc

class Command(BaseCommand):
    help = 'Start gRPC server'

    def handle(self, *args, **options):
        server = grpc.server(futures.ThreadPoolExecutor(
            max_workers=10))
        grpc_app_pb2_grpc.add_GRPCAPPServicer_to_server(
            auto_grpc_app.AutoGRPC(), server)
        server.add_insecure_port('[::]:50051')
        server.start()
        print('server started on port 50051 ...')
        try:
            while True:
                pass
        except KeyboardInterrupt:
            server.stop(0)
```

Start gRPC server:
```
python manage.py run_grpc
```
You can now send request at `http://127.0.0.1:50051/`

## Notes
DO NOT FILES IN `grpc_dir`
