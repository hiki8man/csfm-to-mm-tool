from enum import Enum, auto
import kkdlib
from pathlib import Path
from PIL import Image
from dataclasses import dataclass, field
from typing import ClassVar

class Compression(Enum):
    BC7 = "BC7"
    ATI2 = "YCbCr"
    DXT5 = "DXT5"
    RGBA = "Uncompressed"

    def __str__(self):
        return f"{self.value}"

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
                return "MERGE_DT5COMP"
            case Compression.BC7:
                return "MERGE_BC7COMP"
            case Compression.RGBA:
                return "MERGE_NOCOMP"
@dataclass
class txp_info:
    _id_count:ClassVar[int] = 0
    
    id:int = field(init=False)
    data:Image.ImageFile.ImageFile
    width:float = field(init=False)
    height:float = field(init=False)
    
    def __post_init__(self) -> None:
        self.id = self._id_count
        type(self)._id_count += 1
        
        self.width = self.data.width
        self.height = self.data.height
        
@dataclass
class spr_info:
    texture_name:str
    start_x:float
    start_y:float
    width:float
    height:float

class Farc:
    def __init__(self, compression:Compression = Compression.ATI2) -> None:
        self.compression:Compression = compression
        self.texture_dict:dict[str, txp_info] = {}
        self.sprit_dict  :dict[str, spr_info] = {}
    
    def add_texture(self, data:Image.ImageFile.ImageFile) -> None:
        info = txp_info(data)
        name:str = f"{self.compression.default_spr_name()}_{info.id}"
        self.texture_dict.update({name:info})
    
    def add_sprite(self, name:str, setting:dict) -> None:
        info = spr_info(**setting)
        self.sprit_dict.update({name:info})
    
    def _get_texture_index(self, _name) -> int:
        for name,info in self.texture_dict.items():
            if name == _name:
                return info.id
        return -1
    
    def export_farc(self, export_name:str, export_path:Path) -> None:
        txp = kkdlib.txp.Set() #type:ignore
        name_list:list[str] = [] #记录Texture名称

        # 添加texture
        for name,info in self.texture_dict.items():
            name_list.append(name)

            if self.compression is Compression.ATI2:
                txp.add_file(
                    kkdlib.txp.Texture.py_ycbcr_from_rgba_gpu(info.width, info.height, info.data.tobytes()) #type:ignore
                    )
            else:
                txp.add_file(
                    kkdlib.txp.Texture.py_ycbcr_from_rgba_gpu(info.width, info.height, info.data.tobytes(), self.compression.to_kkdlib_format())#type:ignore
                    )
        
        spr_bin = kkdlib.spr.Set() #type:ignore
        spr_bin.set_txp(txp, name_list)
        spr_bin.ready = True

        #添加sprite
        for name,txp_info in self.sprit_dict.items():
            info = kkdlib.spr.Info() #type:ignore
            # 配置spr信息
            info.texid = self._get_texture_index(txp_info.texture_name)
            info.resolution_mode = kkdlib.spr.ResolutionMode.FHD #type:ignore
            info.px = txp_info.start_x
            info.py = txp_info.start_y
            info.width = txp_info.width
            info.height = txp_info.height
            #添加到spr
            spr_bin.add_spr(info, name)

        farc = kkdlib.farc.Farc() #type:ignore
        farc.add_file_data(f"{export_name}.bin", spr_bin.to_buf())
        farc.write(export_path.joinpath(f"{export_name}.farc"), False, False)

def create_spr_sel(spr_sel_dict:dict[str,int|Image.ImageFile.ImageFile], export_path:Path, compression:Compression = Compression.ATI2):
    assert isinstance(spr_sel_dict["id"],int)
    song_id = int(spr_sel_dict["id"])
    
    pass
