```markdown
# LightPyTray

[![PyPI version](https://badge.fury.io/py/lightpytray.svg)](https://pypi.org/project/lightpytray/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Platform Windows](https://img.shields.io/badge/platform-Windows-lightgrey)]()
[![Downloads](https://static.pepy.tech/badge/lightpytray)](https://pepy.tech/project/lightpytray)

**纯 `ctypes` 实现的 Windows 系统托盘库，零依赖，功能强大。**

LightPyTray 让你无需任何第三方库即可在 Windows 上创建带菜单、图标、气球通知和动画的系统托盘图标。  
所有功能通过原生 Win32 API 实现，代码干净、运行高效。

---

## ✨ 特性

- ✅ **零依赖** —— 仅使用 Python 标准库和 `ctypes`，无需 `pywin32` 或 `pystray`
- 🎨 **菜单系统** —— 支持多级子菜单、菜单图标、分隔线、菜单项状态动态修改（启用/禁用/勾选/默认）
- 💬 **气球通知** —— 完整的标题、正文、自定义图标、静音模式、回调事件
- 🎞️ **图标动画** —— 定时轮播一组自定义 `.ico` 文件，轻松实现闪烁或动态效果
- 🔄 **动态更新** —— 运行时更换托盘图标、提示文字，或整体替换菜单
- 🆔 **GUID 支持** —— 可选使用 GUID 标识图标，任务栏重启后图标自动恢复
- 🖥️ **高 DPI 优化** —— 自动设置 Per‑Monitor V2 DPI 感知，右键菜单清晰锐利
- 🧵 **线程安全** —— 消息循环运行在独立守护线程，不会阻塞主线程

---

## 📦 安装

**要求：Windows 系统，Python 3.7 及以上版本。**

```bash
pip install lightpytray
```

无需安装任何其他依赖。

---

## 🚀 快速开始

```python
from lightpytray import LightPyTray

def on_left_click():
    print("左键单击了托盘图标")

def on_quit():
    print("退出")
    tray.stop()

# 创建托盘（图标文件为 "myicon.ico"，也可设为 None 使用系统默认图标）
tray = LightPyTray(
    icon_path="myicon.ico",
    tooltip="我的应用",
    menu_items=[
        ("打开面板", lambda: print("打开主面板")),
        (None, None),                     # 分隔线
        ("退出", on_quit)
    ],
    on_left_click=on_left_click
)

tray.start()

# 保持主线程运行
import time
try:
    while tray._thread and tray._thread.is_alive():
        time.sleep(0.5)
except KeyboardInterrupt:
    tray.stop()
```

---

## 📖 详细用法

### 1. 菜单

菜单项由元组列表定义，格式灵活：

- `(文本, 回调)` → 普通菜单项
- `(文本, 回调, 图标路径)` → 带图标的菜单项
- `(文本, 子菜单列表)` → 子菜单
- `(文本, 子菜单列表, 图标路径)` → 带图标的子菜单
- `(None, None)` → 分隔线

**示例**：

```python
menu = [
    ("选项一", lambda: print("选了1"), "icon1.ico"),
    (None, None),
    ("更多", [
        ("子选项", lambda: print("子选项"), "sub.ico"),
        ("退出", tray.stop)
    ], "folder.ico")
]
tray.update_menu(menu)   # 动态替换菜单
```

#### 动态修改菜单项状态

```python
# 通过文本或命令 ID 修改状态
tray.set_menu_item_state("选项一", enabled=False)   # 禁用
tray.set_menu_item_state("退出", checked=True)      # 勾选
tray.set_menu_item_state("退出", default=True)      # 粗体（设为默认项）
```

### 2. 气球通知

```python
# 显示通知（Info 类型，10秒，静音，不使用大图标）
tray.show_balloon("新消息", "您收到一条新消息", icon_type=1, timeout=10000, no_sound=True)

# 设置回调（气球显示/隐藏/超时/点击）
tray.set_balloon_callbacks(
    user_click=lambda: print("用户点击了气球"),
    timeout=lambda: print("气球超时关闭")
)
```

`icon_type` 可选：
- `0` = 无图标
- `1` = 信息图标（默认）
- `2` = 警告图标
- `3` = 错误图标

### 3. 图标动画

```python
# 准备一组 .ico 文件
frames = ["frame1.ico", "frame2.ico", "frame3.ico"]

# 启动动画，每 400ms 切换一帧
tray.start_animation(frames, interval_ms=400)

# 停止动画，恢复原始图标
tray.stop_animation()
```

### 4. 动态更新图标和提示

```python
tray.update_icon("new_icon.ico")          # 更换托盘图标
tray.update_tooltip("新的提示文字")        # 修改鼠标悬停提示
```

### 5. GUID 标识

使用 GUID 后，即使资源管理器重启，托盘图标也能自动恢复，且卸载时更可靠。

```python
tray = LightPyTray(
    icon_path="myicon.ico",
    guid="12345678-1234-1234-1234-123456789abc"   # 自定义 GUID 字符串
)
# 或者让程序自动生成（默认行为）
```

### 6. 退出管理

在 `quit_button` 参数中可以自定义默认退出按钮，或完全隐藏。

```python
# 添加自定义退出项
tray = LightPyTray(..., quit_button=("退出程序", custom_quit_callback))

# 禁用自动退出项（需自行在菜单中调用 tray.stop()）
tray = LightPyTray(..., quit_button=(None, None))
```

---

## 🧩 示例项目

完整可运行的示例请参见仓库中的 [`example.py`](https://github.com/octopus-h/lightpytray/blob/main/example.py)，它演示了：

- 动态切换菜单 A/B
- 气球通知及回调
- 菜单状态动态修改（启用/禁用/勾选）
- 图标动画启动与停止
- 左键单击更换图标

---

## ⚙️ 技术细节

- **窗口机制**：内部创建一个隐藏窗口，在独立线程中运行 `GetMessage` 消息循环。
- **DPI 感知**：在 `start()` 时自动调用 `SetProcessDpiAwarenessContext`（Per‑Monitor V2），确保高 DPI 下清晰显示。
- **线程安全**：`stop()` 可从任意线程调用，回调均运行在托盘线程，需注意跨线程数据交换。
- **资源释放**：退出时自动销毁所有 GDI 对象、菜单和窗口，无内存泄漏。

---

## ⚠️ 注意事项

- 仅支持 **Windows** 操作系统。
- 托盘图标的尺寸由系统决定，建议使用包含多种分辨率的 `.ico` 文件以获得最佳效果。
- 所有菜单/通知回调运行在**托盘线程**中，如需更新 GUI，请使用线程间通信（如 `queue.Queue`）。
- 气球通知可能被系统静音或拦截，请确保 Windows 通知设置已允许应用发送通知。

---

## 📄 许可证

[MIT License](LICENSE) © 2024 octopus-h

---

## 🙌 贡献

欢迎提交 Issue 或 Pull Request！  
如果你有好的想法，或者发现了 bug，请到 [GitHub 仓库](https://github.com/octopus-h/lightpytray) 反馈。

---

## 📧 联系

- GitHub: [@octopus-h](https://github.com/octopus-h)
- PyPI: [lightpytray](https://pypi.org/project/lightpytray/)

---

**Made with ❤️ and pure ctypes**
```