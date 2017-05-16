"""
GUI tool to create a Bag from a filesystem folder.
"""

import sys
import os
import shutil
import bagit
import platform
import random
import string
import re
from time import strftime
import subprocess
from paramiko import SSHClient
from paramiko import AutoAddPolicy
from paramiko import AuthenticationException
from scp import SCPClient
from distutils.dir_util import copy_tree
import zipfile
import hashlib
import tempfile
from urllib import urlencode
import urllib2
from zipfile import ZipFile


# These are toggled at build time. TODO: switch to argument parser.

# toggle this if depositing to an Active Directory server
internalDepositor = 0

# toggle this if depositing to SFU Library
radar = 0

# toggle this if bypassing the Bagit step
nobag = 0

# toggle this if bypassing the transfer and only creating a Bag on desktop
ziponly = 1

bagit_checksum_algorithms = ['md5']


session_message = "Session Number"
session_message_final_win = "The transfer package will be created and placed on your\n desktop after this; large packages may take a moment.\n\nSession Number"
session_message_final_mac = "The transfer package will be created and placed on your desktop after this; large packages may take a moment.\n\nSession Number"

transfer_message = "Transfer Number"

if internalDepositor == 0:
	username_message = "Username"
	password_message = "Password"
else:
	username_message = "SFU Computing ID"
	password_message = "SFU Computing password"

close_session_message = "Is this the final session for this transfer?\nThe transfer will begin in the background after this \nand let you know when it is complete."
close_session_osx_title = "Is this the final session for this transfer?"
close_session_osx_informative = "The transfer will begin in the background and let you know when it is complete."

if radar == 0:
	sfu_success_message = "Files have been successfuly transferred to SFU Archives. \nAn archivist will be in contact with you if further attention is needed."

	bag_success_message = "Files have been successfully packaged and placed in a new folder on your desktop for transfer."

else:
	sfu_success_message = "Files have been successfuly transferred to SFU Library. \nA librarian will be in contact with you if further attention is needed."
	password_message = "Please input your SFU Computing password. \nTransfer will commence after clicking OK and you will be notified when it is complete."

sfu_failure_message = "Transfer did not complete successfully. \nPlease contact moveit@sfu.ca for help."

if platform.system() != 'Darwin' and platform.system() != 'Windows':
	# The Linux/Gtk config has been removed for now
	from gi.repository import Gtk
elif platform.system() == 'Windows':
	from PyQt4 import QtGui, QtCore
elif platform.system() == 'Darwin':
	# Sets up Cocoadialog for error message popup on OSX.
	CD_PATH = os.path.join("~/.createbag/", "CocoaDialog.app/Contents/MacOS/CocoaDialog")

	def cocoaPopup(boxtype, title, texttype, message, button, buttontext):
		template = CD_PATH + " %s --title '%s' '%s' '%s' '%s' '%s'"
		cocoa_process = subprocess.Popen(template % (boxtype, title, texttype, message, button, buttontext), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=False)
		cocoa_output = cocoa_process.communicate()
		cocoa_result = cocoa_output[0].splitlines()
		return cocoa_result

	def cocoaError():
			if __name__ == "__main__":
				popup = cocoaPopup("msgbox", "Error", "--text", "Sorry, you can't create a bag here -- you may want to change the config file so that bags are always created in a different output directory, rather than in situ.", "--button1", "OK")
				if popup == "1":
					sys.exit()

	def cocoaSuccess(bag_dir):
			if __name__ == "__main__":
				popup = cocoaPopup("msgbox", "Success!", "--text", "Bag created at %s" % bag_dir, "--button1", "OK")

	def cocoaTransferSuccess(success_type):
			if __name__ == "__main__":
				popup = cocoaPopup("msgbox", "SFU MoveIt", "--informative-text", success_type, "--button1", "OK")

	def cocoaTransferError(failure_message=sfu_failure_message):
			if __name__ == "__main__":
				popup = cocoaPopup("msgbox", "SFU MoveIt", "--informative-text", failure_message, "--button1", "OK")
				if popup == "1":
					sys.exit()

	def cocoaSessionNo():
			if __name__ == "__main__":
				if ziponly == 0:
					popup = cocoaPopup("standard-inputbox", "Session Number", "--informative-text", session_message, "", "")
				else:
					popup = cocoaPopup("standard-inputbox", "Session Number", "--informative-text", session_message_final_mac, "", "")	
				if popup[0] == "2":
					sys.exit()
				return popup[1]

	def cocoaTransferNo():
			if __name__ == "__main__":
				popup = cocoaPopup("standard-inputbox", "Transfer Number", "--informative-text", transfer_message, "", "")
				if popup[0] == "2":
					sys.exit()
				return popup[1]

	def cocoaUsername():
			if __name__ == "__main__":
				popup = cocoaPopup("standard-inputbox", "Username", "--informative-text", username_message, "", "")
				if popup[0] == "2":
					sys.exit()
				return popup[1]

	def cocoaPassword():
			if __name__ == "__main__":
				popup = cocoaPopup("secure-standard-inputbox", "Password", "--informative-text", password_message, "", "")
				if popup[0] == "2":
					sys.exit()
				return popup[1]

	def cocoaCloseSession():
			if __name__ == "__main__":
				popup = cocoaPopup("yesno-msgbox", "SFU MoveIt", "--text", close_session_osx_title, "--informative-text", close_session_osx_informative)
				if popup[0] == "3":
					sys.exit()
				# "no" will equal 2 rather than 0 in cocoa, but "yes" still = 1
				return popup[0]


