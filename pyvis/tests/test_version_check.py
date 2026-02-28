import unittest
import os
import shutil
from ..network import Network


class VersionCheckTestCase(unittest.TestCase):
    def setUp(self):
        self.g = Network()
        self.g.add_node(1)
        self.g.add_node(2)
        self.g.add_edge(1, 2)
        self.test_file = "test_version.html"

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists("lib"):
            if os.path.exists("lib/vis-10.0.2"):
                shutil.rmtree("lib/vis-10.0.2")
            # Only remove lib if it's empty
            if not os.listdir("lib"):
                os.rmdir("lib")

    def test_cdn_resources_local_version(self):
        # Test that local resources copy the correct version
        self.g.cdn_resources = "local"
        self.g.write_html(self.test_file)
        
        # Check if the directory exists
        self.assertTrue(os.path.exists("lib/vis-10.0.2"))
        self.assertTrue(os.path.exists("lib/vis-10.0.2/vis-network.min.js"))
        self.assertTrue(os.path.exists("lib/vis-10.0.2/vis-network.min.css"))

        # Check if the HTML file references the correct version
        with open(self.test_file, "r") as f:
            content = f.read()
            self.assertIn('lib/vis-10.0.2/vis-network.min.js', content)
            self.assertIn('lib/vis-10.0.2/vis-network.min.css', content)

    def test_cdn_resources_remote_version(self):
        # Test that remote resources point to the correct version
        self.g.cdn_resources = "remote"
        self.g.write_html(self.test_file)

        with open(self.test_file, "r") as f:
            content = f.read()
            # We expect the CDN link to be updated to 10.0.2
            # The template uses unpkg.com
            self.assertIn('https://unpkg.com/vis-network@10.0.2/dist/vis-network.min.js', content)
            self.assertIn('https://unpkg.com/vis-network@10.0.2/styles/vis-network.min.css', content)
