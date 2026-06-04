import dearpygui.dearpygui as dpg

from loguru import logger

def left_menu() -> None:
    with dpg.group(tag="left_menu"):
        dpg.add_separator(label="导入CSFM")
        dpg.add_button(label="添加CSFM",width=-1)

        with dpg.table(header_row=False):
            dpg.add_table_column(init_width_or_weight=0.5)
            dpg.add_table_column(init_width_or_weight=0.5)
            with dpg.table_row():
                dpg.add_button(label="移除选中", width=-1)
                dpg.add_button(label="清除列表", width=-1)
        
        dpg.add_separator(label="歌曲列表")
        with dpg.table(header_row=False, height=-200):
            dpg.add_table_column()

        dpg.add_separator(label="导出MOD")
        with dpg.table(header_row=False,
                       borders_innerV=True, 
                       borders_outerH=True, 
                       borders_outerV=True):
                dpg.add_table_column(init_width_or_weight=0.5)
                dpg.add_table_column(init_width_or_weight=0.5)
                with dpg.table_row():
                    dpg.add_selectable(label="导出新MOD",span_columns=False)
                    dpg.add_selectable(label="添加到MOD",span_columns=False)
        dpg.add_spacer(height=4)
        dpg.add_input_text(width=-1)
        dpg.add_spacer(height=4)
        dpg.add_button(label="创建MOD", width=-1)