# can monitor directories for input to this script like so:

# inotifywait -m -r -q -e create --format %w%f /home/*/deposit_here | while read line; do if [[ $line == *"-meta.txt" ]]; then echo "Subject: Deposit Report "$(basename $(line)) > deposits.txt; python /home/archivesuser/deposit_monitor.py $line; rsync -az -e ssh $(dirname $line) archivesadmin@pine.archives.sfu.ca:~/arbutus_backups/.; sendmail "radancy@sfu.ca, kas22@sfu.ca" < deposits.txt; rm deposits.txt; fi; done&


import hashlib
import re
import sys
from time import strftime

if not re.search('meta\.txt', sys.argv[1]):
	sys.exit()

zipname = re.sub('-meta\.txt', '.zip', sys.argv[1])
filelistname = re.sub('-meta\.txt', '-list.txt', sys.argv[1])

with open(zipname,'rb') as transferZip:
	data = transferZip.read()
	checksum = hashlib.md5(data).hexdigest()

with open(sys.argv[1],'rb') as transferMeta:
	metaTxt = transferMeta.read()
	originalChecksum = re.search('(?<=Checksum: )[a-z0-9]+', metaTxt).group(0)

if checksum == originalChecksum:
	listnote = "deposit " + sys.argv[1] + " valid " + strftime("%Y-%m-%d %H:%M:%S") + "\n"
else:
	listnote = "deposit " + sys.argv[1] + " invalid " + strftime("%Y-%m-%d %H:%M:%S") + "\n"

with open(filelistname,'rb') as transferList:
	listTxt = transferList.read()

listnote = listnote + listTxt + "\n"

with open('deposits.txt', 'a') as depositlist:
	depositlist.write(listnote)
