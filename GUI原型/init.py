# ===初始化log===
from loguru import logger

# ===判断是否为开发模式（使用python运行）===
def check_develop() -> bool:
    from pathlib import Path
    from sys import executable

    is_develop = Path(executable).stem.lower() in {'python', 'python3', 'pythonw'}
    logger.info(f"开发者模式：{is_develop}")
    return is_develop

# ===正式执行===
logger.info("初始化导入库")

import dearpygui.dearpygui as dpg
import dpg_gui.creat_dpg as creat_dpg



logger.info("程序启动")

creat_dpg.start(title="Comfy Studio Export Tool",width=1280,height=800,light_mode=False)
creat_dpg.set_viewport_min(1280,800)

import sys_gui

logger.info("初始化界面布局")
with dpg.window(label="主视口", tag="main"):
    with dpg.menu_bar():
        with dpg.menu(label="文件"):
            dpg.add_menu_item(label="添加csfm文件")
            pass

        with dpg.menu(label="关于"):
            dpg.add_menu_item(label="版本 ver2.0.0dev5",enabled=False)

    with dpg.table(header_row=False, height=-32, policy=dpg.mvTable_SizingStretchProp,
                   borders_innerV=True, borders_outerH=True, borders_outerV=True):
        dpg.add_table_column(init_width_or_weight=0.25)
        dpg.add_table_column(init_width_or_weight=0.75)

        with dpg.table_row():
            sys_gui.left_menu()
        
            with dpg.tab_bar(tracked=True):
                with dpg.tab(label="歌曲信息",tag="song_info_tab"):
                    pass
                with dpg.tab(label="歌曲信息配置",tag="song_config_tab"):
                    pass
                with dpg.tab(label="谱面配置",tag="csfm_tab"):
                    pass


    dpg.add_progress_bar(default_value=0, tag="data_progress", width=-1, height=28, overlay="完成！")

# 设置快捷键
with dpg.handler_registry():
    dpg.add_key_press_handler(key=dpg.mvKey_Tab,callback=lambda: None)

if check_develop() == False: 
    # 数据提取没有做完，需要在实际使用环境屏蔽
    dpg.configure_item("data_filter_tab",show=False)

logger.success("初始化界面布局完成")

creat_dpg.end("main")
logger.success("程序退出")