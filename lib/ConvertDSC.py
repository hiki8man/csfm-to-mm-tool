from .CsfmReader import read_csfm
from .CsfmDataClass import BPM,Note,DSCCommandID,Difficulty
from pathlib import Path
from collections import defaultdict
from pprint import pprint
import struct
from collections.abc import Generator

DSC_HEAD = b"\x21\x09\x05\x14"

class NoteManager:
    def __init__(self) -> None:
        '''
        使用列表储存Note数据
        利用列表pop（末端取出）效率更快的特性颠倒了列表
        时间具体时间仍然由TickManager处理
        '''
        self.data_list : list[Note] = []
        self.data : tuple[Note]

    def check_last_data(self, tick : int) -> bool:
        return len(self.data_list) > 0 and self.data_list[-1].tick == tick

    def read_note(self, data_dict : dict) -> None:
        data_zip : zip = zip(data_dict["Tick"],
                             data_dict["Type"],
                             data_dict["Properties"],
                             data_dict["Hold"],data_dict["Chain"],data_dict["Chance"],
                             data_dict["Position"],data_dict["Angle"],
                             data_dict["Frequency"],data_dict["Amplitude"],data_dict["Distance"])
        self.data_list.clear()
        for data_tuple in data_zip:
            self.data_list.append(Note(*data_tuple))
        self.data_list.reverse()

    def get_note(self) -> Generator[tuple[Note], None, None]:
        while len(self.data_list) > 0:
            yield self.get_last_note()
    
    def get_last_note(self) -> tuple[Note]:
        last_note_list = []
        tick = self.data_list[-1].tick
        while self.check_last_data(tick):
            note_data = self.data_list.pop()
            last_note_list.append(note_data)
        self.data = tuple(last_note_list)
        return self.data

class BPMManager:
    """
    使用列表记录不同tick时的BPM点
    与NoteManager一样利用弹出的方式实现高速查询
    时间计算全程交给TickManager处理
    后续可能需要用于计算家用机长条，直接使用self。data也许可以解决
    """
    def __init__(self) -> None:
        self.data_list : list[BPM] = []

    def check_last_data(self, tick : int) -> bool:
        return len(self.data_list) == 0 and self.data_list[-1].tick <= tick

    def read_bpm(self, data_dict : dict) -> None:
        data_zip : zip = zip(data_dict["Tick"],
                             data_dict["Tempo"],
                             data_dict["Flying Time Factor"])
        self.data_list.clear()
        for data_tuple in data_zip:
            self.data_list.append(BPM(*data_tuple))

class TickManager:
    '''
    负责提供实际的时间点与BPM值
    target_flying_time记录是否需要写入飞入时间
    -1使用于一开始计算的时候
    '''
    def __init__(self, _manager:BPMManager) -> None:
        self.bpm_manager:BPMManager = _manager
        self.target_flying_time:int = -1
        
    def tick_to_time(self, tick:int) -> tuple[dict[int,bytes], int]:
        pre_bpm = None
        now_bpm = BPM()
        last_change_time = 0
        if self.bpm_manager.data_list == []:
            raise ValueError("列表中无BPM变速")
        
        for bpm in self.bpm_manager.data_list:
            if now_bpm != None:
                pre_bpm = now_bpm
            elif bpm.tick > tick:
                break
            now_bpm = bpm
            if pre_bpm != None:
                last_change_time += (now_bpm.tick - pre_bpm.tick) * pre_bpm.tick_time
        
        after_change_tick = tick - now_bpm.tick
        if pre_bpm == None or after_change_tick >= 192:
            """
            太好了是无BPM变速我们有救了
            """
            flying_time = now_bpm.flying_time
        else:
            """
            变速给我去死啊啊啊啊啊啊啊
            """
            flying_time = pre_bpm.flying_time - (now_bpm.flying_time - pre_bpm.flying_time) * (192 / after_change_tick)

        time = int(now_bpm.tick_time * after_change_tick + last_change_time - (flying_time * 100))
        return self.get_dsc_data(int(flying_time), time) , time
    
    def get_dsc_data(self, flying_time:int, time:int) -> dict[int,bytes]:
        dsc_dict = defaultdict(bytes)
        if flying_time == self.target_flying_time:
            dsc_dict[time] = b''
        else:
            self.target_flying_time = flying_time
            dsc_dict[time] = struct.pack("<ii",DSCCommandID.TARGET_FLYING_TIME,flying_time)
        return dsc_dict

