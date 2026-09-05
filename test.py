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
from ffmpeg_normalize import FFmpegNormalize
from spr_db.SprDb import create_spr_db

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
    folder_name: str = f"Song Pack_{datetime.now().strftime(r"%Y%m%d_%H%M%S")}"
    base_path: Path = Path("output", folder_name)

    for dir in [r"rom//2d", r"rom//movie", r"rom//script", r"rom//sound//song"]:
        base_path.joinpath(dir).mkdir(parents=True, exist_ok=True)
    with open(base_path.joinpath("config.toml"), encoding="utf-8", mode="w+")as f:
        f.write(
            'enabled = true\n'
            'include = ["."]\n'
            '\n'
            'name = "Template Song Pack"\n'
            'description = "Create with csfm_to_mm_tool"\n'
            'version = "1.0"\n'
            'date = "06.05.2026"\n'
            'author = "hiki8man"\n')
    return base_path

chart_info_dict:dict[int,ChartInfo] = {}

if __name__ == "__main__":
    init_logging()
    import os
    from lib.media_convert import ffprobe_helper, convert_ogg

    
    BASE_PATH = create_output_folder()
    '''
    os.environ['FFMPEG_PATH'] = str(Path().joinpath("ffmpeg", "ffmpeg.exe"))
    normalizer = FFmpegNormalize(
        target_level=-10,
        true_peak=-0.5,
        audio_codec='libvorbis',
        sample_rate=44100,
        extra_output_options=['-aq', '6'],
        video_disable=True,
    )
    '''    

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
        pv_db_list += chart_info.export_chart(BASE_PATH)
        
        src_song:Path = chart_info.meta_data["song_path"]
        if src_song is None or not src_song.exists():
            logging.warning(f"Song file not found for PV ID {chart_info.pv_id}")
            continue
        dst_song = BASE_PATH.joinpath("rom", "sound", "song", f"pv_{chart_info.pv_id:03d}.ogg")
        '''
        normalizer.add_media_file(str(src_song), str(dst_song))
        normalizer.run_normalization()
        '''
        if isinstance(src_song, Path) and src_song.exists():
            media_info = ffprobe_helper().get_media_info(src_song)
            if media_info["audio"] != None:
                convert_ogg().start(media_info["audio"], dst_song)

    
    pv_db_list.sort()
    with open(BASE_PATH.joinpath("rom", "mod_pv_db.txt"),"w",encoding="utf-8") as f:
        f.write("\n".join(pv_db_list))
    
    spr_path = BASE_PATH.joinpath("rom", "2d")
    create_spr_db(spr_path, spr_path.joinpath("mod_spr_db.bin"))
