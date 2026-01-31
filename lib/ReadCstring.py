from typing import BinaryIO
import logging

logger = logging.getLogger("ReadCstring")

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
    logger.debug("检测数据完整性")

    if isPadding(data):
        logger.debug("数据字符串为填充数据")
        raise PaddingDataError("检测到填充数据")
    
    elif isCorrupted(data):
        logger.debug("数据字符串不完整")
        raise ValueError("字符串数据不完整")
    
    logger.debug("数据完整性检测完成")

def ReadCstring(data: bytes) -> bytes:
    logger.debug("读取Cstring")

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
            logger.debug(f"读取到的值 {bytestring}")

        except PaddingDataError:
            logger.debug("读取到填充数据，不再读取后续内容")
            #读取到填充直接跳出
            break
        
        address = startoffset + offset
        logger.debug(f"{address}地址对应的字符串{bytestring}")
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

def ReadCstringFile2(file: BinaryIO, offset:int) -> str:

    file.seek(offset)
    string = b""
    while True:
        string_char = file.read(1)
        if not string_char or string_char == b"\x00":
            break # 读取到末尾没有数据
        else:
            string += string_char

    return string.decode()
        