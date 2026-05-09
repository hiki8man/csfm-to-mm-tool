from .FarcCreater import Farc, Compression, SprInfo
from pathlib import Path
from PIL import Image, ImageFile, ImageOps
from PIL.Image import Transpose

def fit_image(img:Image.Image, width:int, height:int, alpha_edge:bool=False) -> Image.Image:
    img = ImageOps.fit(img, (width, height),Image.Resampling.LANCZOS)
    # 需要扩展两像素出血
    import numpy as np
    img_array = np.array(img)
    expand_data = np.pad(img_array, pad_width=((2,2),(2,2),(0,0)), mode='edge')
    if alpha_edge:
        # 将最边缘的像素也设置为透明
        alpha_img = Image.fromarray(expand_data)
        alpha_img.putalpha(0) # 设置alpha值为0（完全透明，但其仍然保留有边缘RGB信息）
        img = img.crop((1, 1, img.size[0]-1, img.size[0]-1))
        alpha_img.paste(img, (3, 3))
        
        return alpha_img
    else:
        # 需要扩展两像素出血
        
        return Image.fromarray(expand_data)

def create_sel_texture_0(bg_path:Path, jk_path:Path|None = None) -> Image.Image:
    import numpy as np
    img_data = Image.new("RGBA",(2048, 1024))
    if not jk_path:
        jk_path = bg_path

    bg_img = fit_image(Image.open(bg_path), 1280,720)
    jk_img = fit_image(Image.open(jk_path), 502,502, True)
    # jk_img = fit_image(Image.open(jk_path), 500,500)
    
    img_data.paste(bg_img, (0, 0))
    img_data.paste(jk_img, (1284,0))
    # img_data.paste(jk_img, (1284,0))
    
    return img_data.transpose(Transpose.FLIP_TOP_BOTTOM)

def create_sel_texture_1(logo_path:Path|None) -> Image.Image:
    img_data = Image.new("RGBA",(1024, 512))
    if logo_path:
        logo_img = ImageOps.pad(Image.open(logo_path).convert("RGBA"), (870,330))
        img_data.paste(logo_img)

    return img_data.transpose(Transpose.FLIP_TOP_BOTTOM)

def create_spr_sel_farc(pv_id:int, spr_path_dict:dict[str,Path], export_path:Path, compression:Compression = Compression.ATI2):
    farc = Farc()
    
    texture_0 = create_sel_texture_0(spr_path_dict.pop("bg_path"), spr_path_dict.pop("jk_path"))
    texture_1 = create_sel_texture_1(spr_path_dict.pop("logo_path", None))
    
    bg_jk_index = farc.add_texture(texture_0, compression)
    logo_index  = farc.add_texture(texture_1, compression)
    
    farc.add_sprite(SprInfo(f"SONG_BG{pv_id:03d}", bg_jk_index, 2, 2, 1280, 720))
    farc.add_sprite(SprInfo(f"SONG_JK{pv_id:03d}", bg_jk_index, 1286, 2, 502, 502))
    farc.add_sprite(SprInfo(f"SONG_LOGO{pv_id:03d}", logo_index, 2, 2, 870, 330))
    
    farc.export_farc(f"spr_sel_pv{pv_id:03d}", export_path)
    
if __name__ == "__main__":
    image_info = {"bg_path":Path("SONG_BG_DUMMY.png"),
                  "jk_path":Path("SONG_JK_DUMMY.png")}

    create_spr_sel_farc(10086, image_info, Path("test"), Compression.RGBA)

    image_info = {"bg_path":Path("SONG_BG_DUMMY.png"),
                  "jk_path":Path("SONG_JK_DUMMY.png")}

    create_spr_sel_farc(10087, image_info, Path("test"), Compression.BC7)