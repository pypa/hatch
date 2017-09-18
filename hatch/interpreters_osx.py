import os
import re
import subprocess
import requests
from distutils.version import LooseVersion
from hatch.exceptions import PythonPkgNotInstalled, PkgInstallerSystemProblem

ENCODING = 'utf-8'

PYTHON_PKGS = {
    'app': 'org.python.Python.PythonApplications-', # /Applications/Python x.x
    'docs': 'org.python.Python.PythonDocumentation-', # /Library/Frameworks/Python.framework/Versions/x.x/Resources/English.lproj/Documentation
    'framework': 'org.python.Python.PythonFramework-', #/Library/Frameworks/Python.framework/Versions/x.x
    'tools': 'org.python.Python.PythonUnixTools-'
}

PYTHON_PKGS_DEFAULT_PATHS = {
    'framework': '/Library/Frameworks/Python.framework/Versions/{}',
    'app': '/Applications/Python {}',
}

DEVNULL = open(os.devnull, 'w')


def gen_installers_list():
    ver_to_link = {}
    html = requests.get('https://www.python.org/downloads/mac-osx/').text
    lined = html.split('\n')
    instlr_link_re = re.compile('.*<li>Download <a href="(.+)?">.*64-bit\/32-bit installer.*')
    #TODO: Separate install options for x32 builds?
    ver_re = re.compile('.*python-(.*?)-')
    for li in lined:
        try:
            link = instlr_link_re.match(li).groups(1)[0]
            ver = ver_re.match(link).groups(1)[0]
            ver_to_link[ver] = link
        except AttributeError:
            pass
    return ver_to_link

def gen_installers_cli():
    installers = gen_installers_list()
    for ver in '23':
        vers = [i for i in installers if i.startswith(ver)]
        vers.sort(key=LooseVersion)
        yield vers


def strip_build_ver(version):
    return '.'.join(version.split('.')[:-1])


def no_build(version):
    return len(version.split('.')) == 2


def py_framework_path(stripped_ver):
    return pkg_path(PYTHON_PKGS['framework'] + stripped_ver)


def is_pkgs_installed(stripped_ver):
    for pkg in PYTHON_PKGS.values():
        command = ['pkgutil', '--pkgs=%s%s' % (pkg, stripped_ver)]
        res = subprocess.run(command, stdout=DEVNULL)
        if res.returncode:
            return False
    else:
        return True


def pkg_path(pkg):
    command = ['pkgutil', '--pkg-info=%s' % pkg]
    res = subprocess.run(command, stdout=subprocess.PIPE)
    if res.returncode:
        raise PythonPkgNotInstalled('{} is not installed!'.format(pkg))

    out = res.stdout.decode(ENCODING)
    splitted = out.split('\n')
    vol = splitted[2][8:]  # strip 'volume: '
    loc = splitted[3][10:]  # strip 'location: '
    return vol + loc


def install_interpreter(pkg_path):
    command = ['sudo -S installer -pkg %s -target /' % pkg_path]
    res = subprocess.run(command, stdout=subprocess.PIPE, shell=True)
    if res.returncode:
        raise PkgInstallerSystemProblem('Problem installing package %s' % pkg_path)


def uninstall_pkgs(sv):
    # According to pkgutil --pkg-info org.python.Python.PythonUnixTools-x.x is empty,
    #  and Documentation pkg is in Framework's path
    for pkg in ('framework', 'app'):
        ppath = PYTHON_PKGS_DEFAULT_PATHS[pkg].format(sv)
        print('Removing {}'.format(ppath))
        command = "sudo rm -rf {}".format(ppath)
        subprocess.run(command, stdout=DEVNULL, shell=True)
    for pkg in PYTHON_PKGS.values():
        add_ver = pkg + sv
        forget_pkg = "sudo pkgutil --forget {}".format(add_ver)
        subprocess.run(forget_pkg, stdout=DEVNULL, shell=True)


def download_python_pkg(version):
    PYTHON_PKG_LINKS = gen_installers_list()
    #TODO: Caching in file?
    resp = requests.get(PYTHON_PKG_LINKS[version], stream=True)
    downloads = os.path.expanduser('~/Downloads')
    pkg_name = PYTHON_PKG_LINKS[version].split('/')[-1]
    os.chdir(downloads)
    with open(pkg_name, 'wb') as f:
        for chunk in resp:
            f.write(chunk)
    del resp
    return os.path.join(downloads, pkg_name)