def make_bag(chosen_folder):
	if nobag == 0:
		bag_dir_parent = tempfile.mkdtemp()
		if os.path.isdir(bag_dir_parent):
			shutil.rmtree(bag_dir_parent)
		bag_dir = os.path.join(bag_dir_parent, 'bag')
		os.makedirs(bag_dir)
		copy_tree(chosen_folder, bag_dir)


		# Create the Bag.
		try:
			bag = bagit.make_bag(bag_dir, None, 1, bagit_checksum_algorithms)
		except (bagit.BagError, Exception) as e:
				if platform.system() == 'Darwin':
					cocoaError()
				elif platform.system() == 'Windows':
					QtChooserWindow.qt_error(ex)
					return

		return bag_dir_parent

	else:
		return chosen_folder


def transfer_manifest(bag_dir, sessionno, transferno, archivesUsername, checksum, metafilename, filelist):
	current_time = strftime("%Y-%m-%d %H:%M:%S")
	transfer_metadata = "Transfer Number: " + transferno + "-" + sessionno + "\nUser: " + archivesUsername + "\nChecksum: " + checksum + "\nTime Received: " + current_time + "\n" + filelist

	with open(metafilename, 'w') as transfer_metafile:
		transfer_metafile.write(transfer_metadata)


def generate_password():
	length = 13
	chars = string.ascii_letters + string.digits + '!@#$%^&*()'
	random.seed = (os.urandom(1024))

	passwordString = ''.join(random.choice(chars) for i in range(length))
	return passwordString


def generate_file_md5(zipname, blocksize=2**20):
    m = hashlib.md5()
    with open(zipname, "rb") as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update(buf)
    return m.hexdigest()


