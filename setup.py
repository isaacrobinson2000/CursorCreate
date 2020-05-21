from setuptools import setup
from pathlib import Path

readme_file = (Path(__file__).parent) / "README.md"
with readme_file.open("r") as f:
    text = f.read()

setup(
    name='CursorCreate',
    version='1.3.1',
    packages=['CursorCreate', 'CursorCreate.gui', 'CursorCreate.lib'],
    url='https://github.com/isaacrobinson2000/CursorCreate',
    license='GPLv3',
    author='Isaac Robinson',
    download_url="https://github.com/isaacrobinson2000/CursorCreate/archive/v1.3.1.tar.gz",
    author_email='awesomeisaac2000@gmail.com',
    description='A Multi-platform Cursor Theme Building Program',
    long_description = text,
    long_description_content_type="text/markdown",
    entry_points = {
        'console_scripts': [
           'CursorCreate = CursorCreate.cursorcreate:main'
        ],
    },
    install_requires = [
        "CairoSVG",
        "Pillow",
        "numpy"
    ],
    extras_require = {
        "gui": ["PySide2"]
    }
)
