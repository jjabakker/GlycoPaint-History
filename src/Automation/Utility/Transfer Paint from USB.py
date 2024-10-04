import os
import platform
import shutil
from tkinter.filedialog import askdirectory

d_dir = 'd:\\PyCharmProjects\\Paint-v5\\'


def copy_code_directory(source_dir):
    for root, dirs, files in os.walk(source_dir):
        for filename in files:
            if filename.startswith('.'):
                continue
            if filename.startswith('__'):
                continue
            if filename.endswith('py'):
                index = root.find("src\\")
                destination = d_dir + root[index:]
                if not os.path.exists(destination):
                    os.makedirs(destination)
                shutil.copy(os.path.join(root, filename), destination)
                print(f"From {root:30} copied {filename:30} to {destination}")
        print("\n")
        for dirname in dirs:
            pass


def copy_files():
    if platform.system() == 'Darwin':
        print("Unsupported")
        return
    else:
        source_dir = askdirectory(title='Specify src directory', initialdir=os.path.expanduser('~'))
        if len(source_dir) == 0:
            print("\nNo directory selected")
            return
        source_dir = source_dir + os.sep

        copy_code_directory(source_dir + 'Automation')
        copy_code_directory(source_dir + 'Fiji')
        copy_code_directory(source_dir + 'Common')


if __name__ == '__main__':
    copy_files()
