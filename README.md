# SFU Archives Deposit -- "Create Bag" Tool

This is a simple utility, forked from http://github.com/mjordan/createbag, which facilitates deposit of files and folders to SFU Archives by creating a Library of Congress-standard "bagit" container on the local machine.

You're welcome to use this in your own institution; all that's required is changing the IP addresses of the upload destinations at various locations in createbag.py. If you want to hack on this, you need Python 2.7 and the official bagit module.

The tool is designed to work, with GUI functionality, on Windows, OSX, and Linux. The Windows version uses Qt, the OSX version uses CocoaDialog, and the Linux version uses Gtk3 (though it is currently unmaintained and missing a few hooks).

`blacklist.py` and `deposit_monitor.py` can be run on the deposit server to provide some simple monitoring functionality.

GUI executables are provided for Windows and OSX, built with pyinstaller and Platypus respectively. Pyinstaller syntax to build is `pyinstaller --onefile --noconsole --icon=sfu.ico createbag.py`. Platypus bundles are built with `osxinstall.sh` as the primary executable, with `CocoaDialog.app`, `CreateBag.workflow`, and the `createbag` binary output from pyinstaller as bundled files. The Windows executable runs standalone; the OSX version is installed as an automator hook, detailed below.


## Usage

#### Windows

Download the utility from [http://www.sfu.ca/~garnett/archivesdeposit/SFU%20MoveIt.zip]. When the utility starts, a small window with two buttons appears. One of them is "Exit". Clicking on "Choose a folder to transfer" will open up a standard file/directory browser.

Choosing a directory and clicking on "Create Bag" will prompt a user for a small amount of metadata (username and deposit number), and then automatically create a bag and place it on your desktop. The user will be notified of success or failure with a popup window upon completion.

#### OSX

Download and run the zipped OSX installer from [http://www.sfu.ca/~garnett/archivesdeposit/Install%20SFU%20MoveIt.zip]. You can then create and transfer bag using this script by right-clicking on any folder in your Finder and selecting "Deposit to SFU Archives" from the context menu.

## License

The Unlicense (http://unlicense.org/). Refer to the LICENSE file for
more information.