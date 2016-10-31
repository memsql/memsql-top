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
from memsql.common import database

from columns import CheckHasDataForAllColumns

PlanCacheKey = namedtuple("PlanCacheKey", ["PlanHash", "AggregatorPlanHash"])


def GetPlanCache(conn):
    #
    # We store the parameterized query and deparameterize it in GetPlanCache so
    # that we can filter out this query.
    #
    GET_PLANCACHE_QUERY = "select plan_id, database_name, query_text, " + \
                          "plan_hash, aggregator_plan_hash, " +\
                          "commits, rowcount, execution_time, " + \
                          "IFNULL(queued_time, @) as queued_time, " + \
                          "cpu_time, " + \
                          "commits*average_memory_use as memory_use " + \
                          "from information_schema.plancache"

    rows = conn.query(GET_PLANCACHE_QUERY.replace("@", "0"))

    return {
        PlanCacheKey(r.plan_hash, r.aggregator_plan_hash): r
        for r in rows if r.query_text != GET_PLANCACHE_QUERY
    }


def NormalizeDiffPlanCacheEntry(interval, plan_id, database_name, query_text,
                                commits, rowcount, cpu_time, execution_time,
                                memory_use, queued_time):
    return CheckHasDataForAllColumns(AttrDict({
        'PlanId': plan_id,
        'Database': database_name,
        'Query': query_text,
        'Executions': commits / interval,
        'RowCount': rowcount / interval,
        'CpuUtil': cpu_time / 1000.0 / interval,
        'ExecutionTime': execution_time / commits,
        'Memory': memory_use / commits,
        'QueuedTime': queued_time / commits
    }))


def DiffPlanCache(new_plancache, old_plancache, interval):
    diff_plancache = {}
    for key, n_ent in new_plancache.items():
        if key not in old_plancache:
            diff_plancache[key] = NormalizeDiffPlanCacheEntry(
                interval,
                plan_id=n_ent.plan_id,
                database_name=n_ent.database_name,
                query_text=n_ent.query_text,
                commits=n_ent.commits,
                rowcount=n_ent.rowcount,
                execution_time=n_ent.execution_time,
                cpu_time=n_ent.cpu_time,
                memory_use=n_ent.memory_use,
                queued_time=n_ent.queued_time)
        elif n_ent.commits - old_plancache[key].commits > 0:
            o_ent = old_plancache[key]
            diff_plancache[key] = NormalizeDiffPlanCacheEntry(
                interval,
                plan_id=n_ent.plan_id,
                database_name=n_ent.database_name,
                query_text=n_ent.query_text,
                commits=n_ent.commits - o_ent.commits,
                rowcount=n_ent.rowcount - o_ent.rowcount,
                execution_time=n_ent.execution_time - o_ent.execution_time,
                cpu_time=n_ent.cpu_time - o_ent.cpu_time,
                memory_use=n_ent.memory_use - o_ent.memory_use,
                queued_time=n_ent.queued_time - o_ent.queued_time
            )
    return diff_plancache


class DatabasePoller(urwid.Widget):
    signals = ['plancache_changed', 'cpu_util_changed', 'mem_usage_changed']

    def __init__(self, conn, update_interval, leafuser, leafpass):
        self.conn = conn
        self.leaf_conns = [
            database.connect(host=l['Host'], port=l['Port'], password=leafpass,
                             user=leafuser)
            for l in conn.query("show leaves")
        ]
        self.update_interval = update_interval
        self.plancache = self.get_distributed_plancache()
        super(DatabasePoller, self).__init__()

    def get_distributed_plancache(self):
        ma_plancache = GetPlanCache(self.conn)
        for c in self.leaf_conns:
            for k, lpce in GetPlanCache(c).items():
                mpk = PlanCacheKey(k.AggregatorPlanHash, None)
                if mpk in ma_plancache:
                    mpce = ma_plancache[mpk]
                    #
                    # We aggregate cpu_time and memory_use since they are
                    # resources (properties of the cluster) but we do not
                    # aggregate queued_time, commits, etc because the MA
                    # version of those metrics is more useful.
                    #
                    mpce.cpu_time += lpce.cpu_time
                    mpce.memory_use += lpce.memory_use
        return ma_plancache

    def poll(self, loop, _):
        loop.set_alarm_in(self.update_interval, self.poll)
        ma_plancache = self.get_distributed_plancache()

        diff_plancache = DiffPlanCache(ma_plancache, self.plancache,
                                       self.update_interval)
        self._emit('plancache_changed', diff_plancache)
        self.plancache = ma_plancache

        sum_cpu_util = sum(pe.CpuUtil for pe in diff_plancache.values())
        self._emit('cpu_util_changed', sum_cpu_util)

        tsm_row = self.conn.get("show status like 'Total_server_memory'")
        self._emit('mem_usage_changed', float(tsm_row.Value.split(" ")[0]))
