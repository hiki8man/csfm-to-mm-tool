from lib.CsfmReader import read_csfm
from lib.ConvertDSC import DSCManager
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

class Difficulty(enum.IntEnum):
    EASY    = enum.auto()
    NORMAL  = enum.auto()
    HARD    = enum.auto()
    EXTREME = enum.auto()
    ENCORE  = enum.auto()

    EX_EASY    = enum.auto()
    EX_NORMAL  = enum.auto()
    EX_HARD    = enum.auto()
    EX_EXTREME = enum.auto()
    EX_ENCORE  = enum.auto()

@dataclass
class ChartInfo:
    pv_id: int

    meta_data: dict = field(default_factory=dict)

    easy: dict = field(default_factory=dict)
    normal: dict = field(default_factory=dict)
    hard: dict = field(default_factory=dict)
    extreme: dict = field(default_factory=dict)
    ex_extreme: dict = field(default_factory=dict)

    def update_chart(self, info:dict) -> None:
        diff_type:int = info["Difficulty"]["Type"]
        if info["Difficulty"]["IsEx"]:
            diff_type += 5

        if diff_type == Difficulty.EASY:
            self.easy = info
        elif diff_type == Difficulty.NORMAL:
            self.normal = info
        elif diff_type == Difficulty.HARD:
            self.hard = info
        elif diff_type == Difficulty.EXTREME:
            self.extreme = info
        elif diff_type == Difficulty.EX_EXTREME:
            self.ex_extreme = info
        else:
            raise ValueError(f"未知的难度数: {diff_type}")
    def update_meta(self, info:dict) -> None:
        if info:
            self.meta_data = info
        else:
            ValueError("元数据错误")

if __name__ == "__main__":
    for csfm_path in get_csfm_file():
        pv_id = int(csfm_path.parent.name)
        csfm_data = read_csfm(csfm_path)

    file_path = Path("Untitled Chart6.csfm")
    csfm_data = read_csfm(file_path)
    dsc_managet = DSCManager()
    dsc_managet.read_csfm_data(csfm_data["Chart"])
    dsc_managet.creat_dsc_file(2222,Path("output"))