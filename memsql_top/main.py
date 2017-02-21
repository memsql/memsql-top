#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016, 2017 by MemSQL. All rights reserved.
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
import argparse
import curses
import sys

import database

from DatabasePoller import DatabasePoller
from QueryListBox import QueryListBox
from ResourceMonitor import ResourceMonitor
from WrappingPopUpViewer import WrappingPopUpViewer
from ColumnHeadings import ColumnHeadings

from distutils.version import LooseVersion

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=3306, type=int)
    parser.add_argument("--password", default="")
    parser.add_argument("--user", default="root")

    parser.add_argument("--cores", default=4, type=int,
	                help="When calculating max cpu util, assume the cluster has this many cores.")

    parser.add_argument("--update-interval", default=3.0, type=float,
	                help="How frequently to update the screen.")

    args = parser.parse_args()

    try:
	conn = database.connect(host=args.host, port=args.port,
				database="information_schema",
				password=args.password, user=args.user)
    except Exception as e:
	sys.exit("Unexpected error when connecting to database: %s" % e)

    BLACK = 'h16'
    _BLACK = 'black'
    BLUE = 'h24'
    _BLUE = 'light blue'
    ACCENT_BLUE = 'h74'
    _ACCENT_BLUE = 'dark cyan'
    LIGHT_GRAY = 'h255'
    _LIGHT_GRAY = 'light gray'
    GRAY = 'h253'
    _GRAY = 'light gray'
    TEXT_GRAY = 'h240'
    _TEXT_GRAY = 'dark gray'
    HEAD_GRAY = 'h102'
    _HEAD_GRAY = 'light gray'
    DARK_GRAY = 'h234'
    _DARK_GRAY = 'dark gray'
    WHITE = 'h231'
    _WHITE = 'white'

    palette = [
        ('popup', _TEXT_GRAY, _WHITE, '', TEXT_GRAY, WHITE),
        ('head',
         _HEAD_GRAY, _DARK_GRAY, 'bold', HEAD_GRAY, DARK_GRAY),
        ('head_key',
         _ACCENT_BLUE, _DARK_GRAY, 'bold,underline', ACCENT_BLUE, DARK_GRAY),
        ('head_so',
         _WHITE, _DARK_GRAY, 'bold,standout', WHITE, DARK_GRAY),
        ('resource_bar_empty', _GRAY, _BLACK, '', GRAY, BLACK),
        ('resource_bar', _GRAY, _BLUE, '', GRAY, BLUE),
        ('foot',
         _TEXT_GRAY, _LIGHT_GRAY, 'bold', TEXT_GRAY, LIGHT_GRAY),
        ('foot_key',
         _ACCENT_BLUE, _LIGHT_GRAY, 'bold,underline', ACCENT_BLUE, LIGHT_GRAY),
        ('body', _TEXT_GRAY, _WHITE, '', TEXT_GRAY, WHITE),
        ('body_focus',
         _TEXT_GRAY, _LIGHT_GRAY, 'underline', TEXT_GRAY, LIGHT_GRAY),
    ]

    for tup  in [(0, _TEXT_GRAY, TEXT_GRAY),
	         (1, 'light green', 'h77'),
	         (2, 'yellow', 'h220'),
	         (3, 'light magenta', 'h202'),
	         (4, 'light red', 'h160')]:
	code, old_color, color = tup
        palette.append(('body_%d' % code, old_color, _WHITE, '', color, WHITE))
        palette.append(('body_focus_%d' % code, old_color, _LIGHT_GRAY, 'underline', color, LIGHT_GRAY))

    memsql_version = conn.get("select @@memsql_version as v").v
    if LooseVersion(memsql_version) < LooseVersion("5.7"):
	sys.exit("memsql 5.7 or above is required -- got %s" % memsql_version)

    # Run any check system queries before we start the DatabasePoller and
    # start tracking queries.
    #
    if not conn.get('select @@forward_aggregator_plan_hash as f').f:
        sys.exit("forward_aggregator_plan_hash is required")

    # TODO(awreece) This isn't accurately max memory across the whole cluster.
    max_mem = int(conn.get('select (select count(*) from information_schema.leaves) * (select @@maximum_memory) as m').m)

    dbpoller = DatabasePoller(conn, args.update_interval)

    resources = ResourceMonitor(args.cores, max_mem)
    column_headings = ColumnHeadings()
    header = urwid.Pile([
        urwid.Text("MemSQL - QueryTop"),
# The resources are currently a lie, don't show them.
#       resources,
        urwid.Divider(),
        column_headings
    ])

    qlistbox = QueryListBox()

    footer = urwid.Text([
        ('foot_key', "UP"), ", ", ('foot_key', "DOWN"), ", ",
        ('foot_key', "PAGE UP"), " and ", ('foot_key', "PAGE DOWN"),
        " move view  ",
        ('foot_key', "F#"), " sorts by column ",
        ('foot_key', "Q"), " exits",
    ])

    view = WrappingPopUpViewer(urwid.Frame(
        urwid.AttrMap(qlistbox, "body"),
        header=urwid.AttrMap(header, "head"),
        footer=urwid.AttrMap(footer, "foot")))

    urwid.connect_signal(qlistbox, 'sort_column_changed',
                         column_headings.update_sort_column)
    urwid.connect_signal(dbpoller, 'plancache_changed',
                         qlistbox.update_entries)
    urwid.connect_signal(dbpoller, 'cpu_util_changed',
                         resources.update_cpu_util)
    urwid.connect_signal(dbpoller, 'mem_usage_changed',
                         resources.update_mem_usage)
    urwid.connect_signal(qlistbox, 'query_selected', view.show_popup)

    def handle_keys(input):
        if input in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        if input in qlistbox.sort_keys():
            qlistbox.update_sort_column(input)

    loop = urwid.MainLoop(view, palette, unhandled_input=handle_keys)

    curses.setupterm()
    if curses.tigetnum("colors") == 256:
        loop.screen.set_terminal_properties(colors=256)
    loop.set_alarm_in(args.update_interval, dbpoller.poll)
    loop.run()


if __name__ == "__main__":
    main()
