from gi.repository import Gtk, Adw, Gio

@Gtk.Template(resource_path='/io/github/cacheuseonly/graphite/ui/preferences.ui')
class Preferences(Adw.PreferencesDialog):
    __gtype_name__ = 'Preferences'

    iterations = Gtk.Template.Child()
    gravity = Gtk.Template.Child()
    strong_gravity_mode = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.settings = Gio.Settings.new('io.github.cacheuseonly.graphite.common')

        self.settings.bind(
            'iterations',
            self.iterations,
            'value',
            Gio.SettingsBindFlags.DEFAULT
        )
        self.settings.bind(
            'gravity',
            self.gravity,
            'value',
            Gio.SettingsBindFlags.DEFAULT
        )
        self.settings.bind(
            'strong-gravity-mode',
            self.strong_gravity_mode,
            'active',
            Gio.SettingsBindFlags.DEFAULT
        )
