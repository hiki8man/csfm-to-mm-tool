from typing import BinaryIO
class PaddingDataError(Exception):
    def __init__(self, message) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message

def isPadding(data: bytes) -> bool:
    return data[0] == 0xcc

def isCorrupted(data: bytes) -> bool:
    return data.find(b"\x00") == -1
    
def CheckData(data: bytes) -> None:
    if isPadding(data):
        raise PaddingDataError("检测到填充数据")
    elif isCorrupted(data):
        raise ValueError("字符串数据不完整")

def ReadCstring(data: bytes) -> bytes:
    CheckData(data)
    return data.split(b"\x00",1)[0]

def ReadCstringDict(data: bytes, startoffset: int = 0) -> dict[int,str]:
    CstringDict = {}
    data = data[startoffset:]
    offset = 0
    lenght = len(data)
    while offset < lenght:
        try:
            bytestring = ReadCstring(data[offset:])
        except PaddingDataError:
            #读取到填充直接跳出
            break
        address = startoffset + offset
        CstringDict[address] = bytestring.decode("UTF-8")
        offset += len(bytestring) + 1

    return CstringDict

def ReadCstringFile(file: BinaryIO, offset: int = 0):
    file.seek(offset)
    CstringDict = ReadCstringDict(file.read())
    if offset != 0:
        return {key + offset: value for key, value in CstringDict.items()}
    else:
        return CstringDict