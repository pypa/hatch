import subprocess


def main():
    subprocess.call(['twine', 'upload', 'dist/*'])

if __name__ == '__main__':
    main()
