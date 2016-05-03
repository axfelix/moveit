"""
GUI tool to create a Bag from a filesystem folder.
"""

import sys
import os
import shutil
import getpass
import bagit
import platform
import random
import string
import re
from time import strftime
import subprocess
from paramiko import SSHClient
from paramiko import AutoAddPolicy
from scp import SCPClient
from distutils.dir_util import copy_tree
import zipfile
import hashlib
import tempfile
from urllib import urlencode
import urllib2
from zipfile import ZipFile


# change this to 1 if building for internal deposits, which use SFU credentials and go to a different server
internalDepositor = 1
radar = 0
nobag = 0

bagit_checksum_algorithms = ['md5']


session_message = "Session Number"

transfer_message = "ransfer Number"

if internalDepositor == 0:
	username_message = "Username"
	password_message = "Password"
else:
	username_message = "SFU Computing ID"
	password_message = "SFU Computing password"

close_session_message = "Is this the final session for this transfer?"

if radar == 0:
	sfu_success_message = "Files have been successfuly transferred to SFU Archives. \nAn archivist will be in contact with you if further attention is needed."

else:
	sfu_success_message = "Files have been successfuly transferred to SFU Library. \nA librarian will be in contact with you if further attention is needed."
	password_message = "Please input your SFU Computing password. \nTransfer will commence after clicking OK and you will be notified when it is complete."

sfu_failure_message = "Transfer did not complete successfully. \nPlease contact moveit@sfu.ca for help."

if platform.system() != 'Darwin' and platform.system() != 'Windows':
	# The Linux/Gtk config is currently unmaintained (broken)
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

	def cocoaTransferSuccess():
			if __name__ == "__main__":
				popup = cocoaPopup("msgbox", "SFU Transfer", "--informative-text", sfu_success_message, "--button1", "OK")

	def cocoaTransferError():
			if __name__ == "__main__":
				popup = cocoaPopup("msgbox", "SFU Transfer", "--informative-text", sfu_failure_message, "--button1", "OK")
				if popup == "1":
					sys.exit()

	def cocoaSessionNo():
			if __name__ == "__main__":
				popup = cocoaPopup("standard-inputbox", "Session Number", "--informative-text", session_message, "", "")
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
				popup = cocoaPopup("yesno-msgbox", "SFU Archives Transfer", "--informative-text", close_session_message, "", "")
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
				else:
					FolderChooserWindow.GtkError(win)

		return bag_dir_parent

	else:
		return chosen_folder


def transfer_manifest(bag_dir, sessionno, transferno, archivesUsername, checksum, metafilename, passwordString):
	current_time = strftime("%Y-%m-%d %H:%M:%S")
	# plain language manifest
	# transfer_metadata = "Your transfer, number " + sessionno + "-" + transferno + ", from user \'" + archivesUsername + "\', from the desktop folder " + clean_bag_dir + ", with md5 checksum " + checksum + ", was successfully received by SFU Archives at " + current_time + "."
	# key/value manifest
	transfer_metadata = "Transfer Number: " + transferno + "-" + sessionno + "\nUser: " + archivesUsername + "\nChecksum: " + checksum + "\nTime Received: " + current_time

	with open(metafilename, 'w') as transfer_metafile:
		transfer_metafile.write(transfer_metadata)


def generate_password():
	length = 13
	chars = string.ascii_letters + string.digits + '!@#$%^&*()'
	random.seed = (os.urandom(1024))

	passwordString = ''.join(random.choice(chars) for i in range(length))
	return passwordString


