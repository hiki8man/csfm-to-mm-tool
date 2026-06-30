from subprocess import PIPE, STDOUT
from subprocess import run as command_run,Popen as command_popen
from pprint import pprint
from pathlib import Path
import json
import wannacri
import pythonjsonlogger
from multiprocessing import cpu_count

#通过检测有无错误信息判断GPU编码器是否可用
class h264_encode_helper:
    nvenc = False
    amf   = False
    qsv   = False
    
    def __init__(self):
        ffmpeg_path = Path.joinpath(Path.cwd(),"ffmpeg","ffmpeg.exe")
        h264_encode_list = ["h264_qsv", "h264_nvenc", "h264_amf"]
        for h264_encode_name in h264_encode_list:
            ffmpeg_program  = command_run([ffmpeg_path, "-loglevel", "error",
                                            "-f", "lavfi",
                                            "-i", "color=black:s=1080x1080", "-vframes", "1",
                                            "-an", "-c:v", h264_encode_name,
                                            "-f", "null", "-"]
                                            ,stdout=PIPE,stderr=STDOUT,encoding="UTF-8")
            if len(ffmpeg_program.stdout) == 0:
                self.__set_can_use(h264_encode_name)
                
    def __set_can_use(self, _name):
        if _name == "h264_nvenc":
            self.nvenc = True
        elif _name == "h264_amf":
            self.amf = True
        elif _name == "h264_qsv":
            self.qsv - True          

#通过检测有无错误信息判断GPU编码器是否可用
class vp9_encode_helper:
    vaapi = False
    qsv   = False
    
    def __init__(self):
        ffmpeg_path = Path.joinpath(Path.cwd(),"ffmpeg","ffmpeg.exe")
        vp9_encode_list = ["vp9_vaapi", "vp9_qsv"]
        for vp9_encode_name in vp9_encode_list:
            ffmpeg_program  = command_run([ffmpeg_path, "-loglevel", "error",
                                            "-f", "lavfi",
                                            "-i", "color=black:s=1080x1080", "-vframes", "1",
                                            "-an", "-c:v", vp9_encode_name,
                                            "-f", "null", "-"]
                                            ,stdout=PIPE,stderr=STDOUT,encoding="UTF-8")
            if len(ffmpeg_program.stdout) == 0:
                self.__set_can_use(vp9_encode_name)
                
    def __set_can_use(self, _name):
        if _name == "vp9_vaapi":
            self.vaapi = True
        elif _name == "vp9_qsv":
            self.qsv = True    

class ffprobe_helper():
    
    ffprobe_path = str(Path.joinpath(Path.cwd(),"ffmpeg","ffprobe.exe"))
    
    def get_media_info(self, media_file):
        command = [self.ffprobe_path,"-loglevel","quiet",media_file,"-show_streams","-of","json"]
        json_info_file = command_popen(command, shell=True, stdout=PIPE,encoding="utf-8")
        with json_info_file.stdout as i:
            json_info = json.load(i)
        info = {"video":None,"audio":None}
        for media_info in json_info["streams"]:
            if media_info["codec_type"] == "video" and info["video"] == None:
                info["video"] = {"file_name":media_file.stem,
                                "file_path":media_file,
                                "codec_name":media_info["codec_name"],
                                "width":media_info["width"],
                                "height":media_info["height"]
                                }
            if media_info["codec_type"] == "audio" and info["audio"] == None:
                try:
                    song_bit = int(media_info["bit_rate"])
                except:
                    if media_info["codec_name"].upper() == "FLAC":
                        song_bit = 320000 / media_info["channels"] * 2
                    else:
                        song_bit = 192000 / media_info["channels"] * 2
                info["audio"] = {"file_name":media_file.stem,
                                "file_path":media_file,
                                "song_bit":song_bit,
                                "channels":media_info["channels"]
                                }
        return info
        
    def check_media_file(self, media_file):
        err_info  = command_run([self.ffprobe_path,"-loglevel", "warning",media_file],
                                 shell=True, stderr=PIPE, encoding="utf-8")
        err_str = err_info.stderr
        if len(err_str) > 0:
            return False
        else:
            return True  
 
