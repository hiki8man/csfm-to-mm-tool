from dataclasses import dataclass, field, InitVar
import struct
from enum import IntEnum

NORMAL_NOTE = 3

class DSCCommandID(IntEnum):
    TIME = 1
    CHANGE_FLELD = 14
    MOVIE_PLAY = 67
    MOVIE_DISP = 68
    MUSIC_PLAY = 25
    TARGET_FLYING_TIME = 58
    TARGET = 6
    PV_END = 32
    END = 0

@dataclass(frozen=True)
class VariableDataIndex:
    item_size : int
    data_size : int
    address   : int

    @property
    def item_count(self):
        return int(self.data_size / self.item_size)

@dataclass
class BPM:
    tick : int = 0
    tempo : float = 160.0
    flying_time_factor : float = 1.0

    @property
    def flying_time(self) -> int:
        bpm = self.tempo * self.flying_time_factor
        return int(60 / bpm * 4 * 1000) 
    
    @property
    def tick_time(self) -> int:
        return int(60 * 1000 * 100 / self.tempo / 48)
    
@dataclass
class Note:
    tick : int
    type : int
    isproperties : bool
    ishold : bool
    ischain : bool
    ischance : bool
    position : tuple[float,float]
    angle : float
    frequency : int
    amplitude : int
    distance : float

    def __post_init__(self):
        self.amplitude = int(self.amplitude)
        self.frequency = int(self.frequency)

        if self.ishold:
            self.ischain,self.ischance = (False,False)
        elif self.ischain:
            self.ischance = False

    @property
    def dsc_data(self) -> bytes:
        dsc_note_id = self.__get_dsc_notetype()
        dsc_pos_x = self.__convert_250(self.position[0])
        dsc_pos_y = self.__convert_250(self.position[1])
        dsc_angle = self.__convert_100(self.angle * 100)
        dsc_distance = self.__convert_250(self.distance)

        binary_data = struct.pack(
            "<8i",
            DSCCommandID.TARGET,
            dsc_note_id,
            dsc_pos_x,dsc_pos_y,
            dsc_angle,
            dsc_distance,self.amplitude,self.frequency
            )

        return binary_data
    
    def __get_dsc_notetype(self) -> int:
        dsc_type = self.__dsc_note_id()
        if self.ishold and dsc_type <= NORMAL_NOTE:
            return dsc_type + 4
        elif self.ischance:
            return dsc_type + 18
        elif self.ischain and dsc_type > NORMAL_NOTE:
            return dsc_type + 9
        elif dsc_type > NORMAL_NOTE:
            return dsc_type + 6
        else:
            return dsc_type

    def __dsc_note_id(self) -> int:
        '''
        将id转换为dsc的id
        '''
        if self.type == 1:
            return 3
        elif self.type == 3:
            return 1
        else:
            return self.type

    def __convert_250(self,value:float) -> int:
        return int(value * 250)
    
    def __convert_100(self,value:float) -> int:
        return int(value * 100)
    
@dataclass
class NoteF2X(Note):
    end_tick : int
    islong : bool
    isdouble : bool
    next_id : int
    previous_id : int
    reference_id : int

    raise NotImplementedError("Not implemented")