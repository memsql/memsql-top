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
import logging
import sys

import database

from DatabasePoller import DatabasePoller
from QueryListBox import QueryListBox
from ResourceMonitor import ResourceMonitor
from WrappingPopUpViewer import WrappingPopUpViewer
from ColumnHeadings import ColumnHeadings

from distutils.version import LooseVersion

from columns import DetectColumnsMetaOrExit

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=3306, type=int)
    parser.add_argument("--password", default="")
    parser.add_argument("--user", default="root")

    parser.add_argument("--update-interval", default=3.0, type=float,
	                help="How frequently to update the screen.")

    args = parser.parse_args()

    try:
	conn = database.connect(host=args.host, port=args.port,
				database="information_schema",
				password=args.password, user=args.user)
    except Exception as e:
	sys.exit("Unexpected error when connecting to database: %s" % e)

    columnsMeta = DetectColumnsMetaOrExit(conn)

    # Run any check system queries before we start the DatabasePoller and
    # start tracking queries.
    #
    if not conn.get('select @@forward_aggregator_plan_hash as f').f:
        sys.exit("forward_aggregator_plan_hash is required")

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

    dbpoller = DatabasePoller(conn, args.update_interval, columnsMeta)

    column_headings = ColumnHeadings(columnsMeta)
    resources = ResourceMonitor(columnsMeta.GetMaxCpuTotal(conn),
                                columnsMeta.GetMaxMemTotal(conn))
    headerElems = [urwid.Text("MemSQL - MemSQL Top")]

    # 5.7 did not give us enough info for resource bars.
    if columnsMeta.minimum_version >= LooseVersion("5.8"):
        headerElems  += [urwid.Divider(), resources]
    headerElems += [urwid.Divider(), column_headings]
    header = urwid.Pile(headerElems)

    qlistbox = QueryListBox(columnsMeta)

    footer = urwid.Columns([
        urwid.Text([
            ('foot_key', "UP"), ", ", ('foot_key', "DOWN"), ", ",
            " move view  ",
            ('foot_key', "F#"), " sorts by column ",
            ('foot_key', "Q"), " exits",
        ]),
        urwid.Text("Send feedback to help@memsql.com.", align="right")
    ])

    view = WrappingPopUpViewer(urwid.Frame(
        urwid.AttrMap(qlistbox, "body"),
        header=urwid.AttrMap(header, "head"),
        footer=urwid.AttrMap(footer, "foot")))

    urwid.connect_signal(qlistbox, 'sort_column_changed',
                         column_headings.update_sort_column)
    urwid.connect_signal(qlistbox, 'query_selected',
                         lambda w, q: view.show_popup(w, columnsMeta.GetPopUpText(conn, q)))

    def handle_keys(input):
        if input in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        if input in qlistbox.sort_keys():
            qlistbox.update_sort_column(input)

    loop = urwid.MainLoop(view, palette, unhandled_input=handle_keys)
    def update_widgets(plancache, cpu, mem):
        qlistbox.update_entries(plancache)
        resources.update_cpu_util(cpu)
        resources.update_mem_usage(mem)
    dbpoller.start(loop.watch_pipe(lambda _:
        update_widgets(*dbpoller.get_database_data())))

    try:
        curses.setupterm()
        if curses.tigetnum("colors") == 256:
            loop.screen.set_terminal_properties(colors=256)
    except curses.error:
        logging.warn("Failed to identify terminal color support -- falling back to ANSI terminal colors.")
        logging.warn("Set TERM=xterm-256color or equivalent for best the experience.")
    loop.run()


if __name__ == "__main__":
    main()
