import os


def locate_file(root, file_name):
    while True:
        file_path = os.path.join(root, file_name)
        if os.path.isfile(file_path):
            return file_path

        new_root = os.path.dirname(root)
        if new_root == root:
            return

        root = new_root
