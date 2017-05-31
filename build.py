import os
import subprocess


def main():
    distro_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(distro_dir, 'dist')
    if not os.path.exists(dist_dir):
        os.mkdir(dist_dir)
    os.chdir(dist_dir)
    for file in os.listdir(os.getcwd()):
        os.remove(file)
    os.chdir(distro_dir)
    subprocess.call(['python', 'setup.py', 'bdist_wheel', '--universal'])

if __name__ == '__main__':
    main()
