#!/bin/bash

rm -rf ~/Library/Services/CreateBag.workflow

~/.createbag/CocoaDialog.app/Contents/MacOS/CocoaDialog msgbox --title "SFU MoveIt" --text "Uninstall complete" --informative-text "SFU MoveIt has been uninstalled." --button1 "OK"

rm -rf ~/.createbag
