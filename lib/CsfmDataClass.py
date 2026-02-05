from dataclasses import dataclass, field, InitVar
import struct
from pathlib import Path
from enum import IntEnum, auto
import FarcCreater

import logging

logger = logging.getLogger('CsfmDataClass')

DIFF_STR = '''pv_{pv_id:03d}.difficulty.{diff_str}.{number}.attribute.extra={extra}
pv_{pv_id:03d}.difficulty.{diff_str}.{number}.attribute.original={original}
pv_{pv_id:03d}.difficulty.{diff_str}.{number}.attribute.slide={is_slide}
pv_{pv_id:03d}.difficulty.{diff_str}.{number}.edition={extra}
pv_{pv_id:03d}.difficulty.{diff_str}.{number}.level=PV_LV_{diff_rate}
pv_{pv_id:03d}.difficulty.{diff_str}.{number}.level_sort_index=50
pv_{pv_id:03d}.difficulty.{diff_str}.{number}.script_file_name=rom/script/pv_{pv_id:03d}_{diff_str}{ex_tag}.dsc
pv_{pv_id:03d}.difficulty.{diff_str}.{number}.script_format=0x14050921
pv_{pv_id:03d}.difficulty.{diff_str}.{number}.version=1'''



class DSCCommandID(IntEnum):
    TIME = 1
    MIKU_DISP = 4
    CHANGE_FLELD = 14
    MOVIE_PLAY = 67
    MOVIE_DISP = 68
    MUSIC_PLAY = 25
    TARGET_FLYING_TIME = 58
    TARGET = 6
    PV_END = 32
    END = 0

class ComfyNoteID(IntEnum):
    TRIANGLE = 0
    SQUARE = auto()
    CROSS = auto()
    CIRCLE = auto()
    SLIDE_L = auto()
    SLIDE_R = auto()
    STAR = auto()

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

class Difficulty(IntEnum):
    EASY    = 0
    NORMAL  = auto()
    HARD    = auto()
    EXTREME = auto()
    ENCORE  = auto()

    EX_EASY    = auto()
    EX_NORMAL  = auto()
    EX_HARD    = auto()
    EX_EXTREME = auto()
    EX_ENCORE  = auto()

