import apt
from apt.cache import Filter, FilteredCache, Package

import networkx as nx

from .utils import *

class MarkedManualFilter(Filter):
    """Filter that returns all packages marked as manual"""

    def apply(self, pkg: Package) -> bool:
        if pkg.is_installed and not pkg.is_auto_installed:
            return True
        else:
            return False


def format_pkg_name(pkg: Package) -> str:
    """Format the package name in {name}={version}:{arch} format"""

    return f"{pkg.shortname}={pkg.installed.version}:{pkg.architecture()}"


def build_dependency_graph() -> nx.DiGraph:
    cache = apt.Cache()
    filtered = FilteredCache(cache)
    filtered.set_filter(MarkedManualFilter())

    graph = nx.DiGraph()

    for pkg in filtered:
        formatted_name = format_pkg_name(pkg)
        if pkg.installed.section == "metapackages":
            # Skip metapackages for now
            continue

        graph.add_node(formatted_name, manual=True, section=pkg.installed.section)
        for dep in pkg.installed.dependencies:
            if dep.rawtype == 'Depends':
                # TODO: handle OR-dependencies, or make sure that [0] indicates the installed candidate
                dep_name = format_pkg_name(dep.installed_target_versions[0].package) 
                graph.add_node(dep_name)
                graph.add_edge(formatted_name, dep_name)

    # Assign weight to nodes based on the number of both inward and outward dependencies
    for node in graph.nodes:
        graph.nodes[node]["weight"] = len(graph.in_edges(node)) + len(graph.out_edges(node))
        graph.nodes[node]["size"] = normalized_size(graph.nodes[node]["weight"])
    
    cache.close()

    return graph
