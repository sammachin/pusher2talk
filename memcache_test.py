import memcache

mc = memcache.Client(['127.0.0.1:11211'], debug=0)



def adduser(room, user):
	data = json.loads(mc.get(room))
	data['users'].append(user)
	mc.set(room, json.dumps(data))
	


def deluser(room, user):
	data = json.loads(mc.get(room))
	data['users'].remove(user)
	mc.set(room, json.dumps(data))

	
def getusers(room):
	data = json.loads(mc.get(room))
	return data['users']

	