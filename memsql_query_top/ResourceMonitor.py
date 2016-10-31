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


class ResourceMonitor(urwid.WidgetWrap):
    def __init__(self, num_cores, max_mem):
        self.cpu_utilbar = urwid.ProgressBar('resource_bar_empty',
                                             'resource_bar', done=num_cores)
        self.mem_utilbar = urwid.ProgressBar('resource_bar_empty',
                                             'resource_bar', done=max_mem)

        super(ResourceMonitor, self).__init__(urwid.Pile([
            urwid.Columns([
                urwid.Text("CPU"),
                urwid.Divider(),
                urwid.Divider(),
                urwid.Text("Memory"),
                urwid.Divider(" "),
            ]),
            urwid.Columns([
                urwid.Text("Util"),
                self.cpu_utilbar,
                urwid.Divider(),
                urwid.Text("Util"),
                self.mem_utilbar
            ]),
            urwid.Columns([
                urwid.Text("Sched Latency"),
                urwid.ProgressBar('resource_bar_empty', 'resource_bar'),
                urwid.Divider(),
                urwid.Text("Paging"),
                urwid.ProgressBar('resource_bar_empty', 'resource_bar'),
            ])
        ]))

    def update_cpu_util(self, _, util):
        self.cpu_utilbar.set_completion(util)

    def update_mem_usage(self, _, usage):
        self.mem_utilbar.set_completion(usage)
