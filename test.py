from lib.CsfmReader import read_csfm
from lib.ConvertDSC import DSCManager
from lib.CsfmDataClass import Difficulty, ChartInfo
from pathlib import Path
from collections.abc import Generator
import logging
import re
from dataclasses import dataclass, field, InitVar
import enum

def init_logging():
    logging.basicConfig(
        format='{asctime} {levelname} [{name}]: {message}',
        style='{',
        level=logging.INFO,
        # level=logging.DEBUG,
        handlers=[logging.StreamHandler()],
    )

def get_csfm_file() -> Generator[Path, None, None]:
    for csfm_path in Path("input").rglob("*/*.csfm"):
        if re.match(r"\d+$",csfm_path.parent.name):
            yield csfm_path

if __name__ == "__main__":
    for csfm_path in get_csfm_file():
        pv_id = int(csfm_path.parent.name)
        csfm_data = read_csfm(csfm_path)
        dsc_managet = DSCManager()
        dsc_managet.read_csfm_data(csfm_data)
        dsc_managet.creat_dsc_file(pv_id,Path("output"))
