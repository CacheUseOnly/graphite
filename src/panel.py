from gi.repository import Adw
from gi.repository import Gtk
from gi.repository import GObject

from .state_manager import GraphState
from .utils import *

@Gtk.Template(resource_path='/io/github/cacheuseonly/graphite/ui/panel.ui')
class Panel(Adw.Bin):
    __gtype_name__ = 'Panel'

    header_label = Gtk.Template.Child()
    version_row = Gtk.Template.Child()
    arch_row = Gtk.Template.Child()
    manual_row = Gtk.Template.Child()
    deps_group = Gtk.Template.Child()
    deps_list = Gtk.Template.Child()
    reverse_deps_group = Gtk.Template.Child()
    reverse_deps_list = Gtk.Template.Child()

    def __init__(self):
        super().__init__()

        self.state = None
        self.node_graph = None

    def set_state(self, state: GraphState):
        self.state = state
        self.state.connect('node-selected', self._on_node_selected)
        self.state.connect('node-deselected', self._on_node_deselected)

    def set_node_graph(self, node_graph):
        """Set the node graph and update the panel"""
        self.node_graph = node_graph

        # Clear existing lists
        self.deps_list.remove_all()
        self.reverse_deps_list.remove_all()

        # Reset header
        self.header_label.set_text("-")
        self.version_row.set_label("-")
        self.arch_row.set_label("-")
        self.manual_row.set_label("-")
        self.deps_list.remove_all()
        self.deps_group.set_description("0")
        self.reverse_deps_list.remove_all()
        self.reverse_deps_group.set_description("0")

    def _on_goto_clicked(self, node: str):
        """Handler for when a goto button is clicked"""
        self.state.selected_node = node

    def _on_node_selected(self, _state, node: str):
        name = get_pkg_name_from_node(node)
        version = get_pkg_version_from_node(node)
        arch = get_pkg_arch_from_node(node)
        manual = 'Manual' if self.node_graph.nodes[node].get('manual', False) else 'Auto'

        self.header_label.set_markup(f"<b>{name}</b>")
        self.version_row.set_label(version)
        self.arch_row.set_label(arch)
        self.manual_row.set_label(manual)

        # Update dependencies list
        self.deps_list.remove_all()
        deps = list(self.node_graph.neighbors(node))
        self.deps_group.set_description(str(len(deps)))
        for dep in deps:
            row = Adw.ActionRow(
                title=get_pkg_name_from_node(dep),
                subtitle=get_pkg_version_from_node(dep),
                title_selectable=True,
            )
            button = Gtk.Button(icon_name="go-next-symbolic", valign=Gtk.Align.CENTER)
            button.add_css_class("flat")
            button.connect("clicked", lambda btn, n=dep: self._on_goto_clicked(n))
            row.add_suffix(button)
            self.deps_list.append(row)

        # Update reverse dependencies list
        self.reverse_deps_list.remove_all()
        rev_deps = list(self.node_graph.predecessors(node))
        self.reverse_deps_group.set_description(str(len(rev_deps)))
        for rev_dep in rev_deps:
            row = Adw.ActionRow(
                title=get_pkg_name_from_node(rev_dep),
                subtitle=get_pkg_version_from_node(rev_dep),
                title_selectable=True,
            )
            button = Gtk.Button(icon_name="go-next-symbolic", valign=Gtk.Align.CENTER)
            button.add_css_class("flat")
            button.connect("clicked", lambda btn, n=rev_dep: self._on_goto_clicked(n))
            row.add_suffix(button)
            self.reverse_deps_list.append(row)

    def _on_node_deselected(self, _state):
        self.header_label.set_text("-")
        self.version_row.set_label("-")
        self.arch_row.set_label("-")
        self.manual_row.set_label("-")
        self.deps_list.remove_all()
        self.deps_group.set_description("0")
        self.reverse_deps_list.remove_all()
        self.reverse_deps_group.set_description("0")