class DSCManager:

    def __init__(self) -> None:
        self.difficulty_str : str = "unknow" 
        self.chart_offset : float = 0.0
        self.bpm_manager : BPMManager = BPMManager()
        self.note_mananger : NoteManager = NoteManager()
        self.tick_manager : TickManager = TickManager(self.bpm_manager)

        self.on_bpm_change : bool = True
        self.have_movie : bool = False
        self.have_song : bool = False

        self.command_time_dict : dict[str,float] ={
            "song_offset":0.0,
            "movie_offset":0.0,
            "pv_end_time":0.0,}

    def read_csfm_data(self, csfm_data: dict) -> None:
        chart_data_dict = csfm_data["Chart"]
        # 检查文件是否存在，不存在的文件将offset设置为0
        self.have_movie = csfm_data["Metadata"]["Movie File Name"] and csfm_data["Metadata"]["Movie File Name"].exists()
        self.have_song = csfm_data["Metadata"]["Song File Name"] and csfm_data["Metadata"]["Song File Name"].exists()

        self.bpm_manager.read_bpm(chart_data_dict["Tempo Map"])
        self.note_mananger.read_note(chart_data_dict["Targets"])
        self.__updata_time_var_dict(chart_data_dict["Time"])
        self.__updata_difficulty_str(chart_data_dict["Difficulty"])
    
    def creat_dsc_file(self, pv_id: int, export_path:Path, dsc_head: bytes = DSC_HEAD) -> None:
        DSC_FILE_NAME = "_".join(("pv", str(pv_id), self.difficulty_str))
        DSC_PATH = export_path.joinpath(f"{DSC_FILE_NAME}.dsc")

        with open(DSC_PATH,"wb+") as f:
            f.write(dsc_head)
            dsc_dict = self.get_dsc_dict()
            sort_key = sorted(dsc_dict.keys())
            for key in sort_key:
                f.write(struct.pack("<2i",DSCCommandID.TIME,key))
                f.write(dsc_dict[key])
    
    def get_event_dict(self) -> dict[int,bytes]:
        event_dict = defaultdict(bytes)
        for key in self.command_time_dict.keys():
            match key:
                case "song_offset":
                    time_dsc = int(self.command_time_dict[key]*1000*100)
                    event_dict[time_dsc] += struct.pack("<i",DSCCommandID.MUSIC_PLAY)
                
                case "movie_offset":
                    time_dsc = int(self.command_time_dict[key]*1000*100)
                    event_dict[time_dsc] += struct.pack("<4i",DSCCommandID.MOVIE_PLAY,1,
                                                              DSCCommandID.MOVIE_DISP,1)
                case "pv_end_time":
                    time_dsc = int(self.command_time_dict[key]*1000*100)
                    event_dict[time_dsc] += struct.pack("<2i",DSCCommandID.PV_END,
                                                              DSCCommandID.END)
        return event_dict
    
    def get_note_dict(self) -> dict[int,bytes]:
        note_dict = defaultdict(bytes)
        for note_tuple in self.note_mananger.get_note():
            tick = note_tuple[0].tick
            data_dict, time = self.tick_manager.tick_to_time(tick)
            for note in note_tuple:
                data_dict[time] += note.dsc_data
            note_dict.update(data_dict)
        return note_dict

    def get_dsc_dict(self) -> dict[int,bytes]:
        event_dict = self.get_event_dict()
        note_dict = self.get_note_dict()
        common_key = event_dict.keys() & note_dict.keys()
        for key in event_dict.keys():
            if key in common_key:
                note_dict[key] = event_dict[key] + note_dict[key]
            else:
                note_dict[key] = event_dict[key]
        return note_dict

    def __updata_time_var_dict(self,time_dict:dict) -> None:
        if "Song Offset" in time_dict: # 取相反数转换为dsc里面的单位时间
            song_offset = -time_dict["Song Offset"] if self.have_song else 0.0
            self.command_time_dict.update({"song_offset":song_offset})

        if "Movie Offset" in time_dict: # 取相反数转换为dsc里面的单位时间
            movie_offset = -time_dict["Movie Offset"] if self.have_movie else 0.0
            self.command_time_dict.update({"movie_offset":movie_offset})

        if "Duration" in time_dict:
            self.command_time_dict.update({"pv_end_time":time_dict["Duration"]})

        self.__updata_chart_offset()
    
    def __updata_chart_offset(self) -> None:
        song_offset = self.command_time_dict["song_offset"]
        movie_offset = self.command_time_dict["movie_offset"]

        min_offset = min(song_offset, movie_offset, 0.0)
    
        self.chart_offset = abs(min_offset)
        self.command_time_dict["song_offset"] = song_offset + self.chart_offset
        self.command_time_dict["movie_offset"] = movie_offset + self.chart_offset


    def __updata_difficulty_str(self, diff_dict:dict) -> None:
        match diff_dict["Type"]:
            case Difficulty.EASY:
                self.difficulty_str = "easy"
            case Difficulty.NORMAL:
                self.difficulty_str = "normal"
            case Difficulty.HARD:
                self.difficulty_str = "hard"
            case Difficulty.EXTREME:
                self.difficulty_str = "extreme"
            case _:
                self.difficulty_str = "unknow"
        if diff_dict['IsEx']:
            self.difficulty_str += "_1"


if __name__ == "__main__":
    file_path = Path("Untitled Chart6.csfm")
    csfm_data = read_csfm(file_path)
    dsc_managet = DSCManager()
    dsc_managet.read_csfm_data(csfm_data)
    dsc_managet.creat_dsc_file(2222, Path("output"))
