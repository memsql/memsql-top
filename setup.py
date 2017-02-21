#!/usr/bin/env python
#
# Copyright (c) 2016 by MemSQL. All rights reserved.
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

from setuptools import setup, find_packages

def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='memsql-top',
    version='0.0.4',
    description='A tool for visualing top queries run against memsql',
    long_description=readme(),
    author='Alex Reece',
    author_email='awreece' '@' 'gmail.com',
    license='Apache License',
    install_requires=[
        'urwid',
        'attrdict',
        'pymysql',
    ],
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console :: Curses',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Database',
        'Topic :: Software Development :: Testing',
    ],
    entry_points={
        'console_scripts': [
            'memsql-top=memsql_top.main:main',
        ],
    }
)
