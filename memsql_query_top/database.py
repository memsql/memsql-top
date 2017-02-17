#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 by MemSQL. All rights reserved.
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

from attrdict import AttrDict
import pymysql
import pymysql.cursors

class Connection(object):
    def __init__(self, host, port, database, user, password):
        self.conn = pymysql.connect(host=host, port=port, db=database,
                                    user=user, password=password,
                                    cursorclass=pymysql.cursors.DictCursor)


    def get(self, query):
        with self.conn.cursor() as cursor:
            cursor.execute(query)
            return AttrDict(cursor.fetchone())

    def query(self, query):
        with self.conn.cursor() as cursor:
            cursor.execute(query)
            r = cursor.fetchone()
            while r:
                yield AttrDict(r)
                r = cursor.fetchone()

def connect(host='127.0.0.1', port=3306, database="", user="root", password=""):
    return Connection(host, port, database, user, password)
