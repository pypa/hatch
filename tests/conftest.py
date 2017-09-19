import sys
import pytest

ALL = set("darwin linux win".split())

def pytest_runtest_setup(item): # no cov
    if isinstance(item, item.Function):
        plat = sys.platform
        if not item.get_marker(plat):
            if ALL.intersection(item.keywords):
                pytest.skip("cannot run on platform %s" %(plat))