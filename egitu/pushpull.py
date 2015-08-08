#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2014-2015 Davide Andreoli <dave@gurumeditation.it>
#
# This file is part of Egitu.
#
# Egitu is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# Egitu is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Egitu.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import

from efl.evas import Rectangle
from efl.elementary.entry import Entry, utf8_to_markup, ELM_WRAP_NONE
from efl.elementary.button import Button
from efl.elementary.separator import Separator
from efl.elementary.popup import Popup
from efl.elementary.table import Table
from efl.elementary.label import Label
from efl.elementary.icon import Icon
from efl.elementary.progressbar import Progressbar

from egitu.utils import theme_resource_get, \
    EXPAND_BOTH, FILL_BOTH, EXPAND_HORIZ, FILL_HORIZ


class PullPopup(Popup):
    def __init__(self, parent, repo):
        self.repo = repo

        Popup.__init__(self, parent)
        self.part_text_set('title,text', 'Fetch changes (pull)')
        self.part_content_set('title,icon',
                              Icon(self, file=theme_resource_get('pull.png')))

        tb = Table(self, padding=(0,4), size_hint_expand=EXPAND_BOTH)
        self.content = tb
        tb.show()

        # sep
        sep = Separator(self, horizontal=True, size_hint_expand=EXPAND_BOTH)
        tb.pack(sep, 0, 0, 2, 1)
        sep.show()

        # remote url
        lb = Label(tb, text='<align=left>Remote</align>',
                   size_hint_fill=FILL_BOTH)
        tb.pack(lb, 0, 1, 1, 1)
        lb.show()

        en = Entry(tb, editable=True, single_line=True, scrollable=True,
                   size_hint_expand=EXPAND_BOTH, size_hint_fill=FILL_BOTH)
        en.part_text_set('guide', 'Where to fetch from (TODO)')
        tb.pack(en, 1, 1, 1, 1)
        en.show()

        # remote branch
        lb = Label(tb, text='<align=left>Remote branch  </align>',
                   size_hint_fill=FILL_BOTH)
        tb.pack(lb, 0, 2, 1, 1)
        lb.show()

        en = Entry(tb, editable=True, single_line=True, scrollable=True,
                   size_hint_expand=EXPAND_BOTH, size_hint_fill=FILL_BOTH)
        en.part_text_set('guide', 'The remote branch to fetch (TODO)')
        tb.pack(en, 1, 2, 1, 1)
        en.show()

        # local branch
        lb = Label(tb, text='<align=left>Local branch</align>',
                   size_hint_fill=FILL_BOTH)
        tb.pack(lb, 0, 3, 1, 1)
        lb.show()

        en = Entry(tb, editable=False, single_line=True, scrollable=True,
                   text=repo.current_branch,
                   size_hint_expand=EXPAND_BOTH, size_hint_fill=FILL_BOTH)
        tb.pack(en, 1, 3, 1, 1)
        en.show()

        # output entry
        en = Entry(tb, scrollable=True, editable=False, line_wrap=ELM_WRAP_NONE,
                   size_hint_expand=EXPAND_BOTH, size_hint_fill=FILL_BOTH)
        tb.pack(en, 0, 4, 2, 1)
        en.show()
        self.output_entry = en

        r = Rectangle(tb.evas, size_hint_min=(400,200),
                      size_hint_expand=EXPAND_BOTH)
        tb.pack(r, 0, 4, 2, 1)

        # progress wheel
        pb = Progressbar(self, style='wheel', pulse_mode=True,
                         size_hint_expand=EXPAND_BOTH)
        tb.pack(pb, 0, 4, 2, 1)
        self.wheel = pb

        # sep
        sep = Separator(self, horizontal=True, size_hint_expand=EXPAND_BOTH)
        tb.pack(sep, 0, 5, 2, 1)
        sep.show()

        # buttons
        bt = Button(self, text='Close')
        bt.callback_clicked_add(lambda b: self.delete())
        self.part_content_set('button1', bt)
        bt.show()
        self.close_btn = bt

        bt = Button(self, text='Pull')
        bt.callback_clicked_add(self._pull_btn_cb)
        self.part_content_set('button2', bt)
        bt.show()
        self.pull_btn = bt

        self.show()

    def start_pulse(self):
        self.wheel.pulse(True)
        self.wheel.show()
        self.pull_btn.disabled = True
        self.close_btn.disabled = True

    def stop_pulse(self):
        self.wheel.pulse(False)
        self.wheel.hide()
        self.pull_btn.disabled = False
        self.close_btn.disabled = False

    def _pull_btn_cb(self, btn):
        self.start_pulse()
        self.repo.pull(self._pull_done_cb, self._pull_progress_cb)

    def _pull_progress_cb(self, line):
        self.output_entry.entry_append(line + '<br>')
        self.output_entry.cursor_end_set()

    def _pull_done_cb(self, success, err_msg=None):
        self.stop_pulse()
        self.parent.refresh()
