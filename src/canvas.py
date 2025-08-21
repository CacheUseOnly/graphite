import math

import cairo
from gi.repository import Gtk, Adw, Gdk, Gio

from .utils import *
from .state_manager import GraphState

SCALE_MIN = 0.1
SCALE_MAX = 10.0
SCALE_STEP = 0.1

@Gtk.Template(resource_path='/io/github/cacheuseonly/graphite/ui/canvas.ui')
class Canvas(Adw.Bin):
    __gtype_name__ = 'Canvas'

    x_translate = None
    y_translate = None
    x_drag_start = 0
    y_drag_start = 0
    x_cursor = 0
    y_cursor = 0
    scale = 1.0

    is_dragging = False

    node_graph = None
    pos_dict = None
    orig_pos_dict = None
    state = None

    colors = {}

    normal_edges = set()
    outward_edges = set()
    inward_edges = set()
    dimmed_nodes = set()
    normal_nodes = set()

    drawing_area = Gtk.Template.Child()
    legend_drawing_area = Gtk.Template.Child()
    label_popover = Gtk.Template.Child()
    pkg_name_label = Gtk.Template.Child()

    def __init__(self):
        super().__init__()

        self.drawing_area.set_draw_func(self.draw_func)
        self.legend_drawing_area.set_draw_func(self.draw_legend)

        self.default_cursor = Gdk.Cursor.new_from_name("default")
        self.hand_cursor = Gdk.Cursor.new_from_name("pointer")
        self.move_cursor = Gdk.Cursor.new_from_name("move")
        self.drawing_area.set_cursor(self.default_cursor)

        self.appearance_settings = Gio.Settings.new("io.github.cacheuseonly.graphite.appearance")
        self.style_manager = Adw.StyleManager()
        self.style_manager.connect("notify::dark", self.load_theme_colors)

        self.load_theme_colors()
        self._setup_controllers()

    def draw_legend(self, widget, cr: cairo.Context, width, height):
        def _draw_legend_node(cr: cairo.Context, x: float, y: float, node_type: str):
            # Get color for node type
            color_key = f"{node_type}-node-color"
            color = self.colors[color_key]
            cr.set_source_rgb(color[0]/255, color[1]/255, color[2]/255)

            # Draw circle
            cr.new_sub_path()
            radius = 8
            cr.arc(x, y, radius, 0, 2 * math.pi)
            cr.fill()

        def _draw_legend_edge(cr: cairo.Context, x1: float, y1: float, x2: float, y2: float, 
                            color: tuple, arrow_left: bool = False, arrow_right: bool = False):

            def _draw_legend_arrow(cr: cairo.Context, x: float, y: float, angle: float):
                """Draw an arrow head at the specified position and angle"""
                arrow_length = 8
                arrow_angle = math.pi / 6  # 30 degrees

                # Draw arrow head
                cr.move_to(x, y)
                cr.line_to(x - arrow_length * math.cos(angle - arrow_angle),
                        y - arrow_length * math.sin(angle - arrow_angle))
                cr.move_to(x, y)
                cr.line_to(x - arrow_length * math.cos(angle + arrow_angle),
                        y - arrow_length * math.sin(angle + arrow_angle))
                cr.stroke()

            cr.set_source_rgb(color[0]/255, color[1]/255, color[2]/255)
            cr.set_line_width(2)
            cr.move_to(x1, y1)
            cr.line_to(x2, y2)
            cr.stroke()

            # Draw arrow
            if arrow_left:
                _draw_legend_arrow(cr, x1, y1, math.pi)  # Point left
            elif arrow_right:
                _draw_legend_arrow(cr, x2, y2, 0)  # Point right

        margin = 10
        item_spacing = 25
        y_pos = margin

        # Draw manual node example
        _draw_legend_node(cr, margin + 15, y_pos, "manual")
        y_pos += item_spacing

        # Draw auto node example
        _draw_legend_node(cr, margin + 15, y_pos, "auto")
        y_pos += item_spacing

        # Draw inward edge example (arrow pointing left)
        _draw_legend_edge(cr, margin + 5, y_pos, margin + 35, y_pos,
                          self.colors['inward-edge-color'], arrow_left=True)
        y_pos += item_spacing

        # Draw outward edge example (arrow pointing right)
        _draw_legend_edge(cr, margin + 5, y_pos, margin + 35, y_pos,
                              self.colors['outward-edge-color'], arrow_right=True)

    def set_state(self, state: GraphState):
        self.state = state
        self.state.connect('node-selected', self._on_node_selected)
        self.state.connect('node-deselected', self._on_node_deselected)

    def set_data(self, node_graph, pos_dict):
        self.normal_edges.clear()
        self.outward_edges.clear() 
        self.inward_edges.clear()
        self.dimmed_nodes.clear()
        self.normal_nodes.clear()
        
        self.node_graph = node_graph
        self.all_nodes_set = set(node_graph.nodes())
        self.all_edges_set = set(node_graph.edges())

        self.pos_dict = pos_dict
        self.orig_pos_dict = pos_dict.copy()
        self.scale = 1.0
        self.x_translate = None
        self.y_translate = None

        for node, neighbors in self.node_graph.adjacency():
            for neighbor in neighbors:
                self.normal_edges.add((node, neighbor))

        self.normal_nodes.update(self.node_graph.nodes())

        self.drawing_area.queue_draw()
        self.legend_drawing_area.queue_draw()

    def _setup_controllers(self):
        # Drag controller
        gesture = Gtk.GestureDrag()
        gesture.connect('drag-begin', self.on_drag_begin)
        gesture.connect('drag-update', self.on_drag_update)
        gesture.connect('drag-end', self.on_drag_end)
        self.drawing_area.add_controller(gesture)

        # Motion controller
        motion = Gtk.EventControllerMotion.new()
        motion.connect("motion", self.on_cursor_move)
        self.drawing_area.add_controller(motion)

        # Scroll controller
        scroll = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.VERTICAL)
        scroll.connect("scroll", self.on_scroll)
        self.drawing_area.add_controller(scroll)

        # Click controller
        click = Gtk.GestureClick()
        click.set_button(1)  # Left mouse button
        click.connect("released", self.on_click)
        self.drawing_area.add_controller(click)

    def draw_edge(self,
                  cr: cairo.Context,
                  node_1: str,
                  node_2: str,
                  type: str,
                  width=1,
                  has_arrow=False):
        x1, y1 = self.pos_dict[node_1]
        x2, y2 = self.pos_dict[node_2]

        color = self.colors[f"{type}-edge-color"]
        cr.set_source_rgb(color[0]/255, color[1]/255, color[2]/255)
        cr.set_line_width(width)

        cr.move_to(x1, y1)
        cr.line_to(x2, y2)
        cr.stroke()

        if has_arrow:
            dx = x2 - x1
            dy = y2 - y1
            angle = math.atan2(dy, dx)

            # Arrow properties
            arrow_length = 10
            arrow_angle = math.pi / 6  # 30 degrees

            # Calculate arrow points
            arrow_x = x2 - (self.node_graph.nodes[node_2]["size"] * self.scale) * math.cos(angle)
            arrow_y = y2 - (self.node_graph.nodes[node_2]["size"] * self.scale) * math.sin(angle)

            # Draw arrow head
            cr.move_to(arrow_x, arrow_y)
            cr.line_to(arrow_x - arrow_length * math.cos(angle - arrow_angle),
                       arrow_y - arrow_length * math.sin(angle - arrow_angle))
            cr.move_to(arrow_x, arrow_y)
            cr.line_to(arrow_x - arrow_length * math.cos(angle + arrow_angle),
                       arrow_y - arrow_length * math.sin(angle + arrow_angle))
            cr.stroke()

    def draw_node(self,
                  cr: cairo.Context,
                  node: str,
                  type: str,
                  dimmed: bool = False
                  ):
        color_queue = type + "-node-color" + ("-dimmed" if dimmed else "")
        if self.state.hovered_node == node:
            color_queue += "-hovered"
        color = self.colors[color_queue]
        cr.set_source_rgb(color[0]/255, color[1]/255, color[2]/255)

        # In Cairo, if you draw an arc without starting a new sub-path, it will
        # implicitly draw a line from the current point to the start of the arc.
        # That's where your extra lines are coming from — they are line segments
        # connecting previous drawing operations to the circle. Thus, we have to
        # call new_sub_path()
        cr.new_sub_path()

        radius = self.node_graph.nodes[node]["size"] * self.scale
        cr.arc(self.pos_dict[node][0],
               self.pos_dict[node][1],
               radius,
               0, 2 * math.pi)

        if self.node_graph.nodes[node].get("section", None) == "metapackages":
            cr.stroke()
        else:
            cr.fill()

    def draw_func(self, _event, cr: cairo.Context, width, height):
        if not self.node_graph or not self.pos_dict:
            return

        if self.x_translate is None or self.y_translate is None:
            self.x_translate = width  / 2
            self.y_translate = height / 2

        cr.translate(self.x_translate, self.y_translate)

        for edge in self.normal_edges:
            self.draw_edge(cr, edge[0], edge[1], type='default')

        # Draw dimmed nodes
        for node in self.dimmed_nodes:
            if self.node_graph.nodes[node].get("manual", False):
                self.draw_node(cr, node, type='manual', dimmed=True)
            else:
                self.draw_node(cr, node, type='auto', dimmed=True)

        # Draw highlighted edges
        for edge in self.inward_edges:
            self.draw_edge(cr, edge[0], edge[1], type='inward', width=2, has_arrow=True)
        for edge in self.outward_edges:
            self.draw_edge(cr, edge[0], edge[1], type='outward', width=2, has_arrow=True)

        # Draw normal nodes last
        for node in self.normal_nodes:
            if self.node_graph.nodes[node].get("manual", False):
                self.draw_node(cr, node, type='manual')
            else:
                self.draw_node(cr, node, type='auto')

        if self.state.selected_node:
            self.draw_node(cr, self.state.selected_node, type='selected')

    def on_drag_begin(self, _event, _x, _y):
        self.x_drag_start = self.x_translate
        self.y_drag_start = self.y_translate
        self.is_dragging = False 

    def on_drag_update(self, event: Gtk.GestureDrag, x, y):
        self.x_translate = self.x_drag_start + x
        self.y_translate = self.y_drag_start + y
        self.is_dragging = True
        self.drawing_area.set_cursor(self.move_cursor)

        event.get_widget().queue_draw()

    def on_drag_end(self, _event, _x, _y):
        self.is_dragging = False
        self.drawing_area.set_cursor(self.default_cursor)

    def on_scroll(self, event: Gtk.EventControllerScroll, _dx, dy):
        zoom_factor = SCALE_STEP
        zoom_factor = zoom_factor if dy > 0 else -zoom_factor

        old_scale = self.scale
        new_scale = self.scale - zoom_factor
        new_scale = max(SCALE_MIN, min(new_scale, SCALE_MAX))
        if new_scale == old_scale:
            return

        self.scale = new_scale

        for entry in self.pos_dict:
            x, y = self.orig_pos_dict[entry]
            new_x = x * self.scale
            new_y = y * self.scale
            self.pos_dict[entry] = (new_x, new_y)

        self.x_translate = self.x_cursor - (self.x_cursor - self.x_translate) * (self.scale / old_scale)
        self.y_translate = self.y_cursor - (self.y_cursor - self.y_translate) * (self.scale / old_scale)

        event.get_widget().queue_draw()

    def _get_node_at_position(self, x: float, y: float) -> str | None:
        """Get the node at the given screen coordinates, or None if no node is there."""
        x_graph = (x - self.x_translate) / self.scale
        y_graph = (y - self.y_translate) / self.scale

        for node in self.node_graph.nodes():
            node_x, node_y = self.orig_pos_dict[node]
            distance = math.sqrt((x_graph - node_x)**2 + (y_graph - node_y)**2)
            node_radius = self.node_graph.nodes[node]["size"]
            if distance <= node_radius:
                return node
        return None

    def on_cursor_move(self, _event, x, y):
        self.x_cursor = x
        self.y_cursor = y
        hovered_node = self._get_node_at_position(x, y)

        if hovered_node:
            self.drawing_area.set_cursor(self.hand_cursor)
            name = get_pkg_name_from_node(hovered_node)

            self.pkg_name_label.set_markup(f"<b>{name}</b>")

            rect = Gdk.Rectangle()
            rect.x = self.pos_dict[hovered_node][0] + self.x_translate
            rect.y = self.pos_dict[hovered_node][1] + self.y_translate - self.node_graph.nodes[hovered_node]["size"] * self.scale
            rect.width = 1
            rect.height = 1
            self.label_popover.set_pointing_to(rect)
            self.label_popover.popup()
        else:
            self.drawing_area.set_cursor(self.default_cursor)
            self.label_popover.popdown()

        if hovered_node != self.state.hovered_node:
            self.drawing_area.queue_draw()
        self.state.hovered_node = hovered_node

    def on_click(self, _gesture, _n_press, x: float, y: float):
        if self.is_dragging:
            return

        clicked_node = self._get_node_at_position(x, y)
        if clicked_node is None:
            self.state.selected_node = None
        else:
            self.state.selected_node = clicked_node
        self.drawing_area.queue_draw()

    def _on_node_selected(self, _state, node: str):
        successors = set(self.node_graph.successors(node))
        predecessors = set(self.node_graph.predecessors(node))
        related_nodes = successors | predecessors
        self.normal_nodes = related_nodes
        self.dimmed_nodes = self.all_nodes_set - self.normal_nodes

        self.inward_edges = self.node_graph.in_edges(nbunch=node)
        self.outward_edges = self.node_graph.out_edges(nbunch=node)

        self.drawing_area.queue_draw()

    def _on_node_deselected(self, _state):
        self.normal_nodes = self.all_nodes_set
        self.dimmed_nodes = set()

        self.normal_edges = set(self.node_graph.edges())
        self.inward_edges = set()
        self.outward_edges = set()
        self.drawing_area.queue_draw()

    def load_theme_colors(self, *_):
        """Update the color palette based on the current theme."""
        color_palette = self.appearance_settings.get_child("dark" if self.style_manager.get_dark() else "light")
        keys = color_palette.list_keys()
        for key in keys:
            self.colors[key] = color_palette.get_value(key)
        self.drawing_area.queue_draw()
        self.legend_drawing_area.queue_draw()

