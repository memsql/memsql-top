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

import re


def CleanQuery(query):
    #
    # Strip -- style comments but not /* */ style comments, as the latter
    # are sometimes used for version specific logic.
    #
    # Convert all newlines to spaces
    #
    query = " ".join(re.sub(r"--.*$", "", l) for l in query.split("\n"))

    # Strip unnecessary whitespace.
    query = re.sub(r"(^ +)|( +$)", "", query)
    query = re.sub(r" +", " ", query)
    return query


def HumanizePercent(pct):
    return "%d%%" % (pct * 100)


def HumanizeTime(ms):
    if ms < 1000:
        return "%dms" % ms
    elif ms < 1000*1000:
        return "%.1fs" % (ms / 1000.0)
    elif ms < 1000*1000*60:
        return "%.1fm" % (ms / (1000*1000.0))
    else:
        return "%.1fh" % (ms / (1000*1000*60.0))


def HumanizeBytes(b):
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if b < 1024.0:
            return "%.1f %s" % (b, unit)
        b /= 1024.0
    return "%.1fEB" % b


def HumanizeCount(c):
    return "%.1f" % c
