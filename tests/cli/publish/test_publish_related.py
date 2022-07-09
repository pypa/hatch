import os
import tarfile

import hatch.publish.pypi as pypi

def test_tar_layout(hatch, temp_dir):
    class TarTestApp():
        def __init__(self):
            pass

        def abort(self, message):
            raise Exception(message)

    app = TarTestApp()
    with temp_dir.as_cwd():
        deep = os.path.join('tartest-1.0', 'tartest')
        os.makedirs(deep)
        dummy_path = os.path.join(deep, "dummy")
        pkg_info_path = os.path.join("tartest-1.0", "PKG-INFO")

        with open(dummy_path, "w") as fobj:
            fobj.write("Dummy file.  It just has to exist")

        with open(pkg_info_path, "w") as fobj:
            fobj.write("Name: tartest\nVersion: 1.0\n")

        with tarfile.open("/tmp/tartest-1.0.tar.gz", "w:gz") as tar_archive:
            tar_archive.add(dummy_path)
            tar_archive.add(pkg_info_path)

        headers = pypi.get_sdist_form_data(app, "/tmp/tartest-1.0.tar.gz")

        assert headers["name"] == "tartest"
        assert headers["version"] == "1.0"
