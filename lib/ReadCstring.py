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

def ReadCstringDict(data: bytes, encode:str ,startoffset: int = 0) -> dict[int,str]:
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
        CstringDict[address] = bytestring.decode(encode)
        offset += len(bytestring) + 1

    return CstringDict

def ReadDictFromFile(file: BinaryIO, offset:int = 0, encode:str = "UTF-8"):
    file.seek(offset)
    CstringDict = ReadCstringDict(file.read(), encode)
    if offset != 0:
        return {key + offset: value for key, value in CstringDict.items()}
    else:
        return CstringDict

def ReadStrFromFile(file: BinaryIO, offset:int = 0, encode:str = "UTF-8") -> str:

    file.seek(offset)
    string = b""
    while True:
        string_char = file.read(1)
        if not string_char or string_char == b"\x00":
            break # 读取到末尾没有数据
        else:
            string += string_char

    return string.decode(encode)

