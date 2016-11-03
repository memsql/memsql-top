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

from collections import OrderedDict, namedtuple

from humanize import *

CM = namedtuple("ColumnMetadata",
                ["fixed_width", "humanize", "sort_key", "help"])

COLUMNS = OrderedDict([
    ("Database",        CM(fixed_width=True,
                           humanize=lambda c: str(c),
                           sort_key="f1",
                           help="Database name")),
    ("Query",           CM(fixed_width=False,
                           humanize=CleanQuery,
                           sort_key="f2",
                           help="Paramaterized aggregator query")),
    ("ExecutionsPS",    CM(fixed_width=True,
                           humanize=HumanizeCount,
                           sort_key="f3",
                           help="Successful query executions per second")),
    ("RowCountPS",      CM(fixed_width=True,
                           humanize=HumanizeCount,
                           sort_key="f4",
                           help="Rows returned by queries per second")),
    ("CpuUtil",         CM(fixed_width=True,
                           humanize=HumanizePercent,
                           sort_key="f5",
                           help="Sum cpu utilization accross the cluster")),
    ("MemoryPQ",        CM(fixed_width=True,
                           humanize=HumanizeBytes,
                           sort_key="f6",
                           help="Average memory used per execution")),
    ("ExecutionTimePQ", CM(fixed_width=True,
                           humanize=HumanizeTime,
                           sort_key="f7",
                           help="Average query latency")),
    ("QueuedTimePQ",    CM(fixed_width=True,
                           humanize=HumanizeTime,
                           sort_key="f8",
                           help="Average queued time per execution"))
])

DEFAULT_SORT_COLUMN = 'CpuUtil'


def GetColumnWidth(name):
    return len(name) + len(" (F#)")


def CheckHasDataForAllColumns(dict):
    dictkeys = set(dict.keys())
    COLUMNSkeys = set(COLUMNS.keys())
    missing = COLUMNSkeys - dictkeys
    extra = dictkeys - COLUMNSkeys

    assert dictkeys >= COLUMNSkeys, "Expected %s but got %s" % (missing, extra)

    return dict