def check_zip_and_send(bag_dir_parent, sessionno, transferno, archivesUsername, archivesPassword, close_session, parent_path):

	if nobag == 0:
		bag_dir = os.path.join(str(bag_dir_parent), 'bag')
		numbered_bag_dir = os.path.join(str(bag_dir_parent), (transferno + "-" + sessionno))
		metafilename = numbered_bag_dir + "-meta.txt"
		zipname = shutil.make_archive(numbered_bag_dir, 'zip', bag_dir)

		checksum = generate_file_md5(zipname)

		with open(os.path.join(bag_dir, 'manifest-md5.txt'), 'r') as manifestmd5:
			bagit_manifest_txt = manifestmd5.read()
			filelist = re.sub("\r?\n\S*?\s+data", ("\n" + parent_path), bagit_manifest_txt)
			filelist = filelist.split(' ', 1)[1]

		passwordString = generate_password()
		# Passwording uploaded files is disabled for now.
		#with ZipFile(zipname, 'a') as transferZip:
		#	transferZip.setpassword(passwordString)

		shutil.rmtree(bag_dir)

		# check transfer number blacklist and post back if OK
		get_req = urllib2.Request("http://arbutus.archives.sfu.ca:8008/blacklist")
		try:
			get_response = urllib2.urlopen(get_req, timeout = 2)
			blacklist = get_response.read()
			blacklist_entries = blacklist.split()
			if transferno in blacklist_entries:
				if platform.system() == 'Darwin':
					cocoaTransferError()
				elif platform.system() == 'Windows':
					QtChooserWindow.qt_transfer_failure(ex)
					return
		except:
			pass

		values = {'transfer' : transferno, 'session' : sessionno, 'username' : archivesUsername, 'checksum' : checksum}
		postdata = urlencode(values)
		post_req = urllib2.Request("http://arbutus.archives.sfu.ca:8008/blacklist", postdata)

	else:
		filelist = ""

	transfer_manifest(bag_dir, sessionno, transferno, archivesUsername, checksum, metafilename, filelist)

	if ziponly == 1:
		desktopPath = os.path.expanduser("~/Desktop/")
		outputPath = desktopPath + os.path.splitext(os.path.basename(zipname))[0]
		os.mkdir(outputPath)
		shutil.move(zipname, (outputPath + "/" + os.path.basename(zipname)))
		shutil.move(metafilename, (outputPath + "/" + os.path.basename(metafilename)))
		return "bagged"


	try:
		ssh = SSHClient()
		ssh.set_missing_host_key_policy(AutoAddPolicy())
		if internalDepositor == 0:
			ssh.connect("142.58.136.69", username=archivesUsername, password=archivesPassword, look_for_keys=False)
			scp = SCPClient(ssh.get_transport())
			remote_path = '~/deposit_here/' + transferno + "-" + sessionno
			scp.put(bag_dir_parent, remote_path, recursive=True)
			if close_session == 1:
				try:
					urllib2.urlopen(post_req, timeout = 2)
				except:
					pass

		elif radar == 1:
			ssh.connect("researchdata.sfu.ca", username=archivesUsername, password=archivesPassword, look_for_keys=False)
			scp = SCPClient(ssh.get_transport())
			remote_zip_path = '~/.pydiodata/' + os.path.basename(os.path.normpath(bag_dir))
			try:
				scp.put(os.path.normpath(bag_dir), remote_zip_path, recursive=True)
			except:
				ssh.exec_command('mkdir .pydiodata')
				scp.put(os.path.normpath(bag_dir), remote_zip_path, recursive=True)

		else:
			ssh.connect("pine.archives.sfu.ca", username=archivesUsername, password=archivesPassword, look_for_keys=False)
			scp = SCPClient(ssh.get_transport())
			remote_path = '~/' + transferno + "-" + sessionno
			scp.put(bag_dir_parent, remote_path, recursive=True)
			if close_session == 1:
				try:
					urllib2.urlopen(post_req, timeout = 2)
				except:
					pass

	except AuthenticationException:
		failure_message = "Transfer did not complete successfully. \nUsername or password incorrect."
		if platform.system() == 'Darwin':
			cocoaTransferError(failure_message)
		elif platform.system() == 'Windows':
			QtChooserWindow.qt_transfer_failure(ex, failure_message)
			return

	except:
		if platform.system() == 'Darwin':
			cocoaTransferError()
		elif platform.system() == 'Windows':
			QtChooserWindow.qt_transfer_failure(ex)
			return

	if nobag == 0:
		os.remove(zipname)
		os.remove(metafilename)
	return remote_path

