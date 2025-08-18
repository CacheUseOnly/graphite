import math

def normalized_size(degree):
    """Normalize the size of a node."""
    n = 10
    c = 1
    a = 0.01

    return n - (n - c) * math.exp(-a * degree)


def get_pkg_name_from_node(node: str) -> str:
    """Extract the package name from a node string."""
    return node.split('=')[0] if '=' in node else node


def get_pkg_version_from_node(node: str) -> str:
    """Extract the package version from a node string."""
    parts = node.split('=')
    if len(parts) > 1:
        version_part = parts[1]
        return version_part.rsplit(':', 1)[0] if ':' in version_part else version_part
    return 'Unknown'


def get_pkg_arch_from_node(node: str) -> str:
    """Extract the package architecture from a node string."""
    parts = node.split(':')
    return parts[-1] if len(parts) > 1 else 'Unknown'