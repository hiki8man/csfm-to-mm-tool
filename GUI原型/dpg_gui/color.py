import dearpygui.dearpygui as dpg

table = ["#000000","#ff0000","#00b050","#00b0f0",
         "#ffc000","#0070c0","#7030a0","#0000ff",
         "#c00000","#ff00ff","#00ff00","#800000",
         "#ffff00","#974706","#204d25","#00ff99"]

class DpgLineThemeManager:
    # 管理线条对应的样式，主要用来设置颜色
    # 也许不需要set，因为这里保存的是颜色的样式，我们其实只需要get方法
    # 添加一个新的方法为测试样本试试
    def __init__(self) -> None:
        self.line_theme:dict = {}
        self.first_run:bool = True

    def first_run_init(self) -> None:
        for hex_color in table:
            self.set(hex_color)
    
    def get_color_theme(self, hex_color:str) -> int|str:
        # 获取预先设定好的样式与对应颜色
        # 返回值应该是一个tag，后续验证
        dpg_color = self.hex_to_dpgcolor(hex_color)
        with dpg.theme() as color_theme:
            with dpg.theme_component(dpg.mvScatterSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, dpg_color, category=dpg.mvThemeCat_Plots)
                dpg.add_theme_color(dpg.mvPlotCol_MarkerOutline, dpg_color, category=dpg.mvThemeCat_Plots)
                dpg.add_theme_style(dpg.mvPlotStyleVar_Marker, dpg.mvPlotMarker_Circle, category=dpg.mvThemeCat_Plots)
                dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 3.0, category=dpg.mvThemeCat_Plots)

            with dpg.theme_component(dpg.mvLineSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, dpg_color, category=dpg.mvThemeCat_Plots)
                dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 2, category=dpg.mvThemeCat_Plots)
                dpg.add_theme_style(dpg.mvPlotStyleVar_Marker, dpg.mvPlotMarker_Circle, category=dpg.mvThemeCat_Plots)
                dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 3.0, category=dpg.mvThemeCat_Plots)
            


        return color_theme

    def get(self, hex_color:str):
        if self.first_run:
            self.first_run = False
            self.first_run_init()
            
        if hex_color in self.line_theme:
            return self.line_theme[hex_color]
        
        raise ValueError("未定义的颜色")

    def set(self, hex_color:str) -> None:
        with dpg.theme() as color_theme:
            with dpg.theme_component(dpg.mvLineSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, self.hex_to_dpgcolor(hex_color), category=dpg.mvThemeCat_Plots)
                dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 2.5, category=dpg.mvThemeCat_Plots)
                dpg.add_theme_style(dpg.mvPlotStyleVar_Marker, dpg.mvPlotMarker_Circle, category=dpg.mvThemeCat_Plots)
                dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 5.0, category=dpg.mvThemeCat_Plots)

        self.line_theme[hex_color] = color_theme

    def hex_to_dpgcolor(self, hex_color:str) -> tuple[int,int,int,int]:
        if len(hex_color) == 7 and hex_color[0] == "#": #RRGGBB模式
            return (int(hex_color[1:3], 16), 
                    int(hex_color[3:5], 16),
                    int(hex_color[5:7], 16),
                    255)
        else:
            raise ValueError(f"不支持的颜色代码形式：{hex_color}")

    def get_color_light(self, hex_color:str) -> float:
        if len(hex_color) == 7 and hex_color[0] == "#": #RRGGBB模式
            r = int(hex_color[1:3], 16) / 255
            g = int(hex_color[3:5], 16) / 255
            b = int(hex_color[5:7], 16) / 255
            # 伽马校正（sRGB到线性RGB）
            def gamma_correct(channel: float) -> float:
                if channel <= 0.03928:
                    return channel / 12.92
                else:
                    return ((channel + 0.055) / 1.055) ** 2.4
            
            r_linear = gamma_correct(r)
            g_linear = gamma_correct(g)
            b_linear = gamma_correct(b)
            return 0.2126 * r_linear + 0.7152 * g_linear + 0.0722 * b_linear
        else:
            raise ValueError(f"不支持的颜色代码形式：{hex_color}")