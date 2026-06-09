from hatch.env.lockers.pip import PipLocker
from hatch.env.lockers.uv import UvLocker
from hatchling.plugin import hookimpl


@hookimpl
def hatch_register_locker():
    return [UvLocker, PipLocker]
