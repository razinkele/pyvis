"""Configuration constants for vis-network library integration.

This module centralizes the vis-network version and CDN configuration
for easy maintenance and updates.
"""

from enum import Enum

# vis-network version - update this single constant to upgrade across the entire library
VIS_NETWORK_VERSION = "10.1.2"

# CDN URLs
UNPKG_CDN_BASE = f"https://unpkg.com/vis-network@{VIS_NETWORK_VERSION}"
CDNJS_CDN_BASE = f"https://cdnjs.cloudflare.com/ajax/libs/vis-network/{VIS_NETWORK_VERSION}"

# Local library directory name
LOCAL_LIB_DIR = f"vis-{VIS_NETWORK_VERSION}"

# Resource paths for templates
VIS_CSS_UNPKG = f"{UNPKG_CDN_BASE}/styles/vis-network.min.css"
VIS_JS_UNPKG = f"{UNPKG_CDN_BASE}/dist/vis-network.min.js"
VIS_ESM_UNPKG = f"{UNPKG_CDN_BASE}/dist/vis-network.esm.js"

# Local resource paths (relative to lib directory)
VIS_CSS_LOCAL = f"lib/{LOCAL_LIB_DIR}/vis-network.min.css"
VIS_JS_LOCAL = f"lib/{LOCAL_LIB_DIR}/vis-network.min.js"


class CDNResource(str, Enum):
    """Enum for CDN resource selection in Network visualization.
    
    Provides type-safe constants for specifying how vis-network resources
    (JS and CSS files) are loaded: locally, inline in HTML, or from remote CDN.
    
    All values are strings, allowing direct use with existing code that
    expects string values while providing enum type safety.
    
    Examples:
        >>> from pyvis.network import Network
        >>> net = Network(cdn_resources=CDNResource.LOCAL.value)
        >>> net.cdn_resources
        'local'
        
        >>> # Or use the enum directly with isinstance checks
        >>> from pyvis.vis_config import CDNResource
        >>> resource = CDNResource.REMOTE
        >>> isinstance(resource, str)  # True, due to str mixin
        True
    """
    
    LOCAL = "local"
    INLINE = "in_line"
    REMOTE = "remote"
    REMOTE_ESM = "remote_esm"
    
    # Backward compatibility aliases
    IN_LINE = "in_line"
