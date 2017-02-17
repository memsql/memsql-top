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
import argparse
import curses
import sys

import database

from DatabasePoller import DatabasePoller
from QueryListBox import QueryListBox
from ResourceMonitor import ResourceMonitor
from WrappingPopUpViewer import WrappingPopUpViewer
from ColumnHeadings import ColumnHeadings


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

    ACCENT_ORANGE = 'h202'
    _ACCENT_ORANGE = 'light red'
    BACKGROUND_BLUE = 'h17'
    _BACKGROUND_BLUE = 'black'
    DARK_BLUE = 'h24'
    _DARK_BLUE = 'light blue'
    LIGHT_BLUE = 'h31'
    _LIGHT_BLUE = 'dark blue'
    ACCENT_BLUE = 'h74'
    _ACCENT_BLUE = 'dark cyan'
    GREY = 'h188'
    _GREY = 'light gray'
    WHITE = 'h231'
    _WHITE = 'white'

    palette = [
        ('body', _DARK_BLUE, _WHITE, '', DARK_BLUE, WHITE),
        ('body_focus',
         _WHITE, _ACCENT_BLUE, 'underline', DARK_BLUE, ACCENT_BLUE),
        ('popup', _DARK_BLUE, _WHITE, '', DARK_BLUE, WHITE),
        ('head',
         _LIGHT_BLUE, _BACKGROUND_BLUE, 'bold', LIGHT_BLUE, BACKGROUND_BLUE),
        ('head_so',
         _ACCENT_ORANGE, _BACKGROUND_BLUE, 'bold,standout',
         ACCENT_ORANGE, BACKGROUND_BLUE),
        ('resource_bar_empty', _DARK_BLUE, _WHITE, '', DARK_BLUE, WHITE),
        ('resource_bar', _DARK_BLUE, _GREY, '', DARK_BLUE, GREY),
        ('foot',
         _LIGHT_BLUE, _BACKGROUND_BLUE, 'bold', LIGHT_BLUE, BACKGROUND_BLUE),
        ('key',
         _ACCENT_ORANGE, _BACKGROUND_BLUE, 'bold,underline',
         ACCENT_ORANGE, BACKGROUND_BLUE),
    ]

    # Run any check system queries before we start the DatabasePoller and
    # start tracking queries.
    #
    if not conn.get('select @@forward_aggregator_plan_hash as f').f:
        sys.exit("Enable forward_aggregator_plan_hash to use query-top")

    # TODO(awreece) This isn't accurately max memory across the whole cluster.
    max_mem = int(conn.get('select @@maximum_memory as m').m)

    dbpoller = DatabasePoller(conn, args.update_interval)

    resources = ResourceMonitor(args.cores, max_mem)
    column_headings = ColumnHeadings()
    header = urwid.Pile([
        resources,
        urwid.Divider(),
        column_headings
    ])

    qlistbox = QueryListBox()

    footer = urwid.Text([
        ('key', "UP"), ", ", ('key', "DOWN"), ", ",
        ('key', "PAGE UP"), " and ", ('key', "PAGE DOWN"),
        " move view  ",
        ('key', "F#"), " sorts by column ",
        ('key', "Q"), " exits",
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
