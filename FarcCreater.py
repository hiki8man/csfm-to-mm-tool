from enum import Enum, auto
import kkdlib
from pathlib import Path
from PIL import Image, ImageFile, ImageOps
from PIL.Image import Transpose
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
                return "MERGE_D5COMP"
            case Compression.BC7:
                return "MERGE_BC7COMP"
            case Compression.RGBA:
                return "MERGE_NOCOMP"
@dataclass
class txp_info:
    _id_count:ClassVar[int] = 0
    
    id:int = field(init=False)
    data:Image.Image
    width:float = field(init=False)
    height:float = field(init=False)
    
    def __post_init__(self) -> None:
        self.id = self._id_count
        type(self)._id_count += 1
        
        self.width = self.data.width
        self.height = self.data.height
        
@dataclass
class spr_info:
    texture_id:int
    start_x:float
    start_y:float
    width:float
    height:float

class Farc:
    def __init__(self, compression:Compression = Compression.ATI2) -> None:
        self.compression:Compression = compression
        self.texture_dict:dict[str, txp_info] = {}
        self.sprit_dict  :dict[str, spr_info] = {}
    
    def add_texture(self, data:Image.Image) -> int:
        info = txp_info(data)
        name:str = f"{self.compression.default_spr_name()}_{info.id}"
        self.texture_dict.update({name:info})
        
        return info.id
    
    def add_sprite(self, name:str, setting:tuple) -> None:
        info = spr_info(*setting)
        self.sprit_dict.update({name:info})
    
    def _get_texture_index(self, _name) -> int:
        for name,info in self.texture_dict.items():
            if name == _name:
                return info.id
        return -1
    
    def export_farc(self, export_name:str, export_path:Path, aft_mode:bool=False) -> None:
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
                    kkdlib.txp.Texture.py_from_rgba_gpu(info.width, info.height, info.data.tobytes(), self.compression.to_kkdlib_format())#type:ignore
                    )
        
        spr_bin = kkdlib.spr.Set() #type:ignore
        spr_bin.set_txp(txp, name_list)
        spr_bin.ready = True

        #添加sprite
        for name,txp_info in self.sprit_dict.items():
            info = kkdlib.spr.Info() #type:ignore
            # 配置spr信息
            info.texid = txp_info.texture_id
            info.resolution_mode = kkdlib.spr.ResolutionMode.HD if aft_mode else kkdlib.spr.ResolutionMode.FHD#type:ignore
            info.px = txp_info.start_x
            info.py = txp_info.start_y
            info.width = txp_info.width
            info.height = txp_info.height
            #添加到spr
            spr_bin.add_spr(info, name)

        farc = kkdlib.farc.Farc() #type:ignore
        farc.add_file_data(f"{export_name}.bin", spr_bin.to_buf())
        farc.write(str(export_path.joinpath(f"{export_name}.farc")), False, False)

def create_sel_texture_0(bg_path:Path, jk_path:Path|None = None) -> Image.Image:
    img_data = Image.new("RGBA",(2048, 1024))
    if not jk_path:
        jk_path = bg_path

    jk_img = ImageOps.fit(Image.open(jk_path), (500,500))
    bg_img = ImageOps.fit(Image.open(bg_path), (1280,720))
    
    img_data.paste(bg_img)
    img_data.paste(jk_img, (1287,3 ,1787,503))
    
    return img_data.transpose(Transpose.FLIP_TOP_BOTTOM)

def create_sel_texture_1(logo_path:Path|None) -> Image.Image:
    img_data = Image.new("RGBA",(1024, 512))
    if logo_path:
        logo_img = ImageOps.pad(Image.open(logo_path).convert("RGBA"), (870,330))
        img_data.paste(logo_img)

    return img_data.transpose(Transpose.FLIP_TOP_BOTTOM)

def create_spr_sel_farc(pv_id:int, spr_path_dict:dict[str,Path], export_path:Path, compression:Compression = Compression.ATI2):
    farc = Farc(compression)
    
    texture_0 = create_sel_texture_0(spr_path_dict.pop("bg_path"), spr_path_dict.pop("jk_path"))
    texture_1 = create_sel_texture_1(spr_path_dict.pop("logo_path", None))
    
    bg_jk_index = farc.add_texture(texture_0)
    logo_index  = farc.add_texture(texture_1)
    
    farc.add_sprite(f"SONG_BG{pv_id:03d}", setting=(bg_jk_index, 2, 2, 1280, 720))
    farc.add_sprite(f"SONG_JK{pv_id:03d}", setting=(bg_jk_index, 1286, 2, 502, 502))
    farc.add_sprite(f"SONG_LOGO{pv_id:03d}", setting=(logo_index, 2, 2, 870, 330))
    
    farc.export_farc(f"spr_sel_pv{pv_id:03d}", export_path)
    
if __name__ == "__main__":
    image_info = {"bg_path":Path("background.jpg"),
                "jk_path":Path("preview.png")}

    create_spr_sel_farc(10086, image_info, Path("test"), Compression.BC7)