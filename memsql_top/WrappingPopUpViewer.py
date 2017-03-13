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

class PopUpDialog(urwid.WidgetWrap):
    signals = ['close']

    def __init__(self, message):
        listbox = urwid.ListBox(urwid.SimpleListWalker([
            urwid.Text(line) for line in message.split("\n")
        ]))
        footer = urwid.Pile([
            urwid.Divider(),
            urwid.Text("<close>")
        ])
        self.box = urwid.LineBox(urwid.Frame(listbox, footer=footer))
        super(PopUpDialog, self).__init__(urwid.AttrMap(self.box, 'popup'))

    def keypress(self, size, key):
       if self._command_map[key] != ACTIVATE and key != 'q':
           return self.box.keypress(size, key)

       self._emit("close")


class WrappingPopUpViewer(urwid.WidgetWrap):
    """
    Normally wraps orig_widget, but if show_popup is called will display
    a popup overlayed over orig_widget until the popup is closed.
    """
    def __init__(self, orig_widget):
        self.orig_widget = orig_widget
        super(WrappingPopUpViewer, self).__init__(self.orig_widget)

    def show_popup(self, _, text):
        popup = PopUpDialog(text)
        urwid.connect_signal(popup, "close", self.close_popup)
        self._w = urwid.Overlay(popup, self.orig_widget,
                                align="center", width=("relative", 70),
                                valign="middle", height=("relative", 70))

    def close_popup(self, _):
        self._w = self.orig_widget
