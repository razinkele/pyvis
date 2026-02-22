"""Configuration constants for vis-network library integration.

This module centralizes the vis-network version and CDN configuration
for easy maintenance and updates.
"""

# vis-network version - update this single constant to upgrade across the entire library
VIS_NETWORK_VERSION = "10.0.2"

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
