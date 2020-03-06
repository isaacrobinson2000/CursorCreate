from pathlib import Path
import theme_util
import sys

try:
    from gui.cursorthememaker import launch_gui
except ImportError:
    launch_gui = None

def print_help():
    print("Cursor Theme Maker")
    print("Usage:")
    print("No arguments: Launch the GUI")
    print("'--help': Display help")
    print("'--build FILE1 FILE2 ...': Build cursor projects from the command line \n"
          "by passing the json files of the projects...")
    print("'--open FILE': Open the specified cursor project in the GUI by providing the json file...")

def main(args):
    if(len(args) == 0):
        if(launch_gui is not None):
            launch_gui(None)
        else:
            print("Unable to import and run gui, check if PySide2 is installed...")
            print_help()
        return

    if(args[0] == "--help"):
        print_help()
    elif(args[0] == "--open"):
        if(len(args) > 1):
            if(launch_gui is not None):
                launch_gui(args[1])
            else:
                print("Unable to import and run gui, check if PySide2 is installed...")
        else:
            print("No file provided...")
            launch_gui(None)
    elif(args[0] == "--build"):
        for config_file in args[1:]:
            try:
                config_path = Path(config_file)
                fc_data = theme_util.load_project(config_path)
                fc_data = {name: cursor for name, (cur_path, cursor) in fc_data.items()}
                theme_util.build_theme(config_path.parent.name, config_path.parent.parent, fc_data)
            except Exception as e:
                print(e)
                return
        print("Build Successful!")
    else:
        print_help()

if(__name__ == "__main__"):
    main(sys.argv[1:])