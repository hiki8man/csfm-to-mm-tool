import dearpygui.dearpygui as dpg
from dpg_gui.color import DpgLineThemeManager

line_theme_manager = DpgLineThemeManager()

def add_chart_axis(label:str, tag:str, axis:int=0) -> None:
    """
    label:str 坐标轴标题
    tag:str dpg内部用于区分不同组件使用的标识
    axis:int 与pandas一样0表示Y轴，1表示X轴
    """
    match axis:
        case 0 | 1:
            kwargs:dict[str,int|str] = {"axis":dpg.mvXAxis} if axis == 1 else {"axis":dpg.mvYAxis}
        case _:
            raise ValueError("axis只能为0或1")

    if label != "":
        kwargs["label"] = label
    
    if tag != "":
        # [NOTE] 也许有更好的检测方法？
        try:
            dpg.get_item_info(tag)
            raise KeyError("该tag已被使用")
        except Exception:
            kwargs["tag"] = tag

    dpg.add_plot_axis(**kwargs) #type:ignore

def creat_chart(width:int=-1, height:int=-1, title:str="", x_label:str="", y_label:str="", x_tag:str="", y_tag:str="", query:bool=True) -> None:

    plot_kwargs:dict[str,int|str] = {"width":width, "height":height}
    if title:
        plot_kwargs["label"] = title

    with dpg.plot(**plot_kwargs): #type:ignore
        dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast, show=True, outside=True)
        add_chart_axis(x_label, x_tag, axis=1)
        add_chart_axis(y_label, y_tag, axis=0)