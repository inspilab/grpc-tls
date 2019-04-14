import os
from setuptools import setup
from distutils import util

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()

setup(
    name='grpc-tls',
    version='1.1.6',
    packages=[
        'grpc_tls',
        'grpc_tls.management',
        'grpc_tls.management.commands',
    ],
    description='This tools for generating grpc files',
    long_description=README,
    author='inspitrip',
    author_email='hai@inspitrip.com',
    url='https://github.com/inspilab/grpc-tls/',
    license='MIT',
    install_requires=[
        'grpcio-tools>=1.19.0',
        'inflect>=2.1.0'
    ]
)