class ffmpeg_helper:
    def __init__(self):
        ffmpeg_path = Path.joinpath(Path.cwd(),"ffmpeg","ffmpeg.exe")
        self.command_head = [ffmpeg_path,"-hide_banner","-loglevel", "info", "-hwaccel", "auto"]
        self.command_input = []
        self.command_convert_video = []
        self.command_convert_audio = []
        self.command_output  = []
        self.LogList = []
    
    def input_file(self, file_path):
        self.command_input.clear()
        self.command_input.append("-i")
        self.command_input.append(file_path)
        
    def output_file(self, file_path):
        if file_path == None:
            self.command_output = ["-f", "null", "-"]
        else:
            self.command_output.clear()
            self.command_output.append("-y")
            self.command_output.append(file_path)
        
    def RunFFMpeg(self):
        self.LogList.clear()
        if len(self.command_input) == 0 or len(self.command_output) == 0:
            print("没有指定文件")
            return
        command_convert = self.command_convert_audio + self.command_convert_video
        ffmpeg_command  = self.command_head + self.command_input + command_convert + self.command_output
        ffmpeg_program  = command_popen(ffmpeg_command,stdout=PIPE,stderr=STDOUT,encoding="UTF-8",errors="backslashreplace")
        file_time = None
        log_error_str = ""
        for log_text in ffmpeg_program.stdout:
            log_error_str += self.__get_error_info(log_text)
            self.LogList.append(log_text)
            if file_time == None:
                file_time = self.__get_file_time(log_text)
            else:
                self.__get_convert_process(log_text, file_time)
        print(f"\r[{'='*50}]{1:.2%}",end="")
        print(log_error_str)

                
    def __get_file_time(self, text):
        if text.find("Duration:") != -1:
            file_time_start = text.find("Duration: ") + 10
            file_time_end = text[file_time_start:].find(",") + file_time_start
            return self.__time_convert(text[file_time_start:file_time_end])
      
    def __get_convert_process(self, text, time_all):
        if text.find("speed=") !=-1 and text.find("time=-") == -1:
            convert_time_str_start = text.find("time") + 5
            convert_time_str_end = text.find(" bitrate=")
            time_now = self.__time_convert(text[convert_time_str_start:convert_time_str_end])
            if time_all != 0:
                convert_process = (time_now / time_all) if (time_now <= time_all) else 1
                print(f"\r[{'='*int(convert_process * 50)}{'*'*(50 - int(convert_process * 50))}]{convert_process:.2%}",end="")
            else:
                print(f"\r无法获取转换进度！已转换视频时长秒数：{text[convert_time_str_start:convert_time_str_end]}",end="")
                
    def __get_error_info(self, text):
        text_Upper = text.upper()
        if text_Upper.find("ERROR") != -1:
            return text
        else:
            return ""
        
    def __time_convert(self,time):
        try:
            time_h = float(time[0:2])
            time_m = float(time[3:5])
            time_s = float(time[6:11])
            time_convert_s = (time_h * 60 * 60) + (time_m * 60) + time_s
        except:
            time_convert_s = 0
        return time_convert_s
    
