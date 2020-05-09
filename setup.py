from setuptools import setup

setup(
    name='CursorCreate',
    version='1.2.2',
    packages=['CursorCreate', 'CursorCreate.gui', 'CursorCreate.lib'],
    url='https://github.com/isaacrobinson2000/CursorCreate',
    license='GPLv3',
    author='Isaac Robinson',
    author_email='awesomeisaac2000@gmail.com',
    description='A Multi-platform Cursor Theme Building Program',
    entry_points = {
        'console_scripts': [
           'CursorCreate = CursorCreate.cursorcreate:main'
        ],
    },
    install_requires = {
        "CairoSVG",
        "Pillow",
        "numpy"
    },
    extras_require = {
        "gui": ["PySide2"]
    }
)
