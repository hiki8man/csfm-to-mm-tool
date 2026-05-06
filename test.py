from lib.CsfmReader import read_csfm
from lib.ConvertDSC import DSCManager
from lib.CsfmDataClass import Difficulty, ChartInfo
import FarcCreater
from pathlib import Path
from collections.abc import Generator
import logging
import re
from dataclasses import dataclass, field, InitVar
import enum
import shutil
import auto_creat_mod_spr_db as db_tool
from ffmpeg_normalize import FFmpegNormalize

def init_logging():
    logging.basicConfig(
        format='{asctime} {levelname} [{name}]: {message}',
        style='{',
        # level=logging.INFO,
        level=logging.INFO,
        handlers=[logging.StreamHandler()],
    )

def get_csfm_file() -> Generator[Path, None, None]:
    for csfm_path in Path("input").rglob("*/*.csfm"):
        if re.match(r"\d+$",csfm_path.parent.name):
            yield csfm_path

def create_output_folder() -> Path:
    from datetime import datetime
    folder_name: str = datetime.now().strftime(r"%Y%m%d_%H%M%S")
    base_path: Path = Path("output", folder_name)

    for dir in [r"rom//2d", r"rom//movie", r"rom//script", r"rom//sound//song"]:
        base_path.joinpath(dir).mkdir(parents=True, exist_ok=True)

    return base_path

chart_info_dict:dict[int,ChartInfo] = {}

if __name__ == "__main__":
    init_logging()
    import os

    os.environ['FFMPEG_PATH'] = str(Path().joinpath("ffmpeg", "ffmpeg.exe"))
    BASE_PATH = create_output_folder()

    normalizer = FFmpegNormalize(
        target_level=-14,
        loudness_range_target=11,
        true_peak=-0.5,
        audio_codec='libvorbis',
        sample_rate=44100,
        extra_output_options=['-aq', '6'],
        video_disable=True,
    )    

    for csfm_path in get_csfm_file():
        pv_id = int(csfm_path.parent.name)
        csfm_data = read_csfm(csfm_path)
        if not pv_id in chart_info_dict:
            chart_info_dict.update({pv_id:ChartInfo(pv_id)})
        
        if not chart_info_dict[pv_id].meta_data:
            chart_info_dict[pv_id].update_meta(csfm_data)

        chart_info_dict[pv_id].update_chart(csfm_data)

    pv_db_list = []

    for chart_info in chart_info_dict.values():
        src_song:Path = chart_info.meta_data["song_path"]
        dst_song = BASE_PATH.joinpath("rom", "sound", "song", f"pv_{chart_info.pv_id:03d}.ogg")
        normalizer.add_media_file(str(src_song), str(dst_song))
        normalizer.run_normalization()
        
        pv_db_list += chart_info.export_chart()
    
    pv_db_list.sort()
    with open(BASE_PATH.joinpath("rom", "mod_pv_db.txt"),"w",encoding="utf-8") as f:
        f.write("\n".join(pv_db_list))
    
    SPR_DB = db_tool.Manager()
    spr_path = BASE_PATH.joinpath("rom", "2d")
    farc_list = []
    for spr in spr_path.iterdir():
        _temp_file = Path(spr)
        if _temp_file.suffix.upper() == ".FARC":
            farc_list.append(_temp_file)
    if len(farc_list) >0:
        for farc_file in farc_list:
            farc_reader = db_tool.read_farc(farc_file)
            db_tool.add_farc_to_Manager(farc_reader, SPR_DB)
            
    SPR_DB.write_db(spr_path.joinpath("mod_spr_db.bin"))
