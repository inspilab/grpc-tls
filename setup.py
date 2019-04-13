import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()

setup(
    name='grpc-tls',
    version='1.0',
    packages=['core'],
    description='This tools for generating grpc files',
    long_description=README,
    author='inspitrip',
    author_email='hai@inspitrip.com',
    url='https://github.com/inspilab/grpc-tls/',
    license='MIT',
    install_requires=[
        'Django>=1.6,<1.7',
    ]
)
