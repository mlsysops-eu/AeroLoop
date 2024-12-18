import struct

from dataclasses import dataclass, asdict, field
from dataclass_struct import STRUCT_TYPE, dataclass_struct

from enum import Enum


class MsgTypes(Enum):
	UAV_STATUS = 1

# Example for serialization of dataclasses 
# from dataclass_struct import STRUCT_TYPE, dataclass_struct

# @dataclass_struct
# class Test:
# 	Type: int = field(default = MsgTypes.TRACTOR_INFO.value, metadata={STRUCT_TYPE:'>i'})
# 	param1: float = field(default = 0, metadata={STRUCT_TYPE:'>f'})
# 	param2: float = field(default = 0, metadata={STRUCT_TYPE:'>f'})


@dataclass
class UAVStatus:
	Type: int = MsgTypes.UAV_STATUS.value
	Status: int = 0



@dataclass
class Position:
	lon: float = 0.0
	lat: float = 0.0
	alt: float = 0.0

@dataclass
class NSPos:
	x: float = 0.0
	y: float = 0.0
	z: float = 0.0
