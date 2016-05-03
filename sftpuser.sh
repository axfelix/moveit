#!/bin/bash

echo "New user name?"
read newuser
echo "New user password?"
read password
if id -u $newuser >/dev/null 2>&1; then
	echo "User already exists. Please go to System -> Users and Groups to reconcile existing users."
else
	sudo useradd $newuser
	echo $newuser":"$password | sudo chpasswd
	sudo usermod -a -G sftponly $newuser
	sudo mkdir /home/$newuser
	sudo mkdir /home/$newuser/deposit_here
	sudo chown $newuser /home/$newuser/deposit_here
	sudo chmod 755 /home/$newuser/deposit_here
	echo "User created. To manage users (including users created by this script), please go to System -> Users and Groups (click the mouse icon in the top-left corner of the desktop)."
fi
killall inotifywait
while read line; do bash ~/inotify_deposit.sh; done < <(inotifywait -m -r -q -e create --format %w%f /home/*/deposit_here)
read