@dataclass
class ChartInfo:
    pv_id: int

    meta_data: dict = field(default_factory=dict)

    easy: dict = field(default_factory=dict)
    normal: dict = field(default_factory=dict)
    hard: dict = field(default_factory=dict)
    extreme: dict = field(default_factory=dict)
    ex_extreme: dict = field(default_factory=dict)

    def update_chart(self, info:dict) -> None:
        # 将IsEx转换为Difficulty枚举
        diff_type:int = info["Chart"]["Difficulty"]["Type"]
        if info["Chart"]["Difficulty"]["IsEx"]:
            diff_type += 5

        if diff_type == Difficulty.EASY:
            self.easy = info
        elif diff_type == Difficulty.NORMAL:
            self.normal = info
        elif diff_type == Difficulty.HARD:
            self.hard = info
        elif diff_type == Difficulty.EXTREME:
            self.extreme = info
        elif diff_type == Difficulty.EX_EXTREME:
            self.ex_extreme = info
        else:
            raise ValueError(f"未知的难度数: {diff_type}")

    def update_meta(self, info:dict[str, dict]) -> None:
        if info:
            self.meta_data = {
                "bpm":       int(info["Chart"]["Tempo Map"]["Tempo"][0]),
                "sabi_start":info["Chart"]["Time"]["Song Preview Start"],
                "sabi_play": info["Chart"]["Time"]["Song Preview Duration"],
                
                "song_path": info["Metadata"].get("Song File Name"),
                "movie_path":info["Metadata"].get("Movie File Name"),
                "song_title":info["Metadata"].get("Song Title", "名無し"),
                
                "arranger":info["Metadata"].get("Arranger", "名無し"),
                "lyrics":info["Metadata"].get("Lyricist", "名無し"),
                "music":info["Metadata"].get("Artist", "名無し"),
                
                "bg_path":  info["Metadata"].get("Background File Name"),
                "jk_path":  info["Metadata"].get("Cover File Name"),
                "logo_path":info["Metadata"].get("Logo File Name")
                }
        else:
            ValueError("元数据错误")


    def check_slide(self, data:dict) -> bool:
            return ComfyNoteID.SLIDE_L in data["Chart"]["Targets"]["Type"] or ComfyNoteID.SLIDE_R in data["Chart"]["Targets"]["Type"]
    
    def check_chance(self) -> bool:
        for chart_info in (self.easy,self.normal,self.hard,self.extreme,self.ex_extreme):
            if chart_info and True in chart_info["Chart"]["Targets"]["Chance"]:
                return True
        
        return False
    
    def export_chart(self) -> list[str]:
        from lib.ConvertDSC import DSCManager
        
        # 导出2D图
        logger.info("创建2D图")
        spr_dict = {"bg_path":self.meta_data["bg_path"],
                       "jk_path":self.meta_data["jk_path"],
                       "logo_path":self.meta_data["logo_path"]}

        spr_dict["bg_path"] = spr_dict["bg_path"] if spr_dict["bg_path"] else Path("default","SONG_BG_DUMMY.png").absolute()
        spr_dict["jk_path"] = spr_dict["jk_path"] if spr_dict["jk_path"] else Path("default","SONG_JK_DUMMY.png").absolute()

        FarcCreater.create_spr_sel_farc(self.pv_id,spr_dict,Path("output","rom","2d"))
        # 初始化
        logger.info("生成db并创建谱面")
        pv_db_list:list[str] = []
        dsc_managet = DSCManager()
        # 填写通用部分
        pv_db_list.append(f'pv_{self.pv_id:03d}.bpm={self.meta_data["bpm"]}')
        pv_db_list.append(f'pv_{self.pv_id:03d}.chainslide_failure_name=slide_ng03')
        pv_db_list.append(f'pv_{self.pv_id:03d}.chainslide_first_name=slide_long02a')
        pv_db_list.append(f'pv_{self.pv_id:03d}.chainslide_sub_name=slide_button08')
        pv_db_list.append(f'pv_{self.pv_id:03d}.chainslide_success_name=slide_ok03')
        pv_db_list.append(f'pv_{self.pv_id:03d}.date=20260205')
        # 添加难度pvdb
        # 添加easy
        if self.easy:
            dsc_managet.read_csfm_data(self.easy)
            dsc_managet.creat_dsc_file(self.pv_id,Path("output","rom","script"))

            check_slide = self.check_slide(self.easy)
            pv_db_list.extend(DIFF_STR.format(pv_id = self.pv_id, diff_str = "easy", 
                                              number = 0, ex_tag = "", diff_rate = self.easy["Chart"]["Difficulty"]["Level"],
                                              extra = 0, original = 1, is_slide = int(check_slide)).splitlines())
            pv_db_list.append(f"pv_{self.pv_id:03d}.difficulty.easy.length=1")
        else:
            pv_db_list.append(f"pv_{self.pv_id:03d}.difficulty.easy.length=0")
    
        # 添加encore
        pv_db_list.append(f"pv_{self.pv_id:03d}.difficulty.encore.length=0")
        
        # 添加extreme
        extreme_count = 0
        if self.extreme:
            dsc_managet.read_csfm_data(self.extreme)
            dsc_managet.creat_dsc_file(self.pv_id,Path("output","rom","script"))

            check_slide = self.check_slide(self.extreme)
            pv_db_list.extend(DIFF_STR.format(pv_id = self.pv_id, diff_str = "extreme", 
                                              number = extreme_count, ex_tag = "", diff_rate = self.extreme["Chart"]["Difficulty"]["Level"],
                                              extra = 0, original = 1, is_slide = int(check_slide)).splitlines())
            extreme_count += 1
        if self.ex_extreme:
            dsc_managet.read_csfm_data(self.ex_extreme)
            dsc_managet.creat_dsc_file(self.pv_id,Path("output","rom","script"))

            check_slide = self.check_slide(self.ex_extreme)
            pv_db_list.extend(DIFF_STR.format(pv_id = self.pv_id, diff_str = "extreme", 
                                              number = extreme_count, ex_tag = "_1", diff_rate = self.ex_extreme["Chart"]["Difficulty"]["Level"],
                                              extra = 1, original = 0, is_slide = int(check_slide)).splitlines())
            extreme_count += 1
        pv_db_list.append(f"pv_{self.pv_id:03d}.difficulty.extreme.length={extreme_count}")
        
        # 添加hard
        if self.hard:
            dsc_managet.read_csfm_data(self.hard)
            dsc_managet.creat_dsc_file(self.pv_id,Path("output","rom","script"))

            check_slide = self.check_slide(self.hard)
            pv_db_list.extend(DIFF_STR.format(pv_id = self.pv_id, diff_str = "hard", 
                                              number = 0, ex_tag = "", diff_rate = self.hard["Chart"]["Difficulty"]["Level"],
                                              extra = 0, original = 1, is_slide = int(check_slide)).splitlines())
            pv_db_list.append(f"pv_{self.pv_id:03d}.difficulty.hard.length=1")
        else:
            pv_db_list.append(f"pv_{self.pv_id:03d}.difficulty.hard.length=0")
        
        # 添加normal
        if self.normal:
            dsc_managet.read_csfm_data(self.normal)
            dsc_managet.creat_dsc_file(self.pv_id,Path("output","rom","script"))

            check_slide = self.check_slide(self.normal)
            pv_db_list.extend(DIFF_STR.format(pv_id = self.pv_id, diff_str = "normal", 
                                              number = 0, ex_tag = "", diff_rate = self.normal["Chart"]["Difficulty"]["Level"],
                                              extra = 0, original = 1, is_slide = int(check_slide)).splitlines())
            pv_db_list.append(f"pv_{self.pv_id:03d}.difficulty.normal.length=1")
        else:
            pv_db_list.append(f"pv_{self.pv_id:03d}.difficulty.normal.length=0")
        
        #添加其他信息
        pv_db_list.append(f"pv_{self.pv_id:03d}.hidden_timing=0.3")
        pv_db_list.append(f"pv_{self.pv_id:03d}.high_speed_rate=4") # 不同的飞入速度可能会不同，需要考量修正
        # 添加歌词
        pv_db_list.append(f"pv_{self.pv_id:03d}.lyric.001=###")
        pv_db_list.append(f"pv_{self.pv_id:03d}.lyric_en.001=###")
        #继续添加其他信息
        pv_db_list.append(f"pv_{self.pv_id:03d}.movie_file_name=rom/movie/pv_{self.pv_id:03d}.usm")
        pv_db_list.append(f"pv_{self.pv_id:03d}.movie_pv_type=ONLY")
        pv_db_list.append(f"pv_{self.pv_id:03d}.movie_surface=FRONT") # 调整亮度时需要单独出来处理
        pv_db_list.append(f"pv_{self.pv_id:03d}.performer.0.chara=MIK")
        pv_db_list.append(f"pv_{self.pv_id:03d}.performer.0.pv_costume=1")
        pv_db_list.append(f"pv_{self.pv_id:03d}.performer.0.type=VOCAL")
        pv_db_list.append(f"pv_{self.pv_id:03d}.performer.num=1")
        if self.check_chance():
            pv_db_list.append(f"pv_{self.pv_id:03d}.pvbranch_success_se_name=pvchange04")
        if self.meta_data["sabi_play"]:
            pv_db_list.append(f"pv_{self.pv_id:03d}.sabi.play_time={self.meta_data["sabi_play"]}")
        if self.meta_data["sabi_start"]:
            pv_db_list.append(f"pv_{self.pv_id:03d}.sabi.start_time={self.meta_data["sabi_start"]}")
        # 添加音效，目前使用默认音效
        pv_db_list.append(f"pv_{self.pv_id:03d}.se_name=01_button1")
        pv_db_list.append(f"pv_{self.pv_id:03d}.slide_name=slide_se13")
        pv_db_list.append(f"pv_{self.pv_id:03d}.slidertouch_name=slide_windchime")
        # 添加歌曲信息
        pv_db_list.append(f"pv_{self.pv_id:03d}.song_file_name=rom/sound/song/pv_{self.pv_id:03d}.ogg")
        pv_db_list.append(f"pv_{self.pv_id:03d}.song_name={self.meta_data["song_title"]}")
        pv_db_list.append(f"pv_{self.pv_id:03d}.song_name_en=Set Title in mod_pv_db")
        pv_db_list.append(f"pv_{self.pv_id:03d}.song_name_reading=あ")
        # 添加其他信息
        pv_db_list.append(f"pv_{self.pv_id:03d}.songinfo.arranger={self.meta_data["arranger"]}")
        pv_db_list.append(f"pv_{self.pv_id:03d}.songinfo.lyrics={self.meta_data["lyrics"]}")
        pv_db_list.append(f"pv_{self.pv_id:03d}.songinfo.music={self.meta_data["music"]}")
        pv_db_list.append(f"pv_{self.pv_id:03d}.songinfo_en.arranger=arranger_name")
        pv_db_list.append(f"pv_{self.pv_id:03d}.songinfo_en.lyrics=lyrics_name")
        pv_db_list.append(f"pv_{self.pv_id:03d}.songinfo_en.music=music_name")
        pv_db_list.append(f"pv_{self.pv_id:03d}.sudden_timing=0.6")

        return pv_db_list

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
    def flying_time(self) -> float: # 飞入时间精度为1ms，直接给出整数
        bpm = self.tempo * self.flying_time_factor
        return 60 / bpm * 4 * 1000
    
    @property
    def tick_time(self) -> float: # 时间精度为0.01ms，需要给小数
        return 60 * 1000 * 100 / self.tempo / 48
    
    
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
        if self.isproperties == False:
            self.position = (((self.tick + 192) % 384) * 4 + 192,768)
            self.angle = 0.00
            self.frequency = -2
            self.amplitude = 500
            self.distance = 1200

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
        dsc_angle = self.__convert_1000(self.angle)
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
    
    def __convert_1000(self,value:float) -> int:
        return int(value * 1000)
    
@dataclass
class NoteF2X(Note):
    islong : bool
    isdouble : bool
    reference_id : int
    previous_id : int
    next_id : int
    
    def __post_init__(self):
        raise NotImplementedError("Not implemented")