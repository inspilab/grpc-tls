# gRPC tools
This is tool for auto generating *.proto and mapping django model with protobuf.

# Installation
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

# Usage
Generate *.proto file
```
python manage.py grpc_tls
```

All files will be generated in `grpc_dir/*`

# Notes
DO NOT FILES IN `grpc_dir`
