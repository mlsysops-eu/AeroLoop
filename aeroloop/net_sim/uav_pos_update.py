from core.UAV import UAV
from core.Messages import *
from core.env import *

import sys
import zmq
import pyproj
import json
import time
import logging
import logging.config	




logging.config.fileConfig(LOG_CONF,
                        defaults={'logfilename':LOG_FILE},
                        disable_existing_loggers=False)


def pos_update(pos):
	#See the example above to update the transformation procedure
	ecef = pyproj.Proj(proj='geocent', ellps='WGS84', datum='WGS84')
	lla = pyproj.Proj(proj='latlong', ellps='WGS84', datum='WGS84')
	x, y, z = pyproj.transform( lla,
								ecef, 
								pos.lon,
								pos.lat,
								pos.alt,
								radians=False)

	ecef_pos = NSPos(x=x,y=y,z=z)
	# print(json.dumps(asdict(ecef_pos)))
	data=json.dumps(asdict(ecef_pos))
	msg = [b"UAV1",bytes(data,'utf-8')]
	socket.send_multipart(msg)
	print(f"send invoked {msg}")

	# print(json.dumps(asdict(ecef_pos)))


context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5556")

rover = UAV(connection = "udp:0.0.0.0:14556")

rover.RegisterListener("POSITION",pos_update)

while True:
	time.sleep(10000)