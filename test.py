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

chart_info_dict:dict[int,ChartInfo] = {}

if __name__ == "__main__":
    init_logging()
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
        dst_song = Path("output", "rom", "sound", "song", f"pv_{chart_info.pv_id:03d}{src_song.suffix}")
        shutil.copy2(src_song, dst_song)
        
        pv_db_list += chart_info.export_chart()
    
    pv_db_list.sort()
    with open("output//rom//mod_pv_db.txt","w",encoding="utf-8") as f:
        f.write("\n".join(pv_db_list))
    
    SPR_DB = db_tool.Manager()
    spr_path = Path("output\\rom\\2d")
    farc_list = []
    for spr in spr_path.iterdir():
        _temp_file = Path(spr)
        if _temp_file.suffix.upper() == ".FARC":
            farc_list.append(_temp_file)
    if len(farc_list) >0:
        for farc_file in farc_list:
            farc_reader = db_tool.read_farc(farc_file)
            db_tool.add_farc_to_Manager(farc_reader, SPR_DB)
            
    SPR_DB.write_db("output\\rom\\2d\\mod_spr_db.bin")
