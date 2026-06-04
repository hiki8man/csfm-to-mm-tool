import dearpygui.dearpygui as dpg
from loguru import logger
import sys,ctypes
import psutil
import time
import random

BEFORE_TIME: float = 0.0
FPS_TIME: float = 0.03
POWER_SAVE_MODE: bool = False

logger.remove()
logger.add(sink="logs\\log_{time}.log", level="DEBUG")
logger.add(sys.stderr, level="INFO")

def get_dpi() -> float|int:
    logger.debug("获取DPI值")
    if sys.platform == 'win32':
        logger.debug("运行环境为win平台，计算DPI")
        user32 = ctypes.windll.user32
        hdc = user32.GetDC(0)
        dpi_x = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
        user32.ReleaseDC(0, hdc)
        dpi_value = int((dpi_x / 96) * 100)
        logger.debug(f"系统DPI：{dpi_value}")
        return dpi_value
    else:
        logger.debug("非win平台没有实现DPI缩放，返回默认值100")
        return 100

def is_locked() -> bool:
    if sys.platform != 'win32':
        return False
    
    user32 = ctypes.windll.user32
    hDesktop = user32.OpenInputDesktop(0, False, 0x0100)

    if not hDesktop:
        return True

    result = user32.SwitchDesktop(hDesktop)
    user32.CloseDesktop(hDesktop)

    screensaver = bool(user32.SystemParametersInfoW(114, 0, None, 0))

    return not result or screensaver

def is_on_screensaver() -> bool:
    if sys.platform != 'win32':
        return False

    for process in psutil.process_iter():
        try:
            if process.name().lower().endswith(".scr"):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return False

logger.debug("禁用DPI缩放（DearPyGUI原生不支持DPI缩放）")
if sys.platform == 'win32':
    ctypes.windll.shcore.SetProcessDpiAwareness(1)

# ===在这里设置全局异常钩子===
def enhanced_global_exception_hook(exctype, value, traceback_obj):
    """增强版全局异常钩子"""
    import traceback
    from pathlib import Path
    import os
    
    # 提取基本信息
    frames = traceback.extract_tb(traceback_obj)
    if frames:
        last_frame = frames[-1]
        
        # 构建错误位置信息
        location_info = {
            "file": last_frame.filename,
            "line": last_frame.lineno,
            "function": last_frame.name,
            "code": last_frame.line,
            "error_type": exctype.__name__,
            "error_msg": str(value)
        }
        
        # 记录到loguru（包含完整堆栈）
        error_str = (f"未捕获异常\n"
            f"异常信息:\n{location_info['error_type']}: {location_info['error_msg']}\n"
            f"异常位置:\n{location_info['file']}:{location_info['line']}")
        
        logger.opt(exception=(exctype, value, traceback_obj)).error(error_str)
        
    else:
        error_str = (f"未捕获的全局异常:\n {exctype.__name__}: {value}")
        logger.exception(error_str)

    viewport_width = dpg.get_viewport_width()
    viewport_height = dpg.get_viewport_height()
    with dpg.window(pos=[viewport_width//2-250,viewport_height//2 - 180],
                    width = 500, height = 360, modal=True, no_resize=True):

        dpg.add_text("发生异常，请将最新的log文件发送给开发者")
        dpg.add_button(label="打开log文件夹",callback=lambda:os.startfile(Path('logs')))

        dpg.add_separator()
        dpg.add_input_text(default_value=error_str,width=-1, multiline=True, 
                           no_undo_redo=True, readonly=True)

# 设置全局异常钩子
sys.excepthook = enhanced_global_exception_hook

def _setup_chinese_font(font_file:str="font\\font.ttf",font_size:int=18) -> None:
    def char_hex(char:str) -> int:
        return ord(char)

    logger.debug("配置GUI字体")
    from pathlib import Path
    if Path(font_file).exists():
        with dpg.font_registry():
            logger.debug(f"字体：{font_file}，字体大小：{font_size}")

            dpi_value = get_dpi()
            font_size = round(font_size * (dpi_value / 100))
            
            font = dpg.add_font(font_file, font_size)
        
        logger.debug("绑定字体到GUI")
        dpg.bind_font(font)

def start(title:str="Dear PyGui", width:int=1280, height:int=800, light_mode:bool=False) -> None:
    logger.debug(f"GUI设置：标题 {title}，窗口 {width}x{height}，使用夜间模式 {light_mode}")
    dpg.create_context()
    title = str(title.encode("utf-8")) if sys.platform == "win32" else title
    dpg.create_viewport(title=title, width=int(width), height=int(height))
    _setup_chinese_font()

    if light_mode:
        import dpg_gui.themes as themes
        logger.debug("不使用夜间模式")
        light_theme = themes.create_theme_imgui_light()
        dpg.bind_theme(light_theme)

def end(window_tag:str="") -> None:

    global BEFORE_TIME
    logger.info("显示GUI视口")

    dpg.setup_dearpygui()
    
    if window_tag:
        logger.debug(f"为主视口添加tag {window_tag}")
        dpg.set_primary_window(window_tag, True)

    dpg.show_viewport()
    logger.success("初始化GUI完成，显示窗口")
    # 设置标题，渲染一帧生成窗口然后修改标题
    import ast
    from ctypes import windll
    
    dpg.render_dearpygui_frame()
    windll.user32.SetWindowTextW(
        windll.user32.FindWindowW(None, dpg.get_viewport_title()),
        ast.literal_eval(dpg.get_viewport_title()).decode("utf-8")
    )

    #dpg.start_dearpygui()
    # 减轻内存泄漏，在锁屏的时候降低运行速度同时禁止渲染

    run_reader: bool = True
    while dpg.is_dearpygui_running():
        
        if is_locked():
            if run_reader:
                run_reader = False
                logger.debug("进入锁屏，跳过渲染")
            continue
        elif is_on_screensaver():
            if run_reader:
                run_reader = False
                logger.debug("进入屏保，跳过渲染")
            continue
        else:
            if run_reader == False:
                run_reader = True
                logger.debug("返回桌面，恢复渲染")
        '''
        省电模式，目前看来其会影响CPU占用，因此不再需要
        if dpg.get_value("power_save_check"):
            if time.time() - BEFORE_TIME > FPS_TIME:
                BEFORE_TIME = time.time()
            else:
                continue
        '''
        if run_reader:
            dpg.render_dearpygui_frame()

    logger.debug("窗口被关闭，摧毁GUI上下文管理器")
    dpg.destroy_context()

def set_viewport_min(width:int=-1, height:int=-1) -> None:
    logger.debug("配置视口最小尺寸")
    if width > 0:
        logger.debug(f"最小宽度：{width}")
        dpg.set_viewport_min_width(width)
    if height > 0:
        logger.debug(f"最小高度：{height}")
        dpg.set_viewport_min_height(height)

def set_viewport_max(width:int=-1, height:int=-1) -> None:
    logger.debug("配置视口最大尺寸")
    if width > 0:
        logger.debug(f"最大宽度：{width}")
        dpg.set_viewport_max_width(width)
    if height > 0:
        logger.debug(f"最大高度：{height}")
        dpg.set_viewport_max_height(height)