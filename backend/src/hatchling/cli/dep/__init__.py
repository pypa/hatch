import sys


def synced_impl(dependencies, python):
    import subprocess
    from ast import literal_eval

    from packaging.requirements import Requirement

    from hatchling.dep.core import dependencies_in_sync

    sys_path = None
    if python:
        output = subprocess.check_output([python, '-c', 'import sys;print([path for path in sys.path if path])'])
        sys_path = literal_eval(output.strip().decode('utf-8'))

    sys.exit(0 if dependencies_in_sync(map(Requirement, dependencies), sys_path) else 1)


def synced_command(subparsers, defaults):
    parser = subparsers.add_parser('synced')
    parser.add_argument('dependencies', nargs='+')
    parser.add_argument('-p', '--python', dest='python', **defaults)
    parser.set_defaults(func=synced_impl)


def dep_command(subparsers, defaults):
    parser = subparsers.add_parser('dep')
    subparsers = parser.add_subparsers()

    synced_command(subparsers, defaults)
