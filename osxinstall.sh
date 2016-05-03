#!/bin/bash

if [ ! -d ~/Library/Services ]; then
	mkdir ~/Library/Services
fi

cp -R CreateBag.workflow ~/Library/Services/CreateBag.workflow
mkdir ~/.createbag
cp createbag ~/.createbag/createbag
chmod +x ~/.createbag/createbag
cp -R CocoaDialog.app ~/.createbag/CocoaDialog.app

if [ $? -eq 0 ]; then
success=($(~/.createbag/CocoaDialog.app/Contents/MacOS/CocoaDialog msgbox --title "SFU Archives Transfer" --text "Install complete" --informative-text "Hooray! You can now send your file to SFU Archives by right-clicking on a folder in your Finder and selecting 'Transfer to SFU Archives' from the bottom of the menu." --button1 "OK"))
else
failure=($(~/.createbag/CocoaDialog.app/Contents/MacOS/CocoaDialog msgbox --title "SFU Archives Transfer" --text "Install failed" --informative-text "Install did not complete successfully. Please let us know at https://github.com/axfelix/createbag/issues. Sorry!" --button1 "OK"))
fi
