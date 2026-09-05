import unittest
import os
from ..network import Network
from .. import vis_config


class VersionCheckTestCase(unittest.TestCase):
    def setUp(self):
        self.g = Network()
        self.g.add_node(1)
        self.g.add_node(2)
        self.g.add_edge(1, 2)
        self.test_file = "test_version.html"

    def test_cdn_resources_local_version(self):
        # Test that local resources copy the correct version
        self.g.cdn_resources = "local"
        self.g.write_html(self.test_file)

        # Check if the directory exists
        self.assertTrue(os.path.exists(f"lib/{vis_config.LOCAL_LIB_DIR}"))
        self.assertTrue(os.path.exists(vis_config.VIS_JS_LOCAL))
        self.assertTrue(os.path.exists(vis_config.VIS_CSS_LOCAL))

        # Check if the HTML file references the correct version
        with open(self.test_file, "r") as f:
            content = f.read()
            self.assertIn(vis_config.VIS_JS_LOCAL, content)
            self.assertIn(vis_config.VIS_CSS_LOCAL, content)

    def test_cdn_resources_remote_version(self):
        # Test that remote resources point to the correct version
        self.g.cdn_resources = "remote"
        self.g.write_html(self.test_file)

        with open(self.test_file, "r") as f:
            content = f.read()
            # We expect the CDN link to be updated to the configured version
            # The template uses unpkg.com
            self.assertIn(vis_config.VIS_JS_UNPKG, content)
            self.assertIn(vis_config.VIS_CSS_UNPKG, content)
