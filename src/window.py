# window.py
#
# Copyright 2025 Yuxuan Luo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later
import re
import os
import pickle
import threading

from gi.repository import Adw
from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import Gio

from .apt_dependency import build_dependency_graph
from .fa2_adjustSize import ForceAtlas2
from .utils import *

from .panel import Panel
from .loading_page import LoadingPage
from .canvas import Canvas
from .search_row import SearchRow

CACHE_PATH = os.path.join(os.getenv('XDG_CACHE_HOME'), 'graphite')
NODE_GRAPH_CACHE = os.path.join(CACHE_PATH, 'node_graph.pkl')
POS_DICT_CACHE = os.path.join(CACHE_PATH, 'pos_dict.pkl')

@Gtk.Template(resource_path='/io/github/cacheuseonly/graphite/ui/window.ui')
class GraphiteWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'GraphiteWindow'

    stack = Gtk.Template.Child()
    search_button = Gtk.Template.Child('search-button')

    overlay_view = Gtk.Template.Child()
    panel: Panel = Gtk.Template.Child()
    content_stack = Gtk.Template.Child()
    loading_page: LoadingPage = Gtk.Template.Child()
    canvas: Canvas = Gtk.Template.Child()

    search_page = Gtk.Template.Child()
    search_bar = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()
    search_results_list = Gtk.Template.Child()

    def search_filter(self, row):
        match = re.search(self.search_entry.get_text(), row.get_title(), re.IGNORECASE)
        return match

    def __init__(self, state, **kwargs):
        super().__init__(**kwargs)
        self.node_graph = None
        self.pos_dict = {}

        self.setting = Gio.Settings.new('io.github.cacheuseonly.graphite.common')

        self.state = state
        self.panel.set_state(self.state)
        self.canvas.set_state(self.state)

        self.state.connect('regenerate-requested', self._on_regenerate_requested)
        self.state.connect('regenerate-progress', self._on_regenerate_progress)
        self.state.connect('regenerate-complete', self._on_regenerate_complete)

        self.search_bar.connect("notify::search-mode-enabled", self._on_search_mode_enabled)
        self.search_results_list.set_filter_func(self.search_filter)

        threading.Thread(target=self.load_data, daemon=True).start()

    def load_data(self):
        self.state.emit('regenerate-progress')

        try:
            with open(NODE_GRAPH_CACHE, 'rb') as f:
                self.node_graph = pickle.load(f)
            with open(POS_DICT_CACHE, 'rb') as f:
                self.pos_dict = pickle.load(f)
        except (FileNotFoundError, pickle.UnpicklingError):
            self.node_graph = build_dependency_graph()

            fa2 = ForceAtlas2(adjustSizes=True,
                              scalingRatio=1,
                              strongGravityMode=self.setting.get_boolean('strong-gravity-mode'),
                              gravity=self.setting.get_double('gravity'),
                              outboundAttractionDistribution=True,
                              verbose=False,
                              )
            self.pos_dict = fa2.forceatlas2_networkx_layout(self.node_graph,
                                                            iterations=self.setting.get_int('iterations'),
                                                            progress_bar=self.loading_page.progress_bar
                                                            )

            os.makedirs(CACHE_PATH, exist_ok=True)
            with open(NODE_GRAPH_CACHE, 'wb') as f:
                pickle.dump(self.node_graph, f)
            with open(POS_DICT_CACHE, 'wb') as f:
                pickle.dump(self.pos_dict, f)

        for node in self.node_graph.nodes:
            self.search_results_list.append(SearchRow(
                node,
                get_pkg_name_from_node(node),
                get_pkg_version_from_node(node)
            ))

        GLib.idle_add(self.on_loading_complete)

    def on_loading_complete(self):
        self.canvas.set_data(self.node_graph, self.pos_dict)
        self.panel.set_node_graph(self.node_graph)
        self.content_stack.set_visible_child(self.canvas)
        self.state.emit('regenerate-complete')

        return False

    def _on_regenerate_requested(self, _):
        self.content_stack.set_visible_child(self.loading_page)
        self.state.selected_node = None
        self.state.hovered_node = None

        os.remove(os.path.join(CACHE_PATH, 'node_graph.pkl'))
        os.remove(os.path.join(CACHE_PATH, 'pos_dict.pkl'))

        threading.Thread(target=self.load_data, daemon=True).start()

    def _on_regenerate_progress(self, _state):
        self.search_button.set_sensitive(False)

    def _on_regenerate_complete(self, _state):
        self.search_button.set_sensitive(True)

    @Gtk.Template.Callback()
    def _on_collapse_clicked(self, _button):
        """Toggle sidebar collapse state"""
        is_collapsed = self.overlay_view.get_collapsed()
        self.overlay_view.set_collapsed(not is_collapsed)

    @Gtk.Template.Callback()
    def _on_search_clicked(self, button):
        """Toggle search bar visibility"""
        is_active = button.get_active()
        self.search_bar.set_search_mode(is_active)

    @Gtk.Template.Callback()
    def _on_search_changed(self, search_entry):
        """Handle search text changes"""
        self.search_results_list.invalidate_filter()

    @Gtk.Template.Callback()
    def _on_search_result_activated(self, _listbox, row):
        self.state.selected_node = row.pkg_node
        self.search_entry.emit('stop-search')

    def _on_search_mode_enabled(self, search_bar, _):
        # If search bar is dismissed by pressing ESC, toggle search button as
        # well
        is_enabled = search_bar.get_search_mode()
        if is_enabled:
            self.stack.set_visible_child(self.search_page)
        else:
            self.stack.set_visible_child(self.overlay_view)
            if self.search_button.get_active():
                self.search_button.set_active(False)
