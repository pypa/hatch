import os
import re
import subprocess
import requests
from hatch.exceptions import PythonPkgNotInstalled, PkgInstallerSystemProblem

ENCODING = 'utf-8'

# reinstall = 'pip3.5 uninstall hatch & cd ~/PycharmProjects/hatch && python3.5 setup.py install'
#
# example = 'org.python.Python.PythonApplications-3.4'
# example_installer_path = '~/Downloads/python-3.4.4-macosx10.6.pkg'
# ex = 'cd /Applications'
# delete_files_ex = "pkgutil --only-files --files org.python.Python.PythonApplications-3.4 | tr '\n' '\0' | xargs -n 1 -0 sudo rm -rf"
# delete_dirs_ex = "pkgutil --only-dirs --files org.python.Python.PythonApplications-3.4 | tail -r | tr '\n' '\0' | xargs -n 1 -0 sudo rmdir"
# forget_ex = "sudo pkgutil --forget org.python.Python.PythonApplications-3.4"

PYTHON_PKGS = {
    'app': 'org.python.Python.PythonApplications-',
    'docs': 'org.python.Python.PythonDocumentation-',
    'framework': 'org.python.Python.PythonFramework-',
    'tools': 'org.python.Python.PythonUnixTools-'
}

PYTHON_PKGS_DEFAULT_PATHS = {
    'framework': '/Library/Frameworks/Python.framework'
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


def strip_build_ver(version):
    return '.'.join(version.split('.')[:-1])


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


def uninstall_pkg(pkg):
    path = pkg_path(pkg)
    os.chdir(path)
    delete_files = "pkgutil --only-files --files {}" \
                   " | tr '\n' '\\0'" \
                   " | xargs -n 1 -0 sudo rm -rf".format(pkg)
    subprocess.run(delete_files, stdout=DEVNULL, shell=True)

    delete_dirs = "pkgutil --only-dirs --files {}" \
                  " | tail -r" \
                  " | tr '\n' '\\0' | xargs -n 1 -0 sudo rmdir".format(pkg)
    subprocess.run(delete_dirs, stdout=DEVNULL, stderr=DEVNULL, shell=True)

    forget_pkg = "sudo pkgutil --forget {}".format(pkg)
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
