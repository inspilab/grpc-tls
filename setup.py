import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()

setup(
    name='grpc-tls',
    version='1.1.0',
    packages=['core'],
    description='This tools for generating grpc files',
    long_description=README,
    author='inspitrip',
    author_email='hai@inspitrip.com',
    url='https://github.com/inspilab/grpc-tls/',
    license='MIT',
    install_requires=[
        'Django>=1.11',
        'grpcio>=1.19.0',
        'grpcio-tools>=1.19.0'
        'inflect>=2.1.0'
    ]
)
