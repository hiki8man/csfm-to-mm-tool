from lib.CsfmReader import read_csfm
from lib.ConvertDSC import DSCManager
from pathlib import Path
from PIL import Image
for csfm_path in Path("csfm_data").rglob("*.csfm"):
    pass

if __name__ == "__main__":
    '''
    file_path = Path("Untitled Chart6.csfm")
    csfm_data = read_csfm(file_path)
    dsc_managet = DSCManager()
    dsc_managet.read_csfm_data(csfm_data["Chart"])
    dsc_managet.creat_dsc_file(2222)
    '''
    print((417.0 - 1.0/3.0) * (1.0 - pow(0.995, min(400, 1000))))