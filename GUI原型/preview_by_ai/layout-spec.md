# CSFM → MOD 导出工具 · GUI 布局规格

> HTML 预览：`preview/csfm-mod-tool-preview.html`  
> 目标实现：DearPyGui（ImGui 后端），风格参考项目内 `sys_gui.py` + `dpg_gui/themes.py`

## 窗口结构

```
视口 (1280×800, tag: main)
├── menu_bar
│   ├── 文件：扫描 input / 选择输出目录 / 导出 MOD / 保存配置 / 加载配置
│   └── 帮助：README / 关于
├── horizontal group (主区域)
│   ├── child_window 左侧 (width=300, tag: sidebar)
│   │   ├── separator「导入 CSFM」
│   │   ├── input_text (tag: import_path_hint)
│   │   ├── buttons: scan_input, add_folder, remove_selected, clear_all
│   │   ├── separator「已导入歌曲」
│   │   ├── child_window / table (tag: song_list) — 可滚动列表
│   │   ├── separator「导出选项」
│   │   ├── checkbox (tag: opt_convert_audio) 默认 true
│   │   ├── checkbox (tag: opt_convert_video) 默认 false
│   │   ├── checkbox (tag: opt_build_spr) 默认 true
│   │   ├── separator「输出」
│   │   ├── input_text (tag: output_path)
│   │   └── button (tag: btn_export_mod, label: 开始导出 MOD)
│   └── child_window 右侧 (tag: detail_panel)
│       ├── tab_bar
│       │   ├── tab「歌曲概览」（只读）
│       │   │   ├── 顶栏右侧按钮「显示英文」↔ 切换原名/英文（替换显示，非叠加）
│       │   │   ├── 上：曲名 → 读音 / 作曲 / 编曲 / 作词 + JK
│       │   │   └── 下：难度横向栏
│       │   ├── tab「歌曲信息配置」（可编辑）
│       │   │   ├── 上：曲名/读音/作曲/编曲/作词 — 日文|英文 双列输入 + JK 预览
│       │   │   └── 下：背景图 / JK / LOGO 路径 + 浏览 + 缩略图
│       │   └── tab「谱面配置」→ 导出勾选、等级覆盖
│       └── progress / 状态栏
└── progress_bar (tag: export_progress, overlay)
```

## 数据绑定（对接 csfm-to-mm-tool-main）

| UI 区域 | 后端来源 |
|--------|----------|
| 曲名/作曲/编曲/作词（只读） | `song_name`, `songinfo.*`；英文键 `song_name_en`, `songinfo_en.*`（随按钮切换） |
| 读音（只读） | `song_name_reading`，仅日文；**不**随「显示英文」切换 |
| 顶栏 BPM | `meta_data["bpm"]` |
| JK 预览 | `jk_path` / 纹理加载 |
| 难度卡片 | `ChartInfo.easy` … `ex_extreme` + `Chart["Difficulty"]["Level"]` + `check_slide()` |
| 歌曲信息配置 Tab | 日英字段可编辑 → `song_name`/`song_name_en`、`songinfo*`、`songinfo_en*`、`song_name_reading`；`bg/jk/logo` 路径 |
| 谱面配置 Tab | 导出开关、等级覆盖 |
| 转换音频/视频 | `FFmpegNormalize` / `video_convert/` |
| 导出 | `export_chart()` + `mod_pv_db.txt` + `mod_spr_db.bin` |

## 难度枚举映射

与 `lib/CsfmDataClass.py` 中 `Difficulty` 一致：

| 显示名 | 属性 | mod_pv_db 键 |
|--------|------|----------------|
| EASY | `easy` | difficulty.easy |
| NORMAL | `normal` | difficulty.normal |
| HARD | `hard` | difficulty.hard |
| EXTREME | `extreme` | difficulty.extreme |
| EX EXTREME | `ex_extreme` | difficulty.extraextreme |

## 交互流程

1. **扫描/添加** → `read_csfm` 遍历 → 按 `pv_id` 合并为 `chart_info_dict[pv_id]`
2. **列表选中** → 概览/信息配置/谱面配置三 Tab 同步刷新
3. **难度栏** → 仅展示；点击卡片可选中并跳转谱面配置（可选实现）
4. **全局勾选** → 批量导出时对所有歌曲应用音频/视频策略
5. **导出** → `create_output_folder()` → 循环 `export_chart` → 写 db

## DearPyGui 控件 tag 建议

```text
song_list
opt_convert_audio, opt_convert_video, opt_build_spr
# 歌曲概览（只读 text 或 draw_text）
btn_toggle_lang         # 顶栏右侧，切换后刷新 disp_* 与 current_title
disp_title, disp_reading, disp_music, disp_arranger, disp_lyrics
jk_preview_image
diff_bar_group          # 横向 child_window + 每难度一张「卡片」
# 谱面配置（可编辑）
cfg_title, cfg_title_en, cfg_reading
cfg_music, cfg_music_en
cfg_arranger, cfg_arranger_en, cfg_lyrics, cfg_lyrics_en
path_bg, path_jk, path_logo
thumb_bg, thumb_logo, jk_preview_cfg
chart_table
btn_export_mod
export_progress
```

## 与现有项目关系

- 当前仓库 `init.py` / `sys_gui.py` 为另一套「电池管理」GUI，MOD 工具应新建 `mod_gui/` + `mod_init.py`，复用 `dpg_gui/creat_dpg.py`。
- 业务逻辑 `import` `csfm-to-mm-tool-main` 下 `lib`、`FarcCreater`、`auto_creat_mod_spr_db` 等。
