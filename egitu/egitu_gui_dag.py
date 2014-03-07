#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2014 Davide Andreoli <dave@gurumeditation.it>
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

import os
import sys
from datetime import datetime

from efl import elementary
from efl.edje import Edje
from efl.elementary.entry import Entry, ELM_WRAP_NONE
from efl.elementary.table import Table
from efl.elementary.frame import Frame
from efl.elementary.layout import Layout

from egitu_utils import options, theme_resource_get, format_date, \
    GravatarPict, EXPAND_BOTH, FILL_BOTH
from egitu_vcs import Commit



class CommitPopup(Table):
    def __init__(self, parent, repo, commit):
        self.repo = repo
        self.commit = commit

        Table.__init__(self, parent,  padding=(5,5))
        self.show()

        pic = GravatarPict(self)
        pic.email_set(commit.author_email)
        self.pack(pic, 0, 0, 1, 1)
        pic.show()

        text = ''
        if commit.author and commit.commit_date:
            date = format_date(commit.commit_date)
            text += '{} @ {}<br>'.format(commit.author, date)
        if commit.title:
            text += '<b>{}</b><br>'.format(commit.title)
        if commit.sha:
            text += '{}<br>'.format(commit.sha[:7])
        en = Entry(self, text=text)
        en.line_wrap = ELM_WRAP_NONE
        en.size_hint_weight = EXPAND_BOTH
        en.size_hint_align = FILL_BOTH
        self.pack(en, 1, 0, 1, 1)
        en.show()


class DagGraph(Table):
    def __init__(self, parent, *args, **kargs):
        self.repo = None
        self.win = parent
        self.themef = theme_resource_get('main.edj')
        # self.points = []
        # self.lines = []
        self._cols = [(), (100,0,0,100), (0,100,0,100), (0,0,100,100),
                          (100,0,0,100), (0,100,0,100), (0,0,100,100)]
        
        Table.__init__(self, parent, homogeneous=False, padding=(0,0))

    def populate(self, repo):
        self.repo = repo
        self._col = self._row = 1
        self._open_connections = {}
        self._first_commit = None

        self.clear(True)

        # first col for the date (TODO)
        from efl.evas import Line, Rectangle
        l = Rectangle(self.evas, color=(0,0,0,100))
        l.size_hint_min = 20, 20
        l.size_hint_align = FILL_BOTH
        self.pack(l, 0, 0, 1, 100)
        l.show()

        # first row for something else (branch names?) (TODO)
        # l = Rectangle(self.evas, color=(0,0,0,100))
        # l.size_hint_min = 20, 20
        # l.size_hint_align = FILL_BOTH
        # self.pack(l, 1, 0, 10, 1)
        # l.show()

        # create the first fake commit (local changes)
        if not self.repo.status.is_clean:
            c = Commit()
            c.title = "Local changes"
            c.tags = ['Local changes']
            self.point_add(c, self._col, self._row)
            # self.connection_add(1, 1, 1, 2)
            self._row += 1
            self._col -= 1
            self._first_commit = c

        self.repo.request_commits(self._populate_done_cb, self._populate_prog_cb, 100)

    def _populate_prog_cb(self, commit):
        if self._row == 1:
            self._first_commit = commit

        # 1. draw the connection if there are 'open-to' this one
        if commit.sha in self._open_connections:
            R = self._open_connections.pop(commit.sha)
            min_col = min([c[2] for c in R])
            self._col = min_col
            for child_col, child_row, new_col in R:
                self.connection_add(child_col, child_row, self._col, self._row)
        else:
            self._col += 1

        # 2. add an open_connection, one for each parent
        i = 0
        for parent in commit.parents:
            r = (self._col, self._row, self._col + i)
            if parent in self._open_connections:
                self._open_connections[parent].append(r)
            else:
                self._open_connections[parent] = [r]
            i += 1

        # 3. add the commit point
        self.point_add(commit, self._col, self._row)
        self._row += 1

    def _populate_done_cb(self):
        if self._first_commit is not None:
            self.win.show_commit(self._first_commit)

    def point_add(self, commit, col, row):
        p = Layout(self, file=(self.themef,'egitu/graph/item'))
        p.edje.signal_callback_add("mouse,down,*", "base",
                                   self.point_mouse_down_cb, commit)
        p.tooltip_content_cb_set(lambda o,tt:
                CommitPopup(self, self.repo, commit))

        if options.show_message_in_dag is True:
            l = Layout(self, file=(self.themef, 'egitu/graph/msg'))
            l.text_set('msg.text', commit.title)
            p.box_append('refs.box', l)
            l.show()

        for head in commit.heads:
            if head == 'HEAD':
                p.signal_emit('head,show', 'egitu')
            else:
                l = Layout(self, file=(self.themef, 'egitu/graph/ref'))
                l.text_set('ref.text', head)
                p.box_append('refs.box', l)
                l.show()

        if options.show_remotes_in_dag:
            for head in commit.remotes:
                l = Layout(self, file=(self.themef, 'egitu/graph/ref'))
                l.text_set('ref.text', head)
                p.box_append('refs.box', l)
                l.show()
                
        for tag in commit.tags:
            l = Layout(self, file=(self.themef, 'egitu/graph/tag'))
            l.text_set('tag.text', tag)
            p.box_append('refs.box', l)
            l.show()

        self.pack(p, col, row, 1, 1)
        p.show()

    def connection_add(self, col1, row1, col2, row2):
        # print ("CONNECTION", col1, row1, col2, row2)
        if col1 == col2:
            # a stright line
            l = Edje(self.evas, file=self.themef, size_hint_align=FILL_BOTH,
                    group='egitu/graph/connection/vert', color=self._cols[col1])
            self.pack(l, col1, row1, col2 - col1 + 1, row2 - row1 + 1)
            
        elif col1 > col2:
            # a "fork"
            l = Edje(self.evas, file=self.themef, size_hint_align=FILL_BOTH,
                    group='egitu/graph/connection/vert_fork', color=self._cols[col2])
            self.pack(l, col2, row1, col1 - col2 + 1, row2 - row1 + 1)
        else:
            # a "merge"
            l = Edje(self.evas, file=self.themef, size_hint_align=FILL_BOTH,
                    group='egitu/graph/connection/vert_merge', color=self._cols[col2])
            self.pack(l, col1, row1, col2 - col1 + 1, row2 - row1 + 1)

        l.lower()
        l.show()

    def point_mouse_down_cb(self, obj, signal, source, commit):
        self.win.show_commit(commit)
        print(commit)
