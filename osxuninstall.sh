#!/bin/bash

rm -rf ~/Library/Services/CreateBag.workflow

~/.createbag/CocoaDialog.app/Contents/MacOS/CocoaDialog msgbox --title "SFU Archives Transfer" --text "Uninstall complete" --informative-text "SFU Archives Transfer has been uninstalled." --button1 "OK"

rm -rf ~/.createbag
