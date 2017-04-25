#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import urwid

from attrdict import AttrDict
from collections import namedtuple
import database
import os
import sys
import threading
import time

from decimal import Decimal

def DiffSnapshot(a, b):
    akeys = set(a.keys())
    bkeys = set(b.keys())

    assert akeys == bkeys, (akeys - bkeys, bkeys - akeys)

    ret = AttrDict({})
    for k in akeys:
        if isinstance(a[k], (int, Decimal)) and k != "run_count" and not b[k] is None:
            ret[k] = int(a[k] - b[k]) if a[k] >= b[k] else 0
        else:
            ret[k] = a[k]
    return ret


def DiffPlanCache(meta, new_plancache, old_plancache, interval):
    diff_plancache = {}
    for key, n_ent in new_plancache.items():
        delta = n_ent
        if key in old_plancache:
            o_ent = old_plancache[key]
            delta = DiffSnapshot(n_ent, o_ent)

        if meta.IsDeltaInteresting(delta):
            diff_plancache[key] = meta.NormalizeCounterDelta(delta, interval)

    return diff_plancache


class DatabasePoller(threading.Thread):
    def __init__(self, args, column_meta):
        try:
            #
            # The connection objects are not thread safe, so create a new
            # connection.
            #
            conn = database.connect(host=args.host, port=args.port,
                                    database="information_schema",
                                    password=args.password, user=args.user)
        except Exception as e:
            sys.exit("Unexpected error when connecting to database: %s" % e)

        self.conn = conn
        self.update_interval = args.update_interval
        self.column_meta = column_meta
        self.last_read_time = time.time()
        self.plancache = self.column_meta.GetAllCounterSnapshots(self.conn)
        self.diff_plancache = dict()
        self.sum_cpu_util = 0
        self.current_mem = 0
        super(DatabasePoller, self).__init__()

    def get_database_data(self):
        return self.diff_plancache, self.sum_cpu_util, self.current_mem

    def run(self):
        while True:
            time.sleep(self.update_interval)
            self.poll()
            os.write(self.signal_file, "\n")

    def start(self, signal_file):
        self.daemon = True
        self.signal_file = signal_file
        super(DatabasePoller, self).start()

    def poll(self):
        new_time = time.time()
        new_plancache = self.column_meta.GetAllCounterSnapshots(self.conn)

        self.diff_plancache = DiffPlanCache(self.column_meta,
                                       new_plancache, self.plancache,
                                       new_time - self.last_read_time)
        self.last_read_time = new_time
        self.plancache = new_plancache

        self.sum_cpu_util = self.column_meta.GetCpuTotalFromAllDeltas(self.diff_plancache)
        self.current_mem = self.column_meta.GetCurrentMemTotal(self.conn)