# need to add error handling to the ssh connection
def check_zip_and_send(bag_dir_parent, sessionno, transferno, archivesUsername, archivesPassword, close_session):

	if nobag == 0:
		bag_dir = os.path.join(str(bag_dir_parent), 'bag')
		numbered_bag_dir = os.path.join(str(bag_dir_parent), (transferno + "-" + sessionno))
		metafilename = numbered_bag_dir + "-meta.txt"
		zipname = shutil.make_archive(numbered_bag_dir, 'zip', bag_dir)

		with open(zipname,'rb') as transferZip:
			data = transferZip.read()
			checksum = hashlib.md5(data).hexdigest()

		with open(os.path.join(bag_dir, 'manifest-md5.txt'), 'r') as manifestmd5:
			bagit_manifest_txt = manifestmd5.read()
			filelist = re.sub("\r?\n\S*?\s+", "\n", bagit_manifest_txt)

		passwordString = generate_password()
		# Passwording uploaded files is disabled for now.
		#with ZipFile(zipname, 'a') as transferZip:	
		#	transferZip.setpassword(passwordString)

		shutil.rmtree(bag_dir)

		listfilename = numbered_bag_dir + "-list.txt"
		with open(listfilename,'w') as transfer_listfile:
			transfer_listfile.write(filelist)

		# check transfer number blacklist and post back if OK
		get_req = urllib2.Request("http://arbutus.archives.sfu.ca:8008/blacklist")
		get_response = urllib2.urlopen(get_req)
		blacklist = get_response.read()
		blacklist_entries = blacklist.split()
		if transferno in blacklist_entries:
			if platform.system() == 'Darwin':
				cocoaTransferError()
			elif platform.system() == 'Windows':
				QtChooserWindow.qt_transfer_failure(ex)
				return

		values = {'transfer' : transferno, 'session' : sessionno, 'username' : archivesUsername, 'checksum' : checksum}
		postdata = urlencode(values)
		post_req = urllib2.Request("http://arbutus.archives.sfu.ca:8008/blacklist", postdata)


	try:
		ssh = SSHClient()
		ssh.set_missing_host_key_policy(AutoAddPolicy())
		if internalDepositor == 0:
			ssh.connect("142.58.136.69", username=archivesUsername, password=archivesPassword, look_for_keys=False)
			scp = SCPClient(ssh.get_transport())
			#remote_zip_path = '~/deposit_here/' + sessionno + "-" + transferno + '.zip'
			#scp.put(zipname, remote_zip_path)
			transfer_manifest(bag_dir, sessionno, transferno, archivesUsername, checksum, metafilename, passwordString)
			#remote_meta_path = '~/deposit_here/' + sessionno + "-" + transferno + '-meta.txt'
			#scp.put(metafilename, remote_meta_path)
			remote_path = '~/deposit_here/' + transferno + "-" + sessionno
			scp.put(bag_dir_parent, remote_path, recursive=True)
			if close_session == 1:
				urllib2.urlopen(post_req)

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
			#remote_zip_path = '~/' + sessionno + "-" + transferno + '.zip'
			#scp.put(zipname, remote_zip_path)
			transfer_manifest(bag_dir, sessionno, transferno, archivesUsername, checksum, metafilename, passwordString)
			#remote_meta_path = '~/' + sessionno + "-" + transferno + '-meta.txt'
			#scp.put(metafilename, remote_meta_path)
			remote_path = '~/' + transferno + "-" + sessionno
			scp.put(bag_dir_parent, remote_path, recursive=True)
			if close_session == 1:
				urllib2.urlopen(post_req)


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


# Linux/Gtk-specific code (will work on Windows but not easily)
if platform.system() != 'Darwin' and platform.system() != 'Windows':
	class FolderChooserWindow(Gtk.Window):

		def __init__(self):
			Gtk.Window.__init__(self, title = config.get('UILabels', 'main_window_title', 'SFU Transfer'))
			self.set_border_width(10)
			self.move(200, 200)

			box = Gtk.Box(spacing=6)
			self.add(box)
			self.spinner = Gtk.Spinner()

			choose_folder_button = Gtk.Button("Choose a folder to transfer")
			choose_folder_button.connect("clicked", self.on_folder_clicked)
			box.add(choose_folder_button)

			quit_button = Gtk.Button("Quit")
			quit_button.connect("clicked", Gtk.main_quit)
			box.add(quit_button)

		def GtkError(self):
			not_allowed_message = "\n\nYou are not allowed to run the program on that directory."
			error_dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR,
				Gtk.ButtonsType.OK, "Sorry...")
			error_dialog.format_secondary_text(not_allowed_message)
			error_dialog.run()
			error_dialog.destroy()
			raise SystemExit

		def on_folder_clicked(self, widget):
			folder_picker_dialog = Gtk.FileChooserDialog(
				config.get('UILabels', 'file_chooser_window_title', 'SFU Transfer - Choose a folder to transfer'),
				self, Gtk.FileChooserAction.SELECT_FOLDER)
			folder_picker_dialog.set_default_size(800, 400)
			folder_picker_dialog.set_create_folders(False)
			folder_picker_dialog.add_btuton("Create Bag", -5)
			folder_picker_dialog.add_button("Cancel", -6)
			for filechooser_shortcut in filechooser_shortcuts:
				folder_picker_dialog.add_shortcut_folder(filechooser_shortcut)

			response = folder_picker_dialog.run()

			if response == -5:
				bag_dir = make_bag(folder_picker_dialog.get_filename())
				folder_picker_dialog.destroy()

				if (bag_dir):
					confirmation_dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO,
						Gtk.ButtonsType.OK, "Bag created")
					confirmation_dialog.format_secondary_text(
						"The Bag for folder %s has been created." % bag_dir)
					confirmation_dialog.run()
					confirmation_dialog.destroy()
			if response == -6:
				folder_picker_dialog.destroy()

	win = FolderChooserWindow()
	win.connect("delete-event", Gtk.main_quit)
	win.show_all()
	Gtk.main()


