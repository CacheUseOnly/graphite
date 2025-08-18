from typing import Optional

from gi.repository import GObject

class GraphState(GObject.Object):
    """Centralized state management for the graph application"""
    
    __gsignals__ = {
        'node-hovered': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'node-unhovered': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'node-selected': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'node-deselected': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'regenerate-requested': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'regenerate-progress': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'regenerate-complete': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self):
        super().__init__()
        self._hovered_node = None
        self._selected_node = None

    @property
    def hovered_node(self):
        return self._hovered_node

    @hovered_node.setter
    def hovered_node(self, node: Optional[str]):
        if node != self._hovered_node:
            self._hovered_node = node
            if node:
                self.emit('node-hovered', node)
            else:
                self.emit('node-unhovered')

    @property
    def selected_node(self):
        return self._selected_node

    @selected_node.setter
    def selected_node(self, node: Optional[str]):
        if node != self._selected_node:
            self._selected_node = node
            if node:
                self.emit('node-selected', node)
            else:
                self.emit('node-deselected')
