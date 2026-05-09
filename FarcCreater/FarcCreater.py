from enum import StrEnum
import kkdlib
from pathlib import Path
from PIL import Image, ImageFile, ImageOps
from PIL.Image import Transpose
from dataclasses import dataclass, field
from typing import ClassVar
import itertools
from collections.abc import Iterator


class Compression(StrEnum):
    '''
    纹理压缩格式，只给出了常用的四个  
    完整定义见 https://github.com/vixen256/KKdLib-sys/blob/2498f4604bf670b7af75f963ce95a3dd7527adaf/src/txp.rs#L27
    
    - BC7：MM+支持的纹理格式，清晰度比BC5好，需要较新显卡支持
    - BC5：官作使用的格式，清晰度比DXT5好些
    - DXT5：官作使用的格式
    - RGBA：不压缩，效果最好，但文件会很大
    '''
    BC7 = "BC7"
    ATI2 = "YCbCr"
    DXT5 = "DXT5"
    RGBA = "Uncompressed"

    def to_kkdlib_format(self) -> kkdlib.txp.Format: #type:ignore
        match self:
            case Compression.ATI2:
               return kkdlib.txp.Format.BC5 #type:ignore
            case Compression.DXT5:
                return kkdlib.txp.Format.BC3 #type:ignore
            case Compression.BC7:
                return kkdlib.txp.Format.BC7 #type:ignore
            case Compression.RGBA:
                return kkdlib.txp.Format.RGBA8 #type:ignore
    
    def default_spr_name(self) -> str:
        match self:
            case Compression.ATI2:
               return "MERGE_BC5COMP"
            case Compression.DXT5:
                return "MERGE_D5COMP"
            case Compression.BC7:
                return "MERGE_BC7COMP"
            case Compression.RGBA:
                return "MERGE_NOCOMP"

class SprResolutionMode:
    '''
    纹理缩放模式，只留下了可能会用到的  
    kkdlib缺少类型注释，编写一个类便于IDE提示  
    完整定义见 https://github.com/vixen256/KKdLib-sys/blob/2498f4604bf670b7af75f963ce95a3dd7527adaf/src/spr.rs#L23

    - HD：1280x720
    - FHD：1920x1080
    - UHD：3840x2160
    - WQVGA：480x272
    - QuarterHD：960x544
    '''
    HD = kkdlib.spr.ResolutionMode.HD #type:ignore
    FHD = kkdlib.spr.ResolutionMode.FHD #type:ignore
    UHD = kkdlib.spr.ResolutionMode.UHD #type:ignore
    WQVGA = kkdlib.spr.ResolutionMode.WQVGA #type:ignore
    QuarterHD = kkdlib.spr.ResolutionMode.QuarterHD #type:ignore


@dataclass
class TxpInfo:
    
    _id_count:ClassVar[Iterator[int]] = itertools.count() # 用于纹理图ID自增
    
    data:Image.Image
    compression:Compression
    
    id:int = field(init=False)
    name:str = field(init=False)
    width:float = field(init=False)
    height:float = field(init=False)
    
    def __post_init__(self) -> None:
        self.id = next(self._id_count)
        self.width = self.data.width
        self.height = self.data.height
        self.name = f"{self.compression.default_spr_name()}_{self.id}"

    @classmethod
    def reset_counter(cls) -> None:
        cls._id_count = itertools.count()

@dataclass
class SprInfo:
    name:str
    texture_id:int
    start_x:float
    start_y:float
    width:float
    height:float

class Farc:
    def __init__(self) -> None:
        TxpInfo.reset_counter()
        self.texture_dict:dict[str, TxpInfo] = {}
        self.sprit_dict  :dict[str, SprInfo] = {}
    
    def add_texture(self, data:Image.Image, compression:Compression) -> int:
        # 贴图比较特殊，我们不关注名字只关注index
        info = TxpInfo(data, compression)
        self.texture_dict.update({info.name:info})
        
        return info.id
    
    def add_sprite(self, info:SprInfo) -> None:
        self.sprit_dict.update({info.name:info})
    
    def _get_texture_index(self, _name) -> int:
        for name,info in self.texture_dict.items():
            if name == _name:
                return info.id
        return -1
    
    def _convert_to_texture(self, info:TxpInfo):
        '''
        新旧版本命名不一致，在这里进行统一处理
        '''
        if info.compression is Compression.ATI2:
            if hasattr(kkdlib.txp.Texture,"py_ycbcr_from_rgba_gpu"): #type:ignore
                return kkdlib.txp.Texture.py_ycbcr_from_rgba_gpu( #type:ignore
                    info.width, 
                    info.height, 
                    info.data.tobytes()
                ) 
            else:
                return kkdlib.txp.Texture.encode_ycbcr( #type:ignore
                    info.width, 
                    info.height, 
                    info.data.tobytes()
                ) 
        else:
            if hasattr(kkdlib.txp.Texture,"py_from_rgba_gpu"): #type:ignore
                return kkdlib.txp.Texture.py_from_rgba_gpu(  #type:ignore
                    info.width, 
                    info.height, 
                    info.data.tobytes(), 
                    info.compression.to_kkdlib_format()
                )
            else:
                return kkdlib.txp.Texture.py_from_rgba( #type:ignore
                    info.width, 
                    info.height, 
                    info.data.tobytes(), 
                    info.compression.to_kkdlib_format()
                ) 
    
    def export_farc(
        self, 
        export_name: str, 
        export_path: Path, 
        resolution_mode: SprResolutionMode = SprResolutionMode.FHD
    ) -> None:

        txp = kkdlib.txp.Set() #type:ignore
        name_list:list[str] = [] #记录Texture名称
        # 添加texture
        for name,info in self.texture_dict.items():
            name_list.append(name)
            txp.add_file(self._convert_to_texture(info))
   
        spr_bin = kkdlib.spr.Set() #type:ignore
        spr_bin.set_txp(txp, name_list)
        spr_bin.ready = True

        #添加sprite
        for name,spr_info in self.sprit_dict.items():
            info = kkdlib.spr.Info() #type:ignore
            # 配置spr信息
            info.texid = spr_info.texture_id
            info.resolution_mode = resolution_mode
            info.px = spr_info.start_x
            info.py = spr_info.start_y
            info.width = spr_info.width
            info.height = spr_info.height
            #添加到spr
            spr_bin.add_spr(info, name)

        farc = kkdlib.farc.Farc() #type:ignore
        farc.add_file_data(f"{export_name}.bin", spr_bin.to_buf())
        farc.write(str(export_path.joinpath(f"{export_name}.farc")), False, False)
