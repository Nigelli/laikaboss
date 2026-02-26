#!/usr/bin/env python
# Copyright 2015 Lockheed Martin Corporation
# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC
# (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
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
#
# setup_core.py - Minimal setup for core ZMQ scanner only
# Excludes: laikarest package, REST/mail/collector/storage scripts

from setuptools import setup, find_packages

setup(
    name = "laikaboss-core",
    author = "Lockheed Martin and Sandia National Laboratories",
    description = "laikaboss-core: minimal ZMQ-based file scanner",
    license = "Apache 2.0",
    keywords = "malware",
    url = "https://github.com/sandialabs/laikaboss",
    python_requires='>=3.8',

    # Only include laikaboss package, not laikarest
    packages = ['laikaboss', 'laikaboss.modules', 'laikaboss.extras'],

    data_files = [
        # Core config files
        ('/etc/laikaboss', [
            'etc/dist/laikaboss.conf',
            'etc/dist/laikad.conf',
            'etc/cloudscan/cloudscan.conf',
            'etc/framework/dispatch.yara',
            'etc/framework/conditional-dispatch.yara',
        ]),
        # Runtime directories
        ('/var/laikaboss/tmp', []),
        ('/var/log/laikaboss', []),
        # Module config files
        ('/etc/laikaboss/modules/suspicious_md5/',
            ['etc/framework/modules/suspicious_md5/suspicious_md5s.txt']),
        ('/etc/laikaboss/modules/dispositioner',
            ['etc/framework/modules/dispositioner/disposition.yara']),
        ('/etc/laikaboss/modules/scan-yara',
            ['etc/framework/modules/scan-yara/signatures.yara']),
    ],

    # Only core scanner scripts
    scripts = [
        "laika.py",      # Standalone scanner
        "laikad.py",     # ZMQ daemon
        "cloudscan.py",  # ZMQ client
    ],

    test_suite='nose2.collector.collector',
)
