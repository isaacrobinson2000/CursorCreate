# CursorCreate
A Multi-platform Cursor Theme Building Program. 

CursorCreate allows you to build cursor themes for Windows, MacOS, and Linux. It supports reading cursors from svg, xcur, cur, ani, and all image formats supported by the pillow imaging library. Also includes a gui for easily modifying cursor projects.

### Installing

To install CursorCreate from source, you will need the following dependencies:
 - CairoSVG
 - Pillow
 - numpy
 - PySide2

Once all of these dependencies are installed in your python environment (using a virtual environment is recommended) you can pull down this repository using a git clone as below:

```bash
git clone https://github.com/isaacrobinson2000/CursorCreate.git
```

### How to Use

To launch the GUI, simply execute the CursorCreate entry python file, as below:
```bash
python cursorcreate.py
```
In the GUI, images can simply be dragged and dropped onto the cursor selection widgets in order to load them in. The hotspots and delays of animation frames can be modified by simply clicking on the cursor, as shown below:

![GIF of dragging images...](https://user-images.githubusercontent.com/47544550/77180722-f3b7d480-6a8f-11ea-899a-5ecc57f9e9b8.gif)
![GIF of modifying hotspots and delays...](https://user-images.githubusercontent.com/47544550/77181094-75a7fd80-6a90-11ea-9486-dddf1b2dc792.gif)

To save a project, click the "Save Project" button, which will copy the source image files over to the user selected directory and generate a 'build.json' which tells CursorCreate how to turn the image source files into cursor themes for each platform.

For static images and SVGs, the animation frames are expected to be stored horizontally as squares side by side. 

Note that CursorCreate is also capable of doing several actions from the command line, including building cursor themes. To see all the supported command line operations, execute the command below:
```bash
python cursorcreate.py --help
```
