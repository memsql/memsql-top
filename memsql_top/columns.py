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

from __future__ import absolute_import

from attrdict import AttrDict
from collections import OrderedDict, namedtuple

from distutils.version import LooseVersion

import logging
from decimal import Decimal

from .humanize import *

class ColumnMetadata(object):
    __slots__ = ["name", "memsql_column_name", "fixed_width",
                 "humanize", "colorize", "sort_key", "help",
                 "width_weight"]
    def __init__(self,
                 name,
                 memsql_column_name,
                 help=None,
                 width_weight=None,
                 humanize=lambda c: str(c) if c is not None else "",
                 colorize=lambda c: 0,
                 sort_key=None):

        self.name = name
        self.help = help
        self.width_weight = width_weight
        self.fixed_width = self.width_weight is None
        self.humanize = humanize
        self.colorize = colorize
        self.sort_key = sort_key
        self.memsql_column_name = memsql_column_name

    def display_width(self):
        assert self.fixed_width
        sort_key_len = len(" (" + self.sort_key + ")") if self.sort_key else 0
        return max(10, len(self.name) + sort_key_len)

    def display_weight(self):
        assert not self.fixed_width
        return self.width_weight

class MemSqlColumnsMetadata(object):
    __slots__ = ['columns', 'default_sort_key', 'minimum_version',
                 'focus_column']

    def __init__(self, columns, default_sort_key, focus_column, minimum_version):
        self.columns = columns
        self.default_sort_key = default_sort_key
        self.minimum_version = minimum_version
        self.focus_column = focus_column

    def CheckHasDataForAllColumns(self, dict):
        dictkeys = set(dict.keys())
        columns_keys = set(self.columns.keys())
        missing = columns_keys - dictkeys
        extra = dictkeys - columns_keys

        assert dictkeys >= columns_keys, \
               "Expected %s but got %s" % (missing, extra)

        return dict

class Columns57(MemSqlColumnsMetadata):
    def __init__(self):
        sort_keys = iter(map(lambda x: "f%d" % x, range(1, 13)))
        super(Columns57, self).__init__(OrderedDict((cm.name, cm) for cm in [
            ColumnMetadata("Database",
                "database_name",
                help="Database name"),
            ColumnMetadata("Query",
                "query_text",
                width_weight=1,
                humanize=CleanQuery,
                help="Paramaterized aggregator query"),
            ColumnMetadata("Executions/sec",
                "commits",
                humanize=HumanizeCount,
                colorize=GetColorizeFunc(10),
                sort_key=next(sort_keys),
                help="Successful query executions per second"),
            ColumnMetadata("RowCount/sec",
                "rowcount",
                humanize=HumanizeCount,
                colorize=GetColorizeFunc(1000),
                sort_key=next(sort_keys),
                help="Rows returned by queries per second"),
            ColumnMetadata("CpuUtil",
                "cpu_time",
                humanize=HumanizePercent,
                colorize=GetColorizeFunc(0.10),
                sort_key=next(sort_keys),
                help="Sum cpu utilization accross the cluster"),
            ColumnMetadata("Memory/query",
                "memory_use",
                humanize=HumanizeBytes,
                colorize=GetColorizeFunc(128*1024),
                sort_key=next(sort_keys),
                help="Average memory used per execution"),
            ColumnMetadata("ExecutionTime/query",
                "execution_time",
                humanize=HumanizeTime,
                colorize=GetColorizeFunc(10),
                sort_key=next(sort_keys),
                help="Average query latency"),
            ColumnMetadata("QueuedTime/query",
                "queued_time",
                humanize=HumanizeTime,
                colorize=GetColorizeFunc(1),
                sort_key=next(sort_keys),
                help="Average queued time per execution")
        ]), "CpuUtil", "Query", LooseVersion("5.7"))

    def GetPopUpText(self, conn, name):
        return name

    def CheckSupported(self, conn):
        if not conn.get('select @@forward_aggregator_plan_hash as f').f:
            sys.exit("forward_aggregator_plan_hash is required")

    def GetAllCounterSnapshots(self, conn):
        #
        # We store the parameterized query and deparameterize it in GetPlanCache so
        # that we can filter out this query.
        #
        # We filter out queries where the plan_hash is null, because those
        # correspond to leaf queries with no corresponding aggregator.
        #
        # MemSql5.7 would sometimes return null for counter columns.
        #
        GET_PLANCACHE_QUERY = "select plan_hash, " + \
            ", ".join("IFNULL(%s, 0) as %s" % (c.memsql_column_name,
                                               c.memsql_column_name)
                      for c in self.columns.values()) + \
            " from distributed_plancache_summary " + \
            " where plan_hash is not null"

        rows = conn.query(GET_PLANCACHE_QUERY)
        return {
            r.plan_hash: r
            for r in rows if r.query_text != GET_PLANCACHE_QUERY
        }

    def GetCpuTotalFromAllDeltas(self, allDeltas):
        return sum(d.CpuUtil for d in allDeltas.values())

    def GetMaxCpuTotal(self, conn):
        return float(1.0)

    def GetMaxMemTotal(self, conn):
        # TODO(awreece) This isn't accurately max memory across the whole
        # cluster.
        #
        return int(conn.get('select @@maximum_memory as m').m)

    def GetCurrentMemTotal(self, conn):
        # TODO(awreece) This isn't accurately max memory across the whole cluster.
        tsm_row = conn.get("show status like 'Total_server_memory'")
        return float(tsm_row.Value.split(" ")[0])

    def IsDeltaInteresting(self, delta):
        return delta.commits > 0

    def NormalizeCounterDelta(self, snapshot, interval):
        snapkeys = set(snapshot.keys())
        colnames = set(c.memsql_column_name for c in self.columns.values())

        assert snapkeys >= colnames, (snapkeys - colnames, colnames - snapkeys)

        ret = AttrDict({})
        for meta in self.columns.values():
            snapval = snapshot[meta.memsql_column_name]
            if isinstance(snapval, (int, Decimal)):
                ret[meta.name] = float(snapshot[meta.memsql_column_name])
            else:
                ret[meta.name] = snapval

        ret['Executions/sec'] = ret['Executions/sec'] / interval
        ret['RowCount/sec'] = ret['RowCount/sec'] / interval

        # Divide by 1000ms to convert to %.
        ret['CpuUtil'] = ret['CpuUtil'] / 1000.0 / interval

        ret['ExecutionTime/query'] = ret['ExecutionTime/query'] / float(snapshot.commits)
        ret['Memory/query'] = ret['Memory/query'] / float(snapshot.commits)
        ret['QueuedTime/query'] = ret['QueuedTime/query'] / float(snapshot.commits)
        return ret

