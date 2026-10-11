#!/usr/bin/env python3
"""Exercise site publication with real archives and a local S3 substitute."""

import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest


DEPLOY_SCRIPT = Path(__file__).with_name("deploy.sh")
FAKE_AWS = """#!/usr/bin/env python3
import os
from pathlib import Path
import sys

assert sys.argv[1:3] == ["s3", "cp"]
source, destination = sys.argv[3:5]
if source != "-" and os.environ.get("FAIL_UPLOAD") == "1":
    sys.exit(1)
target = Path(os.environ["FAKE_S3_ROOT"]) / destination.removeprefix("s3://")
target.parent.mkdir(parents=True, exist_ok=True)
target.write_bytes(sys.stdin.buffer.read() if source == "-" else Path(source).read_bytes())
"""


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.storage = self.root / "storage"
        self.domain = self.storage / "sites-bucket/sites/oss.silitics.com"
        self.domain.mkdir(parents=True)
        (self.domain / "CURRENT").write_text("domain-current\n")
        (self.domain / "other").mkdir()
        (self.domain / "other/CURRENT").write_text("other-current\n")
        self.source = self.root / "dist"
        self.source.mkdir()
        (self.source / "index.html").write_text("Sidex homepage")
        (self.source / "docs").mkdir()
        (self.source / "docs/index.html").write_text("Sidex docs")
        (self.source / "pagefind").mkdir()
        (self.source / "pagefind/pagefind.js").write_text("search index")
        binaries = self.root / "bin"
        binaries.mkdir()
        aws = binaries / "aws"
        aws.write_text(FAKE_AWS)
        aws.chmod(0o755)
        self.environment = {
            **os.environ,
            "PATH": f"{binaries}:{os.environ['PATH']}",
            "SITE_DOMAIN": "oss.silitics.com",
            "SITE_SOURCE_DIR": str(self.source),
            "SITE_BUCKET": "sites-bucket",
            "SITE_ENDPOINT": "https://unused.invalid",
            "GITHUB_SHA": "0123456789abcdef",
            "GITHUB_OUTPUT": str(self.root / "outputs"),
            "GITHUB_STEP_SUMMARY": str(self.root / "summary"),
            "FAKE_S3_ROOT": str(self.storage),
        }

    def deploy(self, path, fail_upload=False):
        return subprocess.run(
            ["bash", str(DEPLOY_SCRIPT)],
            cwd=self.root,
            env={
                **self.environment,
                "SITE_PATH": path,
                "FAIL_UPLOAD": "1" if fail_upload else "0",
            },
            capture_output=True,
            text=True,
        )

    def test_scoped_archive_and_pointer_leave_other_sites_untouched(self):
        """Publish a usable Sidex archive without replacing domain or sibling pointers."""
        result = self.deploy("sidex")
        self.assertEqual(result.returncode, 0, result.stderr)
        archive_name = (self.domain / "sidex/CURRENT").read_text().strip()
        with tarfile.open(self.domain / "sidex" / archive_name) as archive:
            self.assertEqual(archive.extractfile("./index.html").read(), b"Sidex homepage")
            self.assertEqual(archive.extractfile("./docs/index.html").read(), b"Sidex docs")
            self.assertEqual(archive.extractfile("./pagefind/pagefind.js").read(), b"search index")
        self.assertEqual((self.domain / "CURRENT").read_text(), "domain-current\n")
        self.assertEqual((self.domain / "other/CURRENT").read_text(), "other-current\n")
        self.assertEqual(set(path.name for path in self.domain.iterdir()), {"CURRENT", "other", "sidex"})

    def test_empty_path_preserves_whole_domain_publication(self):
        """Existing callers still publish their archive and pointer at the domain prefix."""
        result = self.deploy("")
        self.assertEqual(result.returncode, 0, result.stderr)
        archive_name = (self.domain / "CURRENT").read_text().strip()
        self.assertTrue((self.domain / archive_name).is_file())
        self.assertFalse((self.domain / "sidex").exists())

    def test_failed_upload_keeps_active_pointer(self):
        """An archive upload failure cannot activate incomplete content."""
        (self.domain / "sidex").mkdir()
        (self.domain / "sidex/CURRENT").write_text("previous.tar.gz\n")
        result = self.deploy("sidex", fail_upload=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.domain / "sidex/CURRENT").read_text(), "previous.tar.gz\n")

    def test_invalid_paths_cannot_escape_the_publication_prefix(self):
        """Reject absolute paths and parent components before uploading any objects."""
        for path in ["/sidex", "../rugix", "sidex/../../rugix"]:
            with self.subTest(path=path):
                self.assertNotEqual(self.deploy(path).returncode, 0)
        self.assertEqual(set(path.name for path in self.domain.iterdir()), {"CURRENT", "other"})


if __name__ == "__main__":
    unittest.main()
