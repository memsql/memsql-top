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

from collections import OrderedDict
from columns import COLUMNS, DEFAULT_SORT_COLUMN, GetColumnWidth


class SortableColumn(urwid.AttrMap):
    def __init__(self, content, attr_class, is_sort_column=False):
        self.attr_class = attr_class
        self.is_sort_column = is_sort_column

        super(SortableColumn, self).__init__(content,
                                             self.get_attr_name(focus=False),
                                             self.get_attr_name(focus=True))

    def get_attr_name(self, focus=False):
        return "%s%s%s" % (
            self.attr_class,
            "_so" if self.is_sort_column else "",
            "_focus" if focus else ""
        )

    def update_sort_column(self, is_sort_column):
        if self.is_sort_column ^ is_sort_column:
            self.is_sort_column = is_sort_column
            self.set_attr_map({None: self.get_attr_name(focus=False)})
            self.set_focus_map({None: self.get_attr_name(focus=True)})


class ColumnHeadings(urwid.Columns):
    def __init__(self):
        self.columns = OrderedDict()
        columns = []
        for name, meta in COLUMNS.items():
            contents = name
            if meta.sort_key:
                contents = [name, ' ', ('head_key', "(%s)" % meta.sort_key.upper())]

            contents = urwid.Text(contents, wrap="clip")
            contents = SortableColumn(contents, 'head')
            self.columns[name] = contents
            if meta.fixed_width:
                assert (contents.original_widget.pack()[0] <=
                        GetColumnWidth(name))
                columns.append((len(name) + len(" (F#)"), contents))
            else:
                columns.append(contents)
        self.sort_column = DEFAULT_SORT_COLUMN
        self.columns[self.sort_column].update_sort_column(True)
        super(ColumnHeadings, self).__init__(columns, dividechars=1)

    def update_sort_column(self, _, sort_column):
        assert sort_column in self.columns
        self.columns[self.sort_column].update_sort_column(False)
        self.sort_column = sort_column
        self.columns[self.sort_column].update_sort_column(True)