class Columns58(MemSqlColumnsMetadata):
    def __init__(self):
        sort_keys = iter(map(lambda x: "f%d" % x, range(1, 13)))
        super(Columns58, self).__init__(OrderedDict((cm.name, cm) for cm in [
            ColumnMetadata("Type",
                "activity_type",
                help="Activity type"),
            ColumnMetadata("Database",
                "database_name",
                help="Database name",
                width_weight=1),
            ColumnMetadata("Name",
                "activity_name",
                help="Activity name",
                width_weight=2),
            ColumnMetadata("Cpu/s",
                "cpu_time_ms",
                humanize=HumanizePercent,
                colorize=GetColorizeFunc(0.10),
                sort_key=next(sort_keys),
                help="Sum cpu utilization across the cluster"),
            ColumnMetadata("Mem/s",
                "memory_bs",
                humanize=HumanizeBytes,
                colorize=GetColorizeFunc(128*1024),
                sort_key=next(sort_keys),
                help="Memory bytes used in the past second"),
             ColumnMetadata("Disk/s",
                "disk_b",
                humanize=HumanizeBytes,
                colorize=GetColorizeFunc(128*1024),
                sort_key=next(sort_keys),
                help="Disk bytes in the past second"),
              ColumnMetadata("Net/s",
                "network_b",
                humanize=HumanizeBytes,
                colorize=GetColorizeFunc(128*1024),
                sort_key=next(sort_keys),
                help="Network bytes in the past second"),
            ColumnMetadata("Pf/s",
                "memory_major_faults",
                humanize=HumanizeCount,
                colorize=GetColorizeFunc(1),
                help="Sum page faults across the closter"),
            ColumnMetadata("Lat/q",
                "elapsed_time_ms",
                humanize=HumanizeTime,
                colorize=GetColorizeFunc(1000),
                help="Latency per query"),
            ColumnMetadata("Cpu/q",
                "cpu_time_ms",
                humanize=HumanizeTime,
                colorize=GetColorizeFunc(5),
                help="Cpu time per query"),
            ColumnMetadata("CpuW/q",
                "cpu_wait_time_ms",
                humanize=HumanizeTime,
                colorize=GetColorizeFunc(2),
                help="Cpu wait per query"),
            ColumnMetadata("LockW/q",
                "lock_time_ms",
                humanize=HumanizeTime,
                colorize=GetColorizeFunc(5),
                help="Lock wait per query"),
            ColumnMetadata("DiskW/q",
                "disk_time_ms",
                humanize=HumanizeTime,
                colorize=GetColorizeFunc(5),
                help="Disk wait per query"),
            ColumnMetadata("NetW/q",
                "network_time_ms",
                humanize=HumanizeTime,
                colorize=GetColorizeFunc(5),
                help="Network wait per query"),
            ColumnMetadata("Run",
                "run_count",
                humanize=HumanizeCount,
                colorize=GetColorizeFunc(10),
                sort_key=next(sort_keys),
                help="Currently running"),
            ColumnMetadata("Done/s",
                "success_count + failure_count",
                humanize=HumanizeCount,
                colorize=GetColorizeFunc(10),
                sort_key=next(sort_keys),
                help="Finished running"),
      ]), "Cpu/s", "Name", LooseVersion("5.8"))

    def GetAllCounterSnapshots(self, conn):
        #
        # We store the parameterized query and deparameterize it in GetPlanCache so
        # that we can filter out this query.
        #
        GET_PLANCACHE_QUERY = "select " + \
            ", ".join("%s" % (c.memsql_column_name)
                      for c in self.columns.values()) + \
            " from mv_activities_cumulative"

        rows = conn.query(GET_PLANCACHE_QUERY)
        return {
            (r.activity_type, r.database_name, r.activity_name): r
            for r in rows
        }

    def GetPopUpText(self, conn, name):
        rows = [r for r in conn.query("select query_text q from mv_queries where activity_name = '%s'" % name)]
        assert len(rows) <= 1
        if len(rows) == 1:
            return rows[0].q
        else:
            return name

    def CheckSupported(self, conn):
        if not conn.get('select @@forward_aggregator_plan_hash as f').f:
            sys.exit("forward_aggregator_plan_hash is required")

        if not conn.get("select @@read_advanced_counters as r").r:
            logging.warn("Cannot read advanced counters.")
            logging.warn("Run `set global read_advanced_counters = ON` on all nodes in the cluster for the best experience.")

    def IsDeltaInteresting(self, delta):
        return delta.run_count > 0 or delta['success_count + failure_count'] > 0

    def GetCpuTotalFromAllDeltas(self, allDeltas):
        return sum(d['Cpu/s'] if d['Cpu/s'] is not None else 0 for d in allDeltas.values())

    def GetMaxCpuTotal(self, conn):
        return float(conn.get("select sum(num_cpus) s from mv_nodes").s)

    def GetMaxMemTotal(self, conn):
        return float(conn.get("select sum(max_memory_mb) m from mv_nodes").m)

    def GetCurrentMemTotal(self, conn):
        return float(conn.get("select sum(memory_used_mb) m from mv_nodes").m)

    def NormalizeCounterDelta(self, snapshot, interval):
        snapkeys = set(snapshot.keys())
        colnames = set(c.memsql_column_name for c in self.columns.values())

        assert snapkeys >= colnames, (snapkeys - colnames, colnames - snapkeys)

        ret = AttrDict({})
        for meta in self.columns.values():
            snapval = snapshot[meta.memsql_column_name]
            if isinstance(snapval, (int, Decimal)):
                ret[meta.name] = float(snapshot[meta.memsql_column_name])
            else:
                ret[meta.name] = snapval

        # od = opt div
        def od(v, d):
            return v/d if v is not None else v

        commits = float(snapshot.run_count + snapshot['success_count + failure_count'])
        # Divide by 1000ms to convert to %.
        ret['Cpu/s'] = od(od(ret['Cpu/s'], 1000.0), interval)
        ret['Disk/s'] = od(ret['Disk/s'], interval)
        ret['Mem/s'] = od(ret['Mem/s'], interval)
        ret['Pf/s'] = od(ret['Pf/s'], interval)
        ret['Net/s'] = od(ret['Net/s'], interval)
        ret['Done/s'] = od(ret['Done/s'], interval)
        ret['Lat/q'] = od(ret['Lat/q'], commits)
        ret['Cpu/q'] = od(ret['Cpu/q'], commits)
        ret['CpuW/q'] = od(ret['CpuW/q'], commits)
        ret['LockW/q'] = od(ret['LockW/q'], commits)
        ret['DiskW/q'] = od(ret['DiskW/q'], commits)
        ret['NetW/q'] = od(ret['NetW/q'], commits)

        return ret

def DetectColumnsMetaOrExit(conn):
    memsql_version = LooseVersion(conn.get("select @@memsql_version as v").v)
    versionsSupported = [Columns58(), Columns57()]

    for version in versionsSupported:
        if memsql_version >= version.minimum_version:
            version.CheckSupported(conn)
            return version
    sys.exit("memsql 5.7 or above is required -- got %s" % memsql_version)
