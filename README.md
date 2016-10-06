# SFU Archives Deposit -- "Create Bag" Tool

This is a simple utility, forked from http://github.com/mjordan/createbag, which facilitates deposit of files and folders to SFU Archives by creating a Library of Congress-standard "bagit" container on the local machine and uploading it via SFTP with a small amount of metadata, including transfer credentials and checksums.

You're welcome to use this in your own institution; all that's required is changing the IP addresses of the upload destinations at various locations in createbag.py. If you want to hack on this, you need Python 2.7 and the official Library of Congress [bagit][] module.

The tool is designed to work, with GUI functionality, on Windows, OSX, and Linux. The Windows version uses Qt, the OSX version uses CocoaDialog, and the Linux version uses Gtk3 (though it is currently unmaintained and missing a few hooks).

GUI executables are provided for Windows and OSX, built with pyinstaller and Platypus respectively. Pyinstaller syntax to build is `pyinstaller --onefile --noconsole --icon=sfu.ico createbag.py`. Platypus bundles are built with `osxinstall.sh` as the primary executable, with `CocoaDialog.app`, `CreateBag.workflow`, and the `createbag` binary output from pyinstaller as bundled files. The Windows executable runs standalone; the OSX version is installed as an automator hook, detailed below.


## Usage

#### Linux / Windows

When the utility starts, a small window with two buttons appears:

![][]

Clicking on the "Choose a folder to transfer" (may instead simply read "Create bag" in older versions) will open up a standard file/directory browser:

![][1]

Choosing a directory and clicking on "Create Bag" will prompt a user for a small amount of metadata (username, password, and deposit number), and then automatically begin creating and transferring the bag in the background. There is currently no progress bar to indicate when the transfer will be complete, but the user will be notified of success or failure with a popup window upon completion.


#### OSX

Download and run either of the zipped OSX installers. You can then create and transfer bag using this script by right-clicking on any folder in your Finder and selecting "Deposit to SFU Archives" from the context menu (this line may simply read "Create bag" in older versions):

![][3]


## License

The Unlicense (http://unlicense.org/). Refer to the LICENSE file for
more information.

  [bagit]: https://github.com/LibraryOfCongress/bagit-python
  []: https://dl.dropboxusercontent.com/u/1015702/linked_to/createbag/createbag.png
  [1]: https://dl.dropboxusercontent.com/u/1015702/linked_to/createbag/choosefolder.png
  [3]: https://dl.dropboxusercontent.com/u/1015702/linked_to/createbag/osx.png
