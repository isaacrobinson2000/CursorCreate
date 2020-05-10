# CursorCreate
A Multi-platform Cursor Theme Building Program. 

CursorCreate allows you to build cursor themes for Windows, MacOS, and Linux. It supports reading cursors from svg, xcur, cur, ani, and all image formats supported by the Pillow imaging library. Also includes a GUI for easily modifying cursor projects.

### Installing

#### Packaged Binaries:

If you would like to avoid going through the process of installing from source, pre-built binaries have been provided on the releases page. Just download the one for your platform, extract the zip file, and run the executable inside the extracted folder. 

Releases Page:
[https://github.com/isaacrobinson2000/CursorCreate/releases](https://github.com/isaacrobinson2000/CursorCreate/releases)

#### From PyPI:

CursorCreate is also avaibable on PyPI. To install it, exectute one of the commands below:
```bash
# For only command line support:
pip install CursorCreate
# For additional GUI support:
pip install CursorCreate[gui]
```
Once it is installed, it can be executed using the `CursorCreate` command in the shell:
```bash
# Launch the GUI:
CursorCreate
# List all command line options:
CursorCreate --help
```

#### From Source:

To install CursorCreate from source, you will need the following dependencies:
 - CairoSVG
 - Pillow
 - numpy
 - PySide2

Once all of these dependencies are installed in your python environment (using a virtual environment is recommended) you can pull down this repository using a git clone as below:

```bash
git clone https://github.com/isaacrobinson2000/CursorCreate.git
```

If you are attempting to package CursorCreate for your platform, you will need PyInstaller installed to the virtual environment, and staticx installed on the global python environment if you plan on building on linux. Use the build scripts provided with this project, as the binary will not have all of the required files and dependencies packaged with it otherwise. 

### Example Theme

This program also comes with a template theme, but due to separate licensing the template theme is kept in a separate repository. Follow the link below to get the template theme:

[https://github.com/isaacrobinson2000/CursorCreateTemplateTheme](https://github.com/isaacrobinson2000/CursorCreateTemplateTheme)

### How to Use

To launch the GUI, simply execute the CursorCreate entry file, as below:
```bash
# If you installed via prepackaged binary (Have to be in the same directory as the executable):
./CursorCreate
# If you installed via PyPI (pip install):
CursorCreate
# If you are running it from source:
python CursorCreate/cursorcreate.py
```
In the GUI, images can simply be dragged and dropped onto the cursor selection widgets in order to load them in. The hotspots and delays of animation frames can be modified by simply clicking on the cursor, as shown below:

![GIF of dragging images...](https://user-images.githubusercontent.com/47544550/77180722-f3b7d480-6a8f-11ea-899a-5ecc57f9e9b8.gif)
![GIF of modifying hotspots and delays...](https://user-images.githubusercontent.com/47544550/77181094-75a7fd80-6a90-11ea-9486-dddf1b2dc792.gif)

To save a project, click the "Save Project" button, which will copy the source image files over to the user selected directory and generate a 'build.json' which tells CursorCreate how to turn the image source files into cursor themes for each platform.

For static images and SVGs, the animation frames are expected to be stored horizontally as squares side by side. 

Note that CursorCreate is also capable of doing several actions from the command line, including building cursor themes. To see all the supported command line operations, execute the command below:
```bash
# If you installed via prepackaged binary (Have to be in the same directory as the executable):
./CursorCreate --help
# If you installed via PyPI (pip install):
CursorCreate --help
# If you are running it from source:
python CursorCreate/cursorcreate.py --help
```

### Bugs/Issues

This software is currently in beta, and therefore may have some bugs. If you run into any issues, feel free to open an issue on the GitHub [issues](https://github.com/isaacrobinson2000/CursorCreate/issues) page.

### Future Goals

 - [x] Create a setup.py for CursorCreate
 - [ ] Add progress indicators when building cursors or performing any other action.