class convert_ogg(ffmpeg_helper):
    def __init__(self):
        super().__init__()
        self.command_convert_video = ["-vn"]

    def start(self,file_info):
        #OGG格式使用可变码率参数，同时由于声道问题无法确认具体上限值
        #需要将其处理为 AQ 参数
        self.song_aq = self.__get_aq(file_info)
        self.input_file(file_info["file_path"])
        self.file_name = file_info["file_name"] + ".ogg"
        self.__pass_1()
        self.__pass_2()
        
    def __pass_1(self):
        print("分析文件：")
        self.command_convert_audio = ["-af","loudnorm=I=-14:TP=-0.5:LRA=11:print_format=json"]
        self.output_file(None)
        self.RunFFMpeg()
    
    def __pass_2(self):
        print("开始转换：")
        self.command_convert_audio.clear()
        self.command_convert_audio = ["-c:a", "libvorbis"]
        self.__SetPass2Value()
        self.command_convert_audio += ["-aq",self.song_aq,
                                       "-ar","44100"]
        self.output_file(Path("output").joinpath(self.file_name))
        self.RunFFMpeg()
    
    def __get_aq(self,file_info):
        #参考资料：https://en.wikipedia.org/wiki/Vorbis#Technical_details
        #根据标准，AQ值以64000为低值，16000为间距差设置不同的值
        #下面的aq计算公式则是利用了这一点将AQ值转换为一个数值
        song_bit = file_info["song_bit"] / file_info["channels"] * 2
        aq = int((song_bit - 64000) / 16000)
        if aq >= 9:
            return "9"
        if aq <= -1:
            return "-1"
        else:
            return str(aq)

    def __SetPass2Value(self):
        Pass2Value = "loudnorm=I=-14:TP=-1.5:LRA=11"
        for message in self.LogList:
            if message.find("input_i") != -1:
                value = self.__get_value(message)
                Pass2Value += f":measured_I={value}"
            elif message.find("input_tp") != -1:
                value = self.__get_value(message)
                Pass2Value += f":measured_TP={value}"
            elif message.find("input_lra") != -1:
                value = self.__get_value(message)
                Pass2Value += f":measured_LRA={value}"
            elif message.find("input_thresh") != -1:
                value = self.__get_value(message)
                Pass2Value += f":measured_thresh={value}"
            elif message.find("target_offset") != -1:
                value = self.__get_value(message)
                Pass2Value += f":offset={value}"
        self.command_convert_audio += ["-af", Pass2Value]
        
    def __get_value(self,text):
        str_start = text.find(":")
        num_start = text[str_start:].find('"') + str_start + 1
        num_end   = text[num_start + 1:].find('"') + num_start + 1
        return text[num_start:num_end]

class convert_vp9(ffmpeg_helper):

    def __init__(self):
        super().__init__()
        self.command_convert_audio = ["-an"]
        vp9_encode_helper()
        self.codec_name = self.__UseCodec()
        self.suffix_name = ".ivf"

    def start(self, file_info, Use2Pass = False, level = 0, Use720P = False):
        self.input_file(file_info["file_path"])
        self.file_name = file_info["file_name"] + self.suffix_name
        self.command_convert_video = ["-c:v", self.codec_name]
        self.__fix_width(file_info, Use720P)
        if level == 0:
            #Google文档官方设定的1080P视频码率
            self.command_convert_video += ["-b:v", "3000k", 
                                           "-crf", "24",
                                           "-minrate", "1500k", "-maxrate", "4350k",
                                           "-pix_fmt", "yuv420p", 
                                           "-tile-columns", "2", "-row-mt", "1",
                                           "-threads", str(cpu_count())]
        if level == 1:
            #曾经使用于WannaCri_QT的参数
            self.command_convert_video += ["-b:v", "5000k", 
                                           "-crf", "16",
                                           "-minrate", "2500k", "-maxrate", "7250k",
                                           "-pix_fmt", "yuv420p", 
                                           "-tile-columns", "2", "-row-mt", "1",
                                           "-threads", str(cpu_count())]
        if level == 2:
            #拿Ghost Rule做测试用的参数
            self.command_convert_video += ["-b:v", "8000k", 
                                           "-crf", "12",
                                           "-minrate", "4000k", "-maxrate", "11600k",
                                           "-pix_fmt", "yuv420p", 
                                           "-tile-columns", "2", "-row-mt", "1",
                                           "-threads", str(cpu_count())]
        if Use2Pass == False:
            return self.__start_1pass()
        else:
            return self.__start_2pass()
        
    def __start_1pass(self):
        output_path = Path("output").joinpath(self.file_name)
        self.output_file(output_path)
        self.RunFFMpeg()
        return output_path.absolute()
        
    def __start_2pass(self):
        output_path = Path("output").joinpath(self.file_name)
        temp_command_convert_video = self.command_convert_video
        print("PASS1:")
        self.command_convert_video = temp_command_convert_video + ["-pass", "1"]
        self.output_file(None)
        self.RunFFMpeg()
        print("PASS2:")
        self.command_convert_video = temp_command_convert_video + ["-pass", "2"]
        self.output_file(output_path)
        self.RunFFMpeg()
        return output_path.absolute()
    
    def __fix_width(self, file_info, Use720P):
        video_width = file_info["width"]
        video_height = file_info["height"]
        Use720P_Command = ""
        if video_width <= 1280 or video_height <= 720:
            Use720P = False
        if Use720P == True:
            Use720P_Command = ",scale=1280x720"
        if (video_height / 9 * 16) > video_width:
            self.command_convert_video.append("-vf")
            self.command_convert_video.append(f"pad=width={(video_height / 9 * 16)}:height={video_height}:x=-1:y=-1:color=black{Use720P_Command}")
        elif (video_height / 9 * 16) < video_width:
            self.command_convert_video.append("-vf")
            self.command_convert_video.append(f"pad=width={video_width}:height={(video_width / 16 * 9)}:x=-1:y=-1:color=black{Use720P_Command}")
    
    def __UseCodec(self):
        if vp9_encode_helper.vaapi == True:
            return "vp9_vaapi"
        elif vp9_encode_helper.qsv == True:
            return "vp9_qsv"
        else:
            return "libvpx-vp9"