# Windows/Qt-specific code (can also work on Linux but Gtk is nicer)
elif platform.system() == 'Windows':

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
			self.setWindowTitle('SFU Transfer')

			self.show()

		def center(self):
			qr = self.frameGeometry()
			cp = QtGui.QDesktopWidget().availableGeometry().center()
			qr.moveCenter(cp)
			self.move(qr.topLeft())

		def showDialog(self):
			fname = QtGui.QFileDialog.getExistingDirectory(self, 'SFU Transfer - Choose a folder to transfer', '/home')

			bag_dir = make_bag(str(fname))

			if (bag_dir):
				# uncomment the below line and comment the ones after it if not SFU
				# self.qt_confirmation(bag_dir)
				archivesUsername = self.qt_username(bag_dir)
				archivesPassword = self.qt_password(bag_dir)
				if radar == 0:
					transferno = self.qt_transfer(bag_dir)
					sessionno = self.qt_session(bag_dir)
					close_session = self.qt_close_session()
				else:
					sessionno = 0
					transferno = 0
					close_session = 0

				payload = check_zip_and_send(bag_dir, str(sessionno), str(transferno), str(archivesUsername), str(archivesPassword), close_session)

				if (payload):
					self.qt_transfer_success()

		def qt_username(self, bag_dir):
			archivesUsername, ok = QtGui.QInputDialog.getText(self, "Username", username_message)
			return archivesUsername

		def qt_password(self, bag_dir):
			# TODO: obscure text entry
			archivesPassword, ok = QtGui.QInputDialog.getText(self, "Password", password_message, 2)
			return archivesPassword

		def qt_session(self, bag_dir):
			sessionno, ok = QtGui.QInputDialog.getText(self, "Session Number", session_message)
			return sessionno

		def qt_transfer(self, bag_dir):
			transferno, ok = QtGui.QInputDialog.getText(self, "Transfer Number", transfer_message)
			return transferno

		def qt_close_session(self):
			close_session_window = QtGui.QMessageBox.question(self, 'SFU Transfer', close_session_message, QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
			if close_session_window == QtGui.QMessageBox.Yes:
				close_session = 1
			else:
				close_session = 0
			return close_session

		def qt_transfer_success(self):
			confirmation_window = QtChooserWindow(self)

			confirmation_string = sfu_success_message
			confirmation_message = QtGui.QLabel(confirmation_string, confirmation_window)
			confirmation_message.move(20, 30)

			confirmation_window.resize(500, 80)
			confirmation_window.center()
			confirmation_window.setWindowTitle('Success')

			confirmation_window.show()

		def qt_transfer_failure(self):
			confirmation_window = QtChooserWindow(self)

			confirmation_string = sfu_failure_message
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

			error_message = QtGui.QLabel("Something went wrong! Please open an issue report at http://github.com/axfelix/createbag/issues", error_window)
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

	bag_dir = make_bag(sys.argv[1])
	# add progress bar code eventually
	# comment everything below except the last line if not SFU
	archivesUsername = cocoaUsername()
	archivesPassword = cocoaPassword()
	transferno = cocoaTransferNo()
	sessionno = cocoaSessionNo()
	close_session = cocoaCloseSession()
	if check_zip_and_send(bag_dir, sessionno, transferno, archivesUsername, archivesPassword, close_session):
		cocoaTransferSuccess()
	#	cocoaSuccess(bag_dir)