# Windows/Qt-specific code (can also work on Linux but Gtk is nicer)
if platform.system() == 'Windows':

	class QtChooserWindow(QtGui.QDialog):

		def __init__(self, parent=None):
			super(QtChooserWindow, self).__init__(parent)
			if parent is None:
				self.initUI()

		def initUI(self):
			choose_folder_button = QtGui.QPushButton("Choose a folder to transfer", self)
			choose_folder_button.clicked.connect(self.showDialog)
			choose_folder_button.resize(choose_folder_button.sizeHint())
			choose_folder_button.move(20, 30)

			quit_button = QtGui.QPushButton("Quit", self)
			quit_button.clicked.connect(QtCore.QCoreApplication.instance().quit)
			quit_button.resize(quit_button.sizeHint())
			quit_button.move(250, 30)

			self.resize(345, 80)
			self.center()
			self.setWindowTitle('SFU MoveIt')

			self.show()

		def center(self):
			qr = self.frameGeometry()
			cp = QtGui.QDesktopWidget().availableGeometry().center()
			qr.moveCenter(cp)
			self.move(qr.topLeft())

		def showDialog(self):
			fname = QtGui.QFileDialog.getExistingDirectory(self, 'SFU MoveIt - Choose a folder to transfer', '/home')

			parent_path = os.path.basename(os.path.normpath(str(fname)))
			bag_dir = make_bag(str(fname))

			if (bag_dir):
				archivesUsername = self.qt_username(bag_dir)
				if ziponly == 0:
					archivesPassword = self.qt_password(bag_dir)
				else:
					archivesPassword = ""
				if radar == 0:
					transferno = self.qt_transfer(bag_dir)
					sessionno = self.qt_session(bag_dir)
					if ziponly == 0:
						close_session = self.qt_close_session()
					else:
						close_session = 0
				else:
					sessionno = 0
					transferno = 0
					close_session = 0

				payload = check_zip_and_send(bag_dir, str(sessionno), str(transferno), str(archivesUsername), str(archivesPassword), close_session, parent_path)

				if (payload):
					if payload == "bagged":
						self.qt_transfer_success(bag_success_message)
					else:
						self.qt_transfer_success(sfu_success_message)

		def qt_username(self, bag_dir):
			archivesUsername, ok = QtGui.QInputDialog.getText(self, "Username", username_message)
			return archivesUsername

		def qt_password(self, bag_dir):
			archivesPassword, ok = QtGui.QInputDialog.getText(self, "Password", password_message, 2)
			return archivesPassword

		def qt_session(self, bag_dir):
			if ziponly == 0:
				sessionno, ok = QtGui.QInputDialog.getText(self, "Session Number", session_message)
			else:
				sessionno, ok = QtGui.QInputDialog.getText(self, "Session Number", session_message_final_win)				
			return sessionno

		def qt_transfer(self, bag_dir):
			transferno, ok = QtGui.QInputDialog.getText(self, "Transfer Number", transfer_message)
			return transferno

		def qt_close_session(self):
			close_session_window = QtGui.QMessageBox.question(self, 'SFU MoveIt', close_session_message, QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
			if close_session_window == QtGui.QMessageBox.Yes:
				close_session = 1
			else:
				close_session = 0
			return close_session

		def qt_transfer_success(self, success_type):
			confirmation_window = QtChooserWindow(self)

			confirmation_string = success_type
			confirmation_message = QtGui.QLabel(confirmation_string, confirmation_window)
			confirmation_message.move(20, 30)

			confirmation_window.resize(500, 80)
			confirmation_window.center()
			confirmation_window.setWindowTitle('Success')

			confirmation_window.show()

		def qt_transfer_failure(self, failure_message=sfu_failure_message):
			confirmation_window = QtChooserWindow(self)

			confirmation_string = failure_message
			confirmation_message = QtGui.QLabel(confirmation_string, confirmation_window)
			confirmation_message.move(20, 30)

			confirmation_window.resize(500, 80)
			confirmation_window.center()
			confirmation_window.setWindowTitle('Error')

			confirmation_window.show()

		def qt_confirmation(self, bag_dir):
			confirmation_window = QtChooserWindow(self)

			confirmation_string = "The Bag for folder " + bag_dir + " has been created."
			confirmation_message = QtGui.QLabel(confirmation_string, confirmation_window)
			confirmation_message.move(20, 30)

			confirmation_window.resize(500, 80)
			confirmation_window.center()
			confirmation_window.setWindowTitle('Bag created')

			confirmation_window.show()

		def qt_error(self):
			error_window = QtChooserWindow(self)

			error_message = QtGui.QLabel("Something went wrong! Please open an issue report at http://github.com/axfelix/moveit/issues", error_window)
			error_message.move(20, 30)

			error_window.resize(360, 80)
			error_window.center()
			error_window.setWindowTitle('Sorry')

			error_window.show()


	app = QtGui.QApplication(sys.argv)
	ex = QtChooserWindow()
	sys.exit(app.exec_())


# OSX-specific code.
elif platform.system() == 'Darwin':

	# add progress bar code eventually
	archivesUsername = cocoaUsername()
	if ziponly == 0:
		archivesPassword = cocoaPassword()
	else:
		archivesPassword = ""
	transferno = cocoaTransferNo()
	sessionno = cocoaSessionNo()
	bag_dir = make_bag(sys.argv[1])
	parent_path = os.path.basename(os.path.normpath(sys.argv[1]))
	if ziponly == 0:
		close_session = cocoaCloseSession()
	else:
		close_session = 0
	script_output = check_zip_and_send(bag_dir, sessionno, transferno, archivesUsername, archivesPassword, close_session, parent_path)
	if script_output == "bagged":
		cocoaTransferSuccess(bag_success_message)
	else:
		cocoaTransferSuccess(sfu_success_message)
