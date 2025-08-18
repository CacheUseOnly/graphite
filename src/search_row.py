from gi.repository import Adw

class SearchRow(Adw.ActionRow):
    """A custom row widget for package search results"""
    def __init__(self, pkg_node: str, pkg_name: str, pkg_version: str):
        super().__init__(
            title=pkg_name,
            subtitle=pkg_version,
            activatable=True
        )

        self.pkg_node = pkg_node