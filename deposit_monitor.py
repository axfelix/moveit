import os
import hashlib
import re
import sys
import datetime
from time import strftime

if not re.search('meta\.txt', sys.argv[1]):
	sys.exit()

zipname = re.sub('-meta\.txt', '.zip', sys.argv[1])

with open(zipname,'rb') as transferZip:
    data = transferZip.read()
    checksum = hashlib.md5(data).hexdigest()

with open(sys.argv[1],'rb') as transferMeta:
    metaTxt = transferMeta.read()
    originalChecksum = re.search('(?<=Checksum: )[a-z0-9]+', metaTxt).group(0)

if checksum == originalChecksum:
    listnote = "deposit " + sys.argv[1] + " valid " + str(datetime.datetime.fromtimestamp(os.path.getmtime(sys.argv[1])))  + "\n"
else:
    listnote = "deposit " + sys.argv[1] + " invalid " + str(datetime.datetime.fromtimestamp(os.path.getmtime(sys.argv[1])))  + "\n"

with open('deposits.txt', 'a') as depositlist:
    depositlist.write(listnote)
