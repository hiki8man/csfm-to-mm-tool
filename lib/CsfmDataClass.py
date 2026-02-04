from dataclasses import dataclass, field, InitVar
import struct
from enum import IntEnum, auto

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

class ComfyNoteID(IntEnum):
    TRIANGLE = auto()
    SQUARE = auto()
    CROSS = auto()
    CIRCLE = auto()
    SLIDE_L = auto()
    SLIDE_R = auto()

class DSCNoteID(IntEnum):
    # Diva FT
    TRIANGLE = 0
    CIRCLE = 1
    CROSS = 2
    SQUARE = 3

    TRIANGLE_HOLD = 4
    CIRCLE_HOLD = 5
    CROSS_HOLD = 6
    SQUARE_HOLD = 7

    RANDOM = 8
    RANDOM_HOLD = 9
    PREVIOUS = 10

    SLIDE_L = 12
    SLIDE_R = 13

    CHAIN_SLIDE_L = 15
    CHAIN_SLIDE_R = 16

    CHANCE_TRIANGLE = 18
    CHANCE_CIRCLE = 19
    CHANCE_CROSS = 20
    CHANCE_SQUARE = 21

    CHANCE_SLIDE_L = 23
    CHANCE_SLIDE_R = 24

    # Diva X
    TRIANGLE_RUSH = 25
    CIRCLE_RUSH = 26
    CROSS_RUSH = 27
    SQUARE_RUSH = 28

    # Console Style(for NewClass)
    UP_W = 29
    RIGHT_W = 30
    DOWN_W = 31
    LEFT_W = 32

    TRIANGLE_LONG = 33
    CIRCLE_LONG = 34
    CROSS_LONG = 35
    SQUARE_LONG = 36

    STAR = 37
    STAR_LONG = 38
    STAR_W = 39
    CHANGE_STAR = 40
    LINK_STAR_START = 41
    LINK_STAR_END = 42
    STAR_RUSH = 43

    @staticmethod
    def get_normal_note_id(comfy_id:int) -> int:
        match comfy_id:
            case ComfyNoteID.TRIANGLE: return DSCNoteID.TRIANGLE
            case ComfyNoteID.SQUARE: return DSCNoteID.SQUARE
            case ComfyNoteID.CROSS: return DSCNoteID.CROSS
            case ComfyNoteID.CIRCLE: return DSCNoteID.CIRCLE
            case ComfyNoteID.SLIDE_L: return DSCNoteID.SLIDE_L
            case ComfyNoteID.SLIDE_R: return DSCNoteID.SLIDE_R

        raise ValueError(f"不支持的Note类型 {comfy_id}")
    
    @staticmethod
    def get_hold_note_id(comfy_id:int) -> int:
        match comfy_id:
            case ComfyNoteID.TRIANGLE: return DSCNoteID.TRIANGLE_HOLD
            case ComfyNoteID.SQUARE: return DSCNoteID.SQUARE_HOLD
            case ComfyNoteID.CROSS: return DSCNoteID.CROSS_HOLD
            case ComfyNoteID.CIRCLE: return DSCNoteID.CIRCLE_HOLD
        
        raise ValueError(f"不支持的HoldNote类型 {comfy_id}")
    
    @staticmethod
    def get_chain_note_id(comfy_id:int) -> int:
        match comfy_id:
            case ComfyNoteID.SLIDE_L: return DSCNoteID.CHAIN_SLIDE_L
            case ComfyNoteID.SLIDE_R: return DSCNoteID.CHAIN_SLIDE_R
        
        raise ValueError(f"不支持的ChainNote类型 {comfy_id}")
    
    @staticmethod
    def get_chance_note_id(comfy_id:int) -> int:
        match comfy_id:
            case ComfyNoteID.TRIANGLE: return DSCNoteID.CHANCE_TRIANGLE
            case ComfyNoteID.SQUARE: return DSCNoteID.CHANCE_SQUARE
            case ComfyNoteID.CROSS: return DSCNoteID.CHANCE_CROSS
            case ComfyNoteID.CIRCLE: return DSCNoteID.CHANCE_CIRCLE
            case ComfyNoteID.SLIDE_L: return DSCNoteID.CHANCE_SLIDE_L
            case ComfyNoteID.SLIDE_R: return DSCNoteID.CHANCE_SLIDE_R
        
        raise ValueError(f"不支持的ChanceNote类型 {comfy_id}")


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
        if self.ishold:
            return DSCNoteID.get_hold_note_id(comfy_id=self.type)
        elif self.ischance:
            return DSCNoteID.get_chance_note_id(comfy_id=self.type)
        elif self.ischain:
            return DSCNoteID.get_chain_note_id(comfy_id=self.type)
        else:
            return DSCNoteID.get_normal_note_id(comfy_id=self.type)

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
    islong : bool
    isdouble : bool
    reference_id : int
    previous_id : int
    next_id : int
    
    def __post_init__(self):
        raise NotImplementedError("Not implemented")