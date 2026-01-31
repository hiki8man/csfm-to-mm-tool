import struct
from pathlib import Path
from typing import BinaryIO
from lib import ReadCstring
from lib.CsfmDataClass import VariableDataIndex
import logging

logger = logging.getLogger('CsfmReader')

def _get_bool(data: int, bits: int = 4):
    return tuple(bool((data >> i) & 1) for i in range(bits-1, -1, -1))

class _CsfmReader:
    
    def __init__(self) -> None:
        self.string_address : dict = {}
        self.data_dict : dict = {"Header":{"Magic":None,
                                           "Version":None,
                                           "Endianness":None,
                                           "PointerSize":None,
                                           "CreationTime":None,
                                           "CharacterEncoding":None},

                                 "CreatorInfo":{"PointerSize":None,
                                                "Name":None,
                                                "Platform":None,
                                                "Architecture":None,
                                                "Author":None,
                                                "CommitHash":None,
                                                "CommitTime":None,
                                                "CommitNumber":None,
                                                "Branch":None,
                                                "CompileTime":None,
                                                "BuildConfig":None},

                                 "Metadata":{"Song Title":None,
                                             "Song File Name":None,
                                             "Movie File Name":None,
                                             "Background File Name":None,
                                             "Cover File Name":None,
                                             "Logo File Name":None},

                                 "Chart":{},

                                 "Debug":"Reserved"}
    
    def __getstring(self,address: bytes) -> str:
        logger.debug(f"获取 {address} 的对应地址")
        address = struct.unpack("<q",address)[0]
        return self.string_address[address]

    def readcsfm(self, _path : Path) -> dict:
        logger.info(f"正在读取 {_path}")
        with open(_path, "rb") as f:
            self.head_reader(f)
            self.creator_info_reader(f)
            self.data_reader(f)
        return self.data_dict

    def head_reader(self, file: BinaryIO) -> None:
        logger.info("开始读取头部信息")
        # [NOTE] 目前没有对数据是否为小端做实际检测，以后可能会出现bug
        # 先调整逻辑判断便于后续修正
        logger.debug("读取魔数信息")
        self.data_dict["Header"]["Magic"] = file.read(4)
        logger.debug("跳转到指定地址读取大小端信息")
        file.seek(8) # 首先读取大小端，大端为B，小端为L
        self.data_dict["Header"]["Endianness"] = struct.unpack("1sx", file.read(2))[0]
        logger.debug("跳转回前面没有读取的部分读取版本号")
        file.seek(4) # 跳回去读版本号
        self.data_dict["Header"]["Version"] = "%i.%i".format(*struct.unpack("<hh", file.read(4)))
        logger.debug("跳转到没有被读取的部分读取剩余的头部信息")
        file.seek(10) # 跳到后面读剩下的值
        self.data_dict["Header"]["PointerSize"] = struct.unpack("<h4x", file.read(6))[0]
        self.data_dict["Header"]["CreationTime"] = struct.unpack("<q", file.read(8))[0]
        self.data_dict["Header"]["CharacterEncoding"] = ReadCstring.ReadCstringFile2(file, file.tell())
        pass

    def creator_info_reader(self, file: BinaryIO) -> None:
        offset = self.data_dict["Header"]["PointerSize"]
        file.seek(offset)

        self.data_dict["CreatorInfo"]["PointerSize"] = struct.unpack("<q", file.read(8))[0]
        keys = list(self.data_dict["CreatorInfo"].keys())

        for index in range(0, int(self.data_dict["CreatorInfo"]["PointerSize"]/8 - 1)):
            file.seek(offset) # 跳转到指定位置
            if index >= len(keys):
                logger.debug(f"未知来源数据：{ReadCstring.ReadCstringFile2(file, struct.unpack("<q", file.read(8))[0])}")
            elif keys[index] == "PointerSize":
                pass
            else:
                self.data_dict["CreatorInfo"][keys[index]] = ReadCstring.ReadCstringFile2(file, struct.unpack("<q", file.read(8))[0])

            offset += 8

    def __getstring_dict(self,file: BinaryIO, data_offset: int):
        file.seek(data_offset)
        offset = struct.unpack("<q",file.read(8))[0]
        self.string_address = ReadCstring.ReadCstringFile(file,offset)
    
    def data_reader(self, file: BinaryIO) -> None:
        file.seek(self.data_dict["Header"]["PointerSize"]+self.data_dict["CreatorInfo"]["PointerSize"])
        data_len = struct.unpack("<q",file.read(8))[0]
        data_offset = struct.unpack("<q",file.read(8))[0]
        self.__getstring_dict(file,data_offset)
        for _ in range(data_len):
            file.seek(data_offset)
            string = self.__getstring(file.read(8))
            address = struct.unpack("<q",file.read(8))[0]
            match string:
                case "Metadata":
                    self.metadata_reader(file, address)
                case "Chart":
                    self.chart_reader(file, address)
                case "Debug":
                    self.data_dict["Debug"] = ReadCstring.ReadCstringFile2(file, address)
                case unknow_info:
                    print(f"未知的数据，将会被舍弃 {unknow_info}")
            data_offset += 32

    def metadata_reader(self, file: BinaryIO, offset: int) -> None:
        address_dict = self.__get_data_address(file, offset)
        for key_address,value_address in address_dict.items():
            assert (isinstance(key_address,bytes) and isinstance(value_address,bytes))

            key = self.__getstring(key_address)
            value = self.__getstring(value_address)
            match key:
                case "Song Title":
                    self.data_dict["Metadata"][key] = value
                case "Song File Name":
                    self.data_dict["Metadata"][key] = Path(value)
                case "Movie File Name":
                    self.data_dict["Metadata"][key] = Path(value)
                case "Background File Name":
                    self.data_dict["Metadata"][key] = Path(value)
                case "Cover File Name":
                    self.data_dict["Metadata"][key] = Path(value)
                case "Logo File Name":
                    self.data_dict["Metadata"][key] = Path(value)
                case "Track Number":
                    pass #不需要其他乱七八糟的数据
                case "Disk Number":
                    pass #不需要其他乱七八糟的数据

    def chart_reader(self, file: BinaryIO, offset: int) -> None:
        address_dict = self.__get_data_address(file, offset)
        for key_address,value_address in address_dict.items():
            assert (isinstance(key_address,bytes) and isinstance(value_address,bytes))

            key = self.__getstring(key_address)
            offset = struct.unpack("<q",value_address)[0]
            match key:
                case "Scale":
                    pass #不明数据，暂不读取
                case "Time":
                    self.data_dict["Chart"][key] = dict()
                    self.__get_time_setting(file, offset)
                case "Targets":
                    self.data_dict["Chart"][key] = dict()
                    self.__get_target(file, offset)
                case "Tempo Map":
                    self.data_dict["Chart"][key] = dict()
                    self.__get_tempo_map(file, offset)
                case "Button Sounds":
                    self.data_dict["Chart"][key] = tuple()
                    self.__get_button_sound_setting(file, offset)
                case "Difficulty":
                    self.data_dict["Chart"][key] = dict()
                    self.__get_difficulty_setting(file, offset)

    def __get_target(self, file: BinaryIO, offset: int) -> None:
        '''
        获取Note数据  
        '''
        data_dict = self.__get_timeline_data(file, offset)
        target_dict = self.data_dict["Chart"]["Targets"]
        for key,value in data_dict.items():
            file.seek(value.address)
            match key:
                case "Tick":
                    target_dict[key] = self.__unpack_data(file, value, "i")
                case "Type":
                    target_dict[key] = self.__unpack_data(file, value, "b")
                case "Properties"|"Hold"|"Chain"|"Chance":
                    target_dict[key] = self.__unpack_data(file, value, "?")
                case "Position":
                    target_dict[key] = self.__unpack_data(file, value, "f", is_vet2=True)
                case "Angle"|"Frequency"|"Amplitude"|"Distance":
                    target_dict[key] = self.__unpack_data(file, value, "f")
                case unknow_param:
                    logger.debug(f"未知参数: {unknow_param}")
                    pass

    def __get_tempo_map(self, file: BinaryIO, offset: int) -> None:
        '''
        获取BPM变速相关设置
        Flags为特殊开关
        Flags //二进制转int保存的4字节数值
                从二进制分析
                第一位是bpm是否勾选改变
                第二位是Flying Time
                第三位是拍号是否改变
        '''
        data_dict = self.__get_timeline_data(file, offset)
        temp_map_dict = self.data_dict["Chart"]["Tempo Map"]
        for key,value in data_dict.items():
            file.seek(value.address)
            match key:
                case "Tick":
                    temp_map_dict[key] = self.__unpack_data(file, value, "i")
                case "Tempo"|"Flying Time Factor":
                    temp_map_dict[key] = self.__unpack_data(file, value, "f")
                case "Time Signature":
                    temp_map_dict[key] = self.__unpack_data(file, value, "h", is_vet2=True)
                case "Flags":
                    data = self.__unpack_data(file, value, "i")
                    temp_map_dict[key] = tuple(_get_bool(value) for value in data if isinstance(value,int))

    def __get_time_setting(self, file: BinaryIO, offset: int) -> None:
        '''
        获取谱面时间相关设置  
        如果总时长为0则设置为90秒
        '''
        DataDict = self.__get_data_address(file, offset)
        for key_address,value_byte in DataDict.items():
            assert (isinstance(key_address,bytes) and isinstance(value_byte,bytes))

            key = self.__getstring(key_address)
            value = struct.unpack("<d",value_byte)[0]
            if key == "Duration" and value == 0.0:
                self.data_dict["Chart"]["Time"][key] = 90.0
            else:
                self.data_dict["Chart"]["Time"][key] = value

    def __get_button_sound_setting(self, file: BinaryIO, offset: int) -> None:
        '''
        获取按键音设置  
        返回的是按键音编号，需要一个字典对应按键音名称便于设置
        '''
        length, address = self.__get_data_length(file, offset)
        file.seek(address)
        self.data_dict["Chart"]["Button Sounds"] = struct.unpack("<bbbb",file.read(length))

    def __get_difficulty_setting(self, file: BinaryIO, offset: int) -> None:
        '''
        获取难度设置
        '''
        file.seek(offset)
        file_data = file.read(4)
        data = struct.unpack("b?bb",file_data)
        self.data_dict["Chart"]["Difficulty"] = {"Type":data[0],
                                                 "IsEx":data[1],
                                                 "Level":f"{data[2]:02}_{data[3]}"}
    
    def __get_timeline_data(self, file: BinaryIO, offset: int) -> dict[str,VariableDataIndex]:
        '''
        时间轴相关数据对应索引位置  
        用于BPM与Note
        '''
        file.seek(offset)
        #暂时不清楚valuelength有什么作用，因为我们完全可以根据数据长度获取到值的数量
        #也许只是为了方便验证数量值，姑且先用一个变量保存
        value_length,key_length,address = struct.unpack("<qqq",file.read(24))
        data_address_dict = {}
        file.seek(address)
        for _ in range(key_length):
            key = self.__getstring(file.read(8))
            value = VariableDataIndex(*struct.unpack("<qqq",file.read(24)))
            data_address_dict[key] = value
            file.seek(16,1)

        return data_address_dict

    def __get_data_length(self, file: BinaryIO, offset: int) -> tuple[int,int]:
        file.seek(offset)
        return struct.unpack("<qq",file.read(16))

    def __get_data_address(self, file: BinaryIO, offset: int) -> dict[int,int]:
        length, address = self.__get_data_length(file, offset)
        file.seek(address)
        address_dict = {}
        
        for _ in range(length):
            key = file.read(8)
            value = file.read(8)
            address_dict[key] = value
            file.seek(16,1)
        
        return address_dict
    
    def __unpack_data(self, file: BinaryIO, info: VariableDataIndex, type: str, is_vet2: bool =False):
        data = file.read(info.data_size)
        if not is_vet2:
            return struct.unpack(f"<{info.item_count}{type}",data)
        unpack_data = struct.unpack(f"<{info.item_count*2}{type}",data)
        return list(zip(unpack_data[::2],unpack_data[1::2]))
    

def read_csfm(_file_path: Path) -> dict:

    return _CsfmReader().readcsfm(_file_path)
