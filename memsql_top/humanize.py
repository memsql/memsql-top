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
    if pct is None:
        return ""
    return "%d%%" % (pct * 100)

def HumanizeBytes(b):
    if b is None:
        return ""
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if b < 1024.0:
            return "%.1f %s" % (b, unit)
        b /= 1024.0
    return "%.1fEB" % b

def HumanizeTime(t):
    if t is None:
        return ""
    units = [("ms", 1000.0), ("s", 60.0), ("m", 60.0), ("h", 24.0)]
    for unit, scale in units:
        if t < scale:
            return "%.1f %s" % (t, unit)
        t /= scale
    return "%.1fd" % t

def HumanizeCount(c):
    if c is None:
        return ""
    return "%.1f" % c


def GetColorizeFunc(scale_point):
    return lambda x: 0 if x is None or x < scale_point else \
                     1 if x < 10*scale_point else \
		     2 if x < 1000*scale_point else \
		     3 if x < 100000*scale_point else \
		     4
