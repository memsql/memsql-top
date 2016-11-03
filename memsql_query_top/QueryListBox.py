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

from urwid.command_map import ACTIVATE
from columns import COLUMNS, DEFAULT_SORT_COLUMN, GetColumnWidth


class QueryRow(urwid.AttrMap):
    signals = ['click']

    def __init__(self, **kwargs):
        self.PlanId = kwargs['PlanId']
        columns = []
        self.fields = {}
        self.widgets = {}
        for name, meta in COLUMNS.items():
            t = urwid.Text(meta.humanize(kwargs[name]), wrap="clip")
            self.widgets[name] = t
            self.fields[name] = kwargs[name]

            if meta.fixed_width:
                columns.append((GetColumnWidth(name), t))
            else:
                columns.append(t)

        content = urwid.Columns(columns, dividechars=1)
        super(QueryRow, self).__init__(content, "body", "body_focus")

    def selectable(self):
        return True

    def keypress(self, size, key):
        if self._command_map[key] != ACTIVATE:
            return key

        self._emit("click")

    def update(self, **kwargs):
        for name, meta in COLUMNS.items():
            self.widgets[name].set_text(meta.humanize(kwargs[name]))
            self.fields[name] = kwargs[name]


class QueryListBox(urwid.ListBox):
    signals = ['sort_column_changed', 'query_selected']

    def __init__(self):
        self.qrlist = urwid.SimpleFocusListWalker([])
        self.widgets = {}
        self.sort_column = DEFAULT_SORT_COLUMN
        self.sort_keys_map = {c.sort_key: name for name, c in COLUMNS.items()}
        super(QueryListBox, self).__init__(self.qrlist)

    def sort_columns(self):
        self.qrlist.sort(key=lambda qr: qr.fields[self.sort_column],
                         reverse=True)

    def sort_keys(self):
        return self.sort_keys_map.keys()

    def update_sort_column(self, key):
        self.sort_column = self.sort_keys_map[key]
        self.sort_columns()
        self._emit('sort_column_changed', self.sort_column)

    def update_entries(self, _, diff_plancache):
        # Remove entries that become obsolete
        remove = [k for k in self.widgets if k not in diff_plancache]
        for qr in remove:
            self.qrlist.remove(self.widgets[qr])
            del self.widgets[qr]

        for key, ent in diff_plancache.items():
            if key not in self.widgets:
                self.widgets[key] = QueryRow(**ent)
                #
                # TODO: Does this prevent the widget from being garbage
                # collected?
                #
                urwid.connect_signal(self.widgets[key], 'click',
                                     lambda qr: self._emit("query_selected",
                                                           qr.fields['Query']))
                self.qrlist.append(self.widgets[key])
            else:
                self.widgets[key].update(**ent)

        self.sort_columns()