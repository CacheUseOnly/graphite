# main.py
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

import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gio, Adw
from .window import GraphiteWindow
from .state_manager import GraphState
from .preferences import Preferences

class GraphiteApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self, appid):
        super().__init__(application_id=appid,
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.state = GraphState()
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action, ['<primary>comma'])
        self.create_action('regenerate', lambda *_: self.state.emit('regenerate-requested'), ['<primary>r'])

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = GraphiteWindow(application=self,
                                 state=self.state
                                 )
        win.present()

    def on_about_action(self, widget, _):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(application_name='Graphite',
                                application_icon='io.github.cacheuseonly.graphite',
                                developer_name='Yuxuan Luo',
                                version='1.0',
                                developers=['Yuxuan Luo'],
                                artists=['Anzhi Li'],
                                copyright='© 2025 Yuxuan Luo')
        about.present()

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        preferences = Preferences()
        preferences.present()

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version, appid):
    """The application's entry point."""
    app = GraphiteApplication(appid=appid)
    return app.run(sys.argv)
