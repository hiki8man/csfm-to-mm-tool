import dearpygui.dearpygui as dpg
import dpg_gui.creat_dpg as creat_dpg
from loguru import logger
# 让AI添加了Tag系统并做了一些完善

# 全局 tag 计数器（用于自动生成唯一整数 tag）
_next_auto_tag = 10000

def _generate_auto_tag() -> int:
    global _next_auto_tag
    tag = _next_auto_tag
    _next_auto_tag += 1
    return tag

def is_ctrl_down():
    return dpg.is_key_down(dpg.mvKey_LControl) or dpg.is_key_down(dpg.mvKey_RControl)

def is_shift_down():
    return dpg.is_key_down(dpg.mvKey_LShift) or dpg.is_key_down(dpg.mvKey_RShift)

class MultiSelectBox:
    def __init__(self, tag: int | str | None = None) -> None:
        # 分配 tag：用户指定 or 自动生成
        if tag is None:
            self.tag = _generate_auto_tag()
        else:
            if dpg.does_item_exist(tag):
                raise ValueError(f"Tag '{tag}' already exists in Dear PyGui.")
            self.tag = tag

        # 把当前实例绑定到 DPG item 的 user_data（可选，方便反向查找）
        # 注意：此时 window 还没创建，稍后在 creat_child_window 中设置

        self.window_tag: int | str = -1
        self.items_list: list[int | str] = []
        self.selected_items_set: set[int | str] = set()
        self.shift_select: int | str = 0

    def clear_item(self) -> None:
        logger.debug(f"{self.tag}: 清空选择项")
        if self.items_list and len(self.items_list) > 0:
            for item_tag in self.items_list:
                if dpg.does_item_exist(item_tag):
                    dpg.delete_item(item_tag)
            self.items_list = []
            self.selected_items_set = set()
            self.shift_select = 0
            logger.debug(f"{self.tag}: 清空选择项完成")
        else:
            logger.debug(f"{self.tag}: 没有选择项无需清空")

    def creat_child_window(self, width: int = 0, height: int = 0) -> None:
        # 创建 child window，并使用 self.tag 作为其 tag（关键！）
        self.window_tag = dpg.add_child_window(
            tag=self.tag,         # 👈 这是关键：把 box 的 tag 绑定到 DPG item
            width=width,
            height=height,
            border=True,
            user_data=self        # 可选：把 Python 实例存进去，方便回调反查
        )

    def configure_item(self, item_label_list: list[str] | None) -> None:
        if item_label_list is not None:
            self.clear_item()
            self.add_items(item_label_list)

    def add_items(self, item_label_list: list[str]) -> None:
        if self.window_tag == -1:
            self.creat_child_window()
        parent_tag = self.window_tag
        for item_label in item_label_list:
            index = len(self.items_list)
            item_tag = dpg.add_selectable(
                label=item_label,
                parent=parent_tag,
                user_data=index,
                callback=self.item_event
            )
            self.items_list.append(item_tag)
        #print("Items added, tags:", self.items_list)
        #print(dpg.get_item_children(parent_tag))

    def delete_items(self, item_tags: list[int | str]) -> None:
        for item_tag in item_tags:
            if item_tag in self.items_list:
                if dpg.does_item_exist(item_tag):
                    dpg.delete_item(item_tag)
                self.items_list.remove(item_tag)
        self.selected_items_set = set()
        self.shift_select = 0
        #print("Remaining items:", self.items_list)

    def delete_select(self) -> None:
        logger.info(f"{self.tag}：开始删除选中的选项")
        self.delete_items(list(self.selected_items_set))
        logger.success(f"{self.tag}：删除完成！")

    def clear_selected(self) -> None:
        self.selected_items_set.clear()
        self._update_selected()

    def get_all_item(self) -> list[str]:
        item_data = []
        for item_tag in self.items_list:
            if dpg.does_item_exist(item_tag):
                item_data.append(dpg.get_item_configuration(item_tag)["label"])
        return item_data

    def item_event(self, sender, app_data, user_data: int) -> None:
        index = user_data
        if index >= len(self.items_list):
            return  # 安全检查
        item_tag = self.items_list[index]
        print(item_tag)

        if is_ctrl_down():
            if item_tag in self.selected_items_set:
                self.selected_items_set.remove(item_tag)
            else:
                self.selected_items_set.add(item_tag)
                self.shift_select = item_tag
        elif is_shift_down():
            if not self.selected_items_set:
                self.selected_items_set.add(item_tag)
                self.shift_select = item_tag
            else:
                shift_index = self.items_list.index(self.shift_select)
                min_i = min(index, shift_index)
                max_i = max(index, shift_index)
                self.selected_items_set = set(self.items_list[min_i:max_i + 1])
        else:
            if len(self.selected_items_set) != 1:
                last_selected = self.selected_items_set
            else:
                last_selected = self.selected_items_set.pop()

            if last_selected == item_tag:
                self.selected_items_set = set()
                self.shift_select = 0
            else:
                self.selected_items_set = {item_tag}
                self.shift_select = item_tag

        self._update_selected()

    def _update_select_box_item(self) -> None:
        pass
    def _update_selected(self, selected_items_set:set = set()) -> None:
        #print(f"==={self.window_tag}===")
        if selected_items_set != set():
            self.selected_items_set = selected_items_set

        for item_tag in self.items_list:
            if dpg.does_item_exist(item_tag):
                #print(item_tag in self.selected_items_set)
                dpg.set_value(item_tag, item_tag in self.selected_items_set)

# ========================
# 测试代码
# ========================
if __name__ == "__main__":
    creat_dpg.start()

    with dpg.window(tag="main"):
        # 方式1：自动分配 tag
        select_box1 = MultiSelectBox()
        print("Auto tag:", select_box1.tag)
        select_box1.add_items([f"Item {i}" for i in range(5)])

        # 方式2：手动指定 tag
        select_box2 = MultiSelectBox(tag="my_selector")
        print("Custom tag:", select_box2.tag)
        select_box2.add_items([f"Choice {i}" for i in range(3)])

    creat_dpg.end("main")