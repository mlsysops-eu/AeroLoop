import time
from pymavlink import mavutil
import logging
import logging.config
import threading
import math
from enum import Enum

from core.env import *
from core.Messages import *

logger = logging.getLogger(__name__)




class DroneState(Enum):
	ARMABLE = 1
	ARMED = 2
	DISARMED = 3
	TAKING_OFF = 4
	READY_TO_CRUISE = 5
	LANDING = 6
	RETURN_TO_HOME = 7
	NOT_READY = 8
	IN_HOME_POSITION = 9
	PILOT_OVERTAKE = 10



class cmd_bucket:
	def __init__(self,msg_type):
		self.msg_type = msg_type
		self.ack_arrived = False



class UAV(object):

	def __init__(self,connection = "udp:0.0.0.0:14556"):


		self.master = mavutil.mavlink_connection(connection)
		self.__handlers = {}

		self.link_active = False
		self.mtx = threading.Lock()
		self.cv = threading.Condition(self.mtx)

		rcv_th = threading.Thread(target = self._recv,daemon=True)
		rcv_th.start()
		self.rr_bucket_lst = []

		self.state = DroneState.NOT_READY.value
		self.armable_status  = DroneState.NOT_READY.value
		self.armed = False
		self.target_alt = 0

		#for controlled return to home position 
		self.home_lat=0.0
		self.home_lon=0.0
		self.targe_pos = 0

		#current location (updated at the rate of message position) 
		self.lat = 0.0
		self.lon = 0.0
		self.alt = 0.0

		logger.info("UAV started")


	def RegisterListener(self,tag,handler):

		self.__handlers[tag]=handler

	def arm(self):
		logger.info("arm called")
		notified = self.__mav_request_reply(mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,1)
		logger.info(f"arm returned {notified}")


	def change_mode(self,mode):
		mode_id = self.master.mode_mapping()[mode]
		notified = self.__mav_request_reply(mavutil.mavlink.MAV_CMD_DO_SET_MODE,
											param1=mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
											param2=mode_id)
		# self.master.set_mode(mode)
		logger.info(f"change mode returned {notified}")


	def take_off(self, alt):
		notified = self.__mav_request_reply(mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
											param1=0,
											param7=alt)


		# self.master.set_mode(mode)
		self.state = DroneState.TAKING_OFF.value
		self.target_alt = alt
		logger.info(f"Takeoff returned {notified}")



	def goto_home(self):

		self.master.mav.mission_item_send(self.master.target_system,
										self.master.target_component,
										0,
										mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
										mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 2, 0, 0,
										0,0,0,
										self.home_lat,self.home_lon,10.0)


	def goto(self,lat,lon,alt):

		self.master.mav.mission_item_send(0,0,0,
										mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
										mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 2, 0, 0,
										0,0,0,lat,lon,alt)

	def change_alt(self,alt):

		self.master.mav.mission_item_send(0,0,0,
										mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
										mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 2, 0, 0,
										0,0,0,self.lat,self.lon,alt)

		self.state = DroneState.TAKING_OFF.value
		self.target_alt = alt


	def update_home_position(self):
		notified = self.__mav_request_reply(mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE,
											param1=242)

		logger.info(f"report home position return {notified}")

	def move_ned(self):
		msg = self.master.mav.set_position_target_local_ned_encode(
	        0,
	        0, 0,
	        mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED,
	        3527 + 1535,
	        0, 0, 0,
	        -1, 0, 0,
	        0, 0, 0,
	        0, 0)

		self.master.mav.send(msg)


	def move_gbl(self,lon,lat,alt,hdg):
		msg = self.master.mav.set_position_target_global_int_encode(
	        0,
	        0, 0,
	        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
	        3064 ,
	        int(lat*1e7), int(lon*1e7), int(alt),
	        0, 0, 0,
	        0, 0, 0,
	        hdg*(3.14/180), 0)


		self.master.mav.send(msg)

	def get_home_position(self):
		return self.home_lat, self.home_lon

	def land(self):
		self.__mav_request_reply(mavutil.mavlink.MAV_CMD_NAV_LAND,
								param5=self.home_lat,
								param6=self.home_lon)


	#internal helpers implementing the MAVLINK command protocol
	def __mav_request_reply(self,command,param1=0,
							param2=0, param3=0,
							param4=0,param5=0,
							param6=0,param7=0):

		if not self.link_active:
			logger.error("no active link")
			return 

		rpl_bucket = cmd_bucket(command)

		self.mtx.acquire()

		self.rr_bucket_lst.append(rpl_bucket)
		logger.info("send command start")
		self.master.mav.command_long_send(
		    self.master.target_system,
		    self.master.target_component,
		    command,
		    0,
		    param1, param2, param3, param4, param5, param6, param7)

		logger.info("send command end")
		while rpl_bucket.ack_arrived == False:
			notified  = self.cv.wait(3)
			if not notified:
				logger.error("Timeout")
				rpl_bucket.ack_arrived = True

		self.rr_bucket_lst.remove(rpl_bucket)
		self.mtx.release()

		return notified


	def _recv(self):

		logger.info("MAVLing receiver started")
		while True:
			msg  = self.master.recv_match(blocking=True,timeout=3)

			if msg is None:
				logger.info("No link with UAV")
				self.link_active = False
				continue

			msg = msg.to_dict()


			if msg['mavpackettype'] == "GLOBAL_POSITION_INT":
				self.lon = msg['lon']/1e7
				self.lat = msg['lat']/1e7
				self.alt = msg['relative_alt']/1e3
				hdg = msg['hdg']/1e2
				spd = self.__convert_to_spd(msg['vx'],msg['vy'])

				if "POSITION" in self.__handlers:
					position_info =Position(lon=self.lon,
										lat=self.lat,
										alt=self.alt)
					self.__handlers["POSITION"](position_info)

			if msg['mavpackettype'] == "HEARTBEAT":
				if not self.link_active:
					logger.info("Link established with UAV")
				self.link_active = True

				self.armed=(msg['base_mode']& mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)


			if msg['mavpackettype'] == "COMMAND_ACK":

				# logger.debug(msg)
				self.mtx.acquire()
				for bucket in self.rr_bucket_lst:
					if msg['command'] == bucket.msg_type:
						bucket.ack_arrived = True

				self.cv.notifyAll()
				self.mtx.release()
				


	def __convert_to_spd(self,vx,vy):
		vx=vx/100.0
		vy=vy/100.0
		v = math.sqrt(vx ** 2 + vy ** 2)
		#logger.info(f"V = {v} m/s")
		return v

