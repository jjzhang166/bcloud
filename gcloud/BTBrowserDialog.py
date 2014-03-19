
# Copyright (C) 2014 LiuLang <gsushzhsosgsu@gmail.com>
# Use of this source code is governed by GPLv3 license that can be found
# in http://www.gnu.org/licenses/gpl-3.0.html

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Pango

CHECK_COL, NAME_COL, SIZE_COL, HUMANSIZE_COL = list(range(4))
from gcloud import Config
_ = Config._
from gcloud import gutil
from gcloud import pcs
from gcloud import util


class BTBrowserDialog(Gtk.Dialog):

    file_sha1 = ''

    def __init__(self, parent, app, title, source_path):
        '''初始化BT种子查询对话框.

        source_path - 如果是BT种子的话, 就是种子的绝对路径.
                      如果是磁链的话, 就是以magent:开头的磁链链接.
        '''
        super().__init__(
            title, app.window, Gtk.DialogFlags.MODAL,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.app = app
        self.source_path = source_path

        self.set_default_size(520, 480)
        self.set_border_width(10)
        box = self.get_content_area()

        select_all_button = Gtk.ToggleButton(_('Select All'))
        select_all_button.props.halign = Gtk.Align.START
        select_all_button.props.margin_bottom = 5
        select_all_button.connect('toggled', self.on_select_all_toggled)
        box.pack_start(select_all_button, False, False, 0)

        scrolled_win = Gtk.ScrolledWindow()
        box.pack_start(scrolled_win, True, True, 0)

        # check, name, size, humansize
        self.liststore = Gtk.ListStore(bool, str, GObject.TYPE_LONG, str)
        self.treeview = Gtk.TreeView(model=self.liststore)
        scrolled_win.add(self.treeview)
        check_cell = Gtk.CellRendererToggle()
        check_cell.connect('toggled', self.on_check_cell_toggled)
        check_col = Gtk.TreeViewColumn(
            _('Check'), check_cell, active=CHECK_COL)
        self.treeview.append_column(check_col)
        name_cell = Gtk.CellRendererText(
                ellipsize=Pango.EllipsizeMode.END, ellipsize_set=True)
        name_col = Gtk.TreeViewColumn(_('Name'), name_cell, text=NAME_COL)
        name_col.set_expand(True)
        self.treeview.append_column(name_col)
        size_cell = Gtk.CellRendererText()
        size_col = Gtk.TreeViewColumn(
            _('Size'), size_cell, text=HUMANSIZE_COL)
        self.treeview.append_column(size_col)

        box.show_all()
        self.request_data()

    def request_data(self):
        '''在调用dialog.run()之前先调用这个函数来获取数据'''
        def on_tasks_received(info, error=None):
            if error or not info:
                return
            if 'magnet_info' in info:
                tasks = info['magnet_info']
            elif 'torrent_info' in info:
                tasks = info['torrent_info']['file_info']
                self.file_sha1 = info['torrent_info']['sha1']
            else:
                print('tasks is null:', info)
                return
            for task in tasks:
                human_size, _ = util.get_human_size(int(task['size']))
                self.liststore.append([
                    False,
                    task['file_name'],
                    int(task['size']),
                    human_size,
                    ])

        if self.source_path.startswith('magnet'):
            gutil.async_call(
                pcs.cloud_query_magnetinfo, self.app.cookie,
                self.app.tokens, self.source_path, '/',
                callback=on_tasks_received)
        else:
            gutil.async_call(
                pcs.cloud_query_sinfo, self.app.cookie, self.app.tokens,
                self.source_path, '/', callback=on_tasks_received)

    def get_selected(self):
        '''返回选中要下载的文件的编号及sha1值, 从1开始计数.'''
        selected_idx = []
        for i, row in enumerate(self.liststore):
            if row[CHECK_COL]:
                selected_idx.append(i + 1)
        return (selected_idx, self.file_sha1)

    def on_select_all_toggled(self, button):
        status = button.get_active()
        for row in self.liststore:
            row[CHECK_COL] = status

    def on_check_cell_toggled(self, cell, tree_path):
        self.liststore[tree_path][CHECK_COL] = not self.liststore[tree_path][CHECK_COL]