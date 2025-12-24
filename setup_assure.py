#!/usr/bin/env python3
# Copyright 2025 Lockheed Martin Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup, find_packages
import os

# Read version from __init__.py
version = '0.1.0'

# Read long description from README if it exists
long_description = ''
readme_path = os.path.join(os.path.dirname(__file__), 'laikaassure', 'testcases', 'README.md')
if os.path.exists(readme_path):
    with open(readme_path, 'r') as f:
        long_description = f.read()

setup(
    name='laikaassure',
    version=version,
    description='Validation tool for Laika BOSS scanning outcomes',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Lockheed Martin Corporation',
    license='Apache-2.0',
    packages=['laikaassure'],
    package_data={
        'laikaassure': [
            'templates/*.html',
            'static/css/*.css',
            'static/js/*.js',
            'etc/*.conf',
            'testcases/*.yaml',
            'testcases/*.md',
            'testcases/samples/*',
        ],
    },
    include_package_data=True,
    install_requires=[
        'PyYAML>=5.0',
        'Flask>=2.0',
        'requests>=2.25',
    ],
    extras_require={
        'zmq': [
            'pyzmq>=22.0',
            # laikaboss is required for ZMQ client but not listed as it's
            # typically installed separately in the same environment
        ],
    },
    entry_points={
        'console_scripts': [
            'laikaassure=laikaassure.assure:main',
            'laikaassure-server=laikaassure.assureserver:main',
        ],
    },
    scripts=[
        'laikaassure/assure.py',
        'laikaassure/assureserver.py',
    ],
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Security',
        'Topic :: Software Development :: Testing',
    ],
)
