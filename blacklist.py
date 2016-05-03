from bottle import get, post, request, run
import re

@get('/blacklist')
def getblacklist():
	with open("blacklist.txt", "r") as blacklist:
		blacklistText = blacklist.read()
		return blacklistText

@post('/blacklist')
def addtoblacklist():
	try:
		transfer = request.forms.get("transfer")
		session = request.forms.get("session")
		username = request.forms.get("username")
		checksum = request.forms.get("checksum")

		transfer_meta_path = "/home/" + username + "/deposit_here/" + transfer + "-" + session + "/" + transfer + "-" + session + "-meta.txt"
		with open(transfer_meta_path,'rb') as transferMeta:
			metaTxt = transferMeta.read()
			originalChecksum = re.search('(?<=Checksum: )[a-z0-9]+', metaTxt).group(0)
		if originalChecksum == checksum and re.match(r'^\w+$', checksum):
			with open("blacklist.txt", "a") as blacklist:
				blacklist.write((transfer + "\n"))
	except:
		pass

run(host='0.0.0.0', port=8008, debug=True)