class convert_copy(ffmpeg_helper):
    def __init__(self):
        super().__init__()
        self.command_convert_audio = ["-an"]
    
    def start(self,file_info):
        self.input_file(file_info["file_path"])
        print()
        if file_info["codec_name"].upper() == "VP9" or file_info["codec_name"].upper() == "VP90":
            self.file_name = file_info["file_name"] + ".ivf"
        elif file_info["codec_name"].upper() == "H264":
            self.file_name = file_info["file_name"] + ".h264"
        else:
            raise ValueError("不支持此编码使用Copy编码")
        self.command_convert_video = ["-c:v", "copy"]
        output_path = Path("output").joinpath(self.file_name)
        self.output_file(output_path)
        self.RunFFMpeg()
        return output_path.absolute()
        
class convert_h264(ffmpeg_helper):
    def __init__(self):
        super().__init__()
        self.command_convert_audio = ["-an"]
        h264_encode_helper()
        self.codec_name = self.__UseCodec()
        self.suffix_name = ".h264"

    def start(self, file_info):
        self.input_file(file_info["file_path"])
        self.file_name = file_info["file_name"] + self.suffix_name
        self.command_convert_video = ["-c:v", self.codec_name]
        self.__fix_width(file_info)
        self.command_convert_video += ["-crf", "16"]
        output_path = Path("output").joinpath(self.file_name)
        self.output_file(output_path)
        self.RunFFMpeg()
        return output_path.absolute()
    
    def __fix_width(self, file_info):
        video_width = file_info["width"]
        video_height = file_info["height"]
        if (video_height / 9 * 16) > video_width:
            self.command_convert_video.append("-vf")
            self.command_convert_video.append(f"pad=width={(video_height / 9 * 16)}:height={video_height}:x=-1:y=-1:color=black")
        elif (video_height / 9 * 16) < video_width:
            self.command_convert_video.append("-vf")
            self.command_convert_video.append(f"pad=width={video_width}:height={(video_width / 16 * 9)}:x=-1:y=-1:color=black")
    
    def __UseCodec(self):
        if h264_encode_helper.nvenc == True:
            return "h264_nvenc"
        elif h264_encode_helper.qsv == True:
            return "h264_qsv"
        elif h264_encode_helper.amf == True:
            return "h264_amf"
        else:
            return "libx264"

'''     
test2 = ffprobe_helper()
info = test2.get_media_info(Path("OP_1080.wmv"))
test = convert_vp9()
test.start(info["video"],Use2Pass=True)
test3 = convert_ogg()
test3.start(info["audio"])
'''
