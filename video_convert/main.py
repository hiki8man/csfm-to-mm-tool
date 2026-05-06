from lib import media_convert
from pathlib import Path
import sys
import os
import argparse
import wannacri
import pythonjsonlogger

medio_info = media_convert.ffprobe_helper()
vp9_convert = media_convert.convert_vp9()
h264_convert = media_convert.convert_h264()
ogg_convert = media_convert.convert_ogg()
videocopy_convert = media_convert.convert_copy()
          
parser = argparse.ArgumentParser(description='MM+用USM打包工具')

parser.add_argument('-Ogg', dest="SoundOnly", action="store_true",help='只转换音频')
parser.add_argument('-H264', action="store_true", help='使用H264编码而不是VP9编码（不支持Linux系统与其他参数，仅限于测试使用）')
parser.add_argument('-Level', type=int, choices= [1,2,3], required=False, default=1, help='设置VP9转码码率：默认为1。1为3000k码率，2为5000k码率，3为8000k码率。通常使用 1 即可')
parser.add_argument('-Use2Pass', action="store_true",help='在VP9使用二次编码，速度会更慢')
parser.add_argument('-Use720P', action="store_true",help='将高于720P的视频强行缩放到720P便于使用更低的码率的同时减少马赛克数量')
parser.add_argument('-Unpack', action="store_true",help='将未加密的USM拆包')
parser.add_argument('File_Path', type=str, help='文件路径')
command_args = parser.parse_args()

def check_file_name(srt_name):
    try:
        srt_name.encode("shift-jis")
        return True
    except:
        return False

def createusm(file):
    output_path = Path("output").absolute()
    os.chdir(str(Path(".\\ffmpeg")))
    sys.argv=["wannacri","createusm",str(file),"--output",str(output_path)]
    wannacri.main()
    os.chdir(os.path.dirname(sys.executable))

def extractusm(file):
    output_path = Path("output").absolute().joinpath(f"usm_unpack")
    os.chdir(str(Path(".\\ffmpeg")))
    sys.argv=["wannacri","extractusm",str(file),"--output",str(output_path)]
    wannacri.main()
    os.chdir(os.path.dirname(sys.executable))
    
def convert_video(file_info):
    is_safe_file = medio_info.check_media_file(file_info["file_path"])
    video_path = ""
    codec_name = file_info['codec_name'].lower()
    
    if not is_safe_file:
        print("文件损坏，将会尝试强行重转码进行修复\n无法保证USM文件能够正常使用")
    print("处理视频：")
    height_check = file_info["width"] / 16 * 9
    if height_check == file_info['height']:
        if command_args.H264 == True and codec_name == "h264" and is_safe_file == True:
            video_path = videocopy_convert.start(file_info)
        elif codec_name == "vp90" or codec_name == "vp9" and is_safe_file == True:
            video_path = videocopy_convert.start(file_info)
        elif command_args.H264 == True:
            video_path = h264_convert.start(file_info)
        else:
            video_path = vp9_convert.start(file_info, command_args.Use2Pass, command_args.Level, command_args.Use720P)
    elif command_args.H264 == True:
        video_path = h264_convert.start(file_info)
    else:
        video_path = vp9_convert.start(file_info, command_args.Use2Pass, command_args.Level, command_args.Use720P)
    print(video_path)    
    createusm(video_path)
    Path.unlink(Path(video_path))
    
def convert_file(_File_Path):
    print("*"*50)
    print(f"开始处理{_File_Path.name}")
    if check_file_name(_File_Path.name):
        file_info = medio_info.get_media_info(_File_Path)
        if file_info["video"] != None and command_args.SoundOnly == False:
            convert_video(file_info["video"])
        if file_info["audio"] != None:
            print("处理音频：")
            ogg_convert.start(file_info["audio"])
        else:
            print(f"{_File_Path.name}没有音频！")
        print(f"{_File_Path.name}已完成！\n")
    else:
        print("WannaCRI不支持部分特殊符号，请重命名文件后再次重试！")

    
file_path = Path(command_args.File_Path)
if command_args.Unpack:
    extractusm(file_path.absolute())
    sys.exit()

if file_path.is_dir():
    if not Path("temp").exists():
        Path.mkdir(Path("temp"))  
    file_list = file_path.iterdir()
    for file in file_list:
        if file.is_file():
            convert_file(file)
else:
    convert_file(file_path)
