from gi.repository import Adw, Gtk

@Gtk.Template(resource_path='/io/github/cacheuseonly/graphite/ui/loading-page.ui')
class LoadingPage(Adw.Bin):
    __gtype_name__ = 'LoadingPage'

    progress_bar = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
