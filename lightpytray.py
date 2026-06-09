"""
LightPyTray - A pure ctypes Windows system tray library.
Runs its message loop in a separate daemon thread.

LightPyTray - 纯 ctypes 实现的 Windows 系统托盘库。
在独立守护线程中运行消息循环。
"""

import threading
import os
import ctypes  # 需要用于 DPI 感知调用

from .windows_api import *

# ------------------------------------------------------------
# Global registry to map hwnd -> LightPyTray instance
# 全局注册表：将窗口句柄映射到 LightPyTray 实例
# ------------------------------------------------------------
_tray_instances = {}
_tray_lock = threading.Lock()

# ------------------------------------------------------------
# Window procedure (static, dispatches to instance methods)
# 窗口过程（静态函数，分派到实例方法）
# ------------------------------------------------------------
@WNDPROC
def _tray_window_proc(hwnd, msg, wparam, lparam):
    """Window procedure for the hidden tray window.
       隐藏托盘窗口的窗口过程。
       Dispatches messages to the corresponding LightPyTray instance.
       将消息分派给对应的 LightPyTray 实例。
    """
    instance = None
    with _tray_lock:
        instance = _tray_instances.get(hwnd)
    if instance is None:
        return DefWindowProcW(hwnd, msg, wparam, lparam)

    # Handle TaskbarCreated to restore icon after explorer restart
    # 处理 TaskbarCreated 消息，在资源管理器重启后恢复图标
    if instance._taskbar_created_msg and msg == instance._taskbar_created_msg:
        instance._on_taskbar_restart()
        return 0
    
    # Animation timer / 动画定时器
    if msg == WM_TIMER:
        instance._on_timer(wparam)
        return 0

    # Tray icon callback message (left/right click)
    # 托盘图标回调消息（左/右键点击）
    if msg == instance._callback_msg:
        if lparam == WM_LBUTTONUP:
            if instance._on_left_click:
                instance._on_left_click()
        elif lparam == WM_LBUTTONDBLCLK:
            if instance._on_left_double:
                instance._on_left_double()
            elif instance._on_left_click:
                instance._on_left_click()
        elif lparam == WM_RBUTTONUP:
            if instance._menu_items:
                instance._show_menu()
            elif instance._on_right_click:
                instance._on_right_click()

        # Balloon notification events / 气球通知事件
        elif lparam == NIN_BALLOONSHOW and instance._on_balloon_show:
            instance._on_balloon_show()
        elif lparam == NIN_BALLOONHIDE and instance._on_balloon_hide:
            instance._on_balloon_hide()
        elif lparam == NIN_BALLOONTIMEOUT and instance._on_balloon_timeout:
            instance._on_balloon_timeout()
        elif lparam == NIN_BALLOONUSERCLICK and instance._on_balloon_user_click:
            instance._on_balloon_user_click()

        return 0

    # Menu command from user click
    # 菜单命令，由用户点击菜单项触发
    if msg == WM_COMMAND:
        cmd_id = wparam & 0xFFFF
        callback = instance._menu_callbacks.get(cmd_id)
        if callback:
            callback()
        return 0

    # Window close -> quit message loop
    # 窗口关闭 -> 退出消息循环
    if msg == WM_DESTROY:
        PostQuitMessage(0)
        return 0

    return DefWindowProcW(hwnd, msg, wparam, lparam)


# ------------------------------------------------------------
# Main class
# 主类
# ------------------------------------------------------------
class LightPyTray:
    """
    A system tray icon controlled via Windows API (ctypes) running in a thread.
    基于 Windows API (ctypes) 的系统托盘图标，在独立线程中运行。

    Supports: custom .ico or default icon, menu icons, multi-level submenus,
              dynamic menu modification, TaskbarCreated handling, DPI awareness.
    支持：自定义 .ico 或默认图标、菜单图标、多级子菜单、动态菜单修改、
          TaskbarCreated 处理、DPI 感知。
    """

    _class_name = "LightPyTrayHiddenWindow"
    _class_registered = False
    _class_lock = threading.Lock()
    _dpi_initialized = False  # Whether process-level DPI awareness has been set / 进程级 DPI 感知是否已设置

    def __init__(self, icon_path=None, tooltip="LightPyTray",
                 menu_items=None, on_left_click=None, on_left_double=None,
                 on_right_click=None, quit_button=("Quit", None), guid=None):
        """
        Initialize the tray icon.
        初始化托盘图标。

        :param icon_path: Path to .ico file, or None for default icon.
                          .ico 文件路径，None 则使用默认图标。
        :param tooltip: Tooltip text (max 128 chars).
                        鼠标悬停提示文字（最长128字符）。
        :param menu_items: List of menu items, see _normalize_menu for format.
                           菜单项列表，格式参见 _normalize_menu。
        :param on_left_click: Callback for left click.
                              左键单击回调。
        :param on_left_double: Callback for left double-click.
                               左键双击回调。
        :param on_right_click: Callback for right click (ignored if menu_items provided).
                               右键单击回调（如果提供了菜单则忽略）。
        :param quit_button: Default exit button, no addition when text is None.
                            默认退出按钮，文本为None时不添加。
        :param guid: NIF_GUID
                     全局唯一标识符（可用于在任务栏重启后保持图标稳定）
        """
        self._guid = None
        if guid:
            self.set_guid(guid)        # 自定义 GUID
        else:
            self._generate_guid()      # 自动生成随机 GUID

        self._icon_path = icon_path
        self._tooltip = tooltip
        self._menu_items = []          # parsed & normalized menu structure / 解析并规范化的菜单结构
        self._on_left_click = on_left_click
        self._on_left_double = on_left_double
        self._on_right_click = on_right_click

        # 气球通知回调
        self._on_balloon_show = None
        self._on_balloon_hide = None
        self._on_balloon_timeout = None
        self._on_balloon_user_click = None

        self._hwnd = None              # Hidden window handle / 隐藏窗口句柄
        self._thread = None            # Message loop thread / 消息循环线程
        self._running = False          # Thread running flag / 线程运行标志
        self._nid = None               # NOTIFYICONDATA structure / 托盘图标数据结构
        self._hmenu = None             # Current popup menu handle / 当前弹出菜单句柄
        self._menu_callbacks = {}      # id -> callback mapping / 菜单ID到回调的映射
        self._menu_id_to_text = {}     # id -> text (for state modification) / id到文本的映射（用于状态修改）
        self._menu_icons = []          # list of HBITMAP to destroy later / 待销毁的位图列表
        self._callback_msg = WM_APP + 1  # Custom message ID for tray events / 托盘事件的自定义消息ID
        self._icon_id = 1              # Tray icon identifier (arbitrary) / 托盘图标标识符（任意唯一值）
        self._next_menu_id = 1000      # Starting command ID for menu items / 菜单项命令ID起始值

        # Register TaskbarCreated message to handle explorer restart
        # 注册 TaskbarCreated 消息以应对资源管理器重启
        self._taskbar_created_msg = RegisterWindowMessageW("TaskbarCreated")

        # 动画相关
        self._animation_icons = []      # HICON 列表
        self._animation_index = 0
        self._animation_timer_id = None

        # Parse initial menu if provided
        # 如果提供了菜单，进行解析
        if menu_items:
            _text, _func=quit_button
            if _func == None:
                _func=self.stop
            if _text != None:
                menu_items.append((_text, _func))
            self._menu_items = self._normalize_menu(menu_items)
        else:
            self._menu_items = self._normalize_menu([("quit", self.stop)])

        # Register window class once per process
        # 每个进程仅注册一次窗口类
        with self._class_lock:
            if not LightPyTray._class_registered:
                self._register_class()
                LightPyTray._class_registered = True

    # ------------------------------------------------------------
    # Window class registration
    # 窗口类注册
    # ------------------------------------------------------------
    def _register_class(self):
        """Register the hidden window class used for tray messages.
           注册用于托盘消息的隐藏窗口类。"""
        wcex = WNDCLASSEXW()
        wcex.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wcex.style = CS_HREDRAW | CS_VREDRAW
        wcex.lpfnWndProc = _tray_window_proc
        wcex.cbClsExtra = 0
        wcex.cbWndExtra = 0
        wcex.hInstance = kernel32.GetModuleHandleW(None)
        wcex.hIcon = None
        wcex.hCursor = None
        wcex.hbrBackground = None
        wcex.lpszMenuName = None
        wcex.lpszClassName = self._class_name
        wcex.hIconSm = None
        if not RegisterClassExW(ctypes.byref(wcex)):
            raise ctypes.WinError()

    # ------------------------------------------------------------
    # Icon loading
    # 图标加载
    # ------------------------------------------------------------
    def _load_icon(self):
        """Load the tray icon (from file or default system icon).
           加载托盘图标（从文件或系统默认图标）。
           Returns an HICON handle.
           返回 HICON 句柄。"""
        if self._icon_path:
            if not os.path.isfile(self._icon_path):
                raise FileNotFoundError(f"Icon file not found: {self._icon_path}")
            hicon = LoadImageW(None, self._icon_path, IMAGE_ICON, 0, 0,
                               LR_LOADFROMFILE | LR_DEFAULTSIZE)
            if not hicon:
                raise ctypes.WinError()
            return hicon
        else:
            hicon = LoadIconW(None, ctypes.c_void_p(IDI_APPLICATION))
            if not hicon:
                raise ctypes.WinError()
            return hicon

    def _load_menu_icon(self, icon_path):
        """Load an .ico file and convert to a menu-sized HBITMAP.
           加载 .ico 文件并转换为菜单尺寸的 HBITMAP。
           This is used to show icons next to menu text.
           用于在菜单文字旁显示图标。"""
        ico_x = GetSystemMetrics(SM_CXSMICON)
        ico_y = GetSystemMetrics(SM_CYSMICON)
        hicon = LoadImageW(None, icon_path, IMAGE_ICON, ico_x, ico_y, LR_LOADFROMFILE)
        if not hicon:
            return None

        # Create a compatible bitmap and draw the icon
        # 创建兼容位图并绘制图标
        hdc_screen = GetDC(None)
        hdc_mem = CreateCompatibleDC(hdc_screen)
        hbm = CreateCompatibleBitmap(hdc_screen, ico_x, ico_y)
        hbm_old = SelectObject(hdc_mem, hbm)

        brush = GetSysColorBrush(COLOR_MENU)
        rect = RECT(0, 0, ico_x, ico_y)
        FillRect(hdc_mem, ctypes.byref(rect), brush)

        DrawIconEx(hdc_mem, 0, 0, hicon, ico_x, ico_y, 0, None, 0x0003)  # DI_NORMAL | DI_COMPAT

        SelectObject(hdc_mem, hbm_old)
        DeleteDC(hdc_mem)
        ReleaseDC(None, hdc_screen)
        DestroyIcon(hicon)

        return hbm

    # ------------------------------------------------------------
    # Menu normalization
    # 菜单规范化
    # ------------------------------------------------------------
    def _normalize_menu(self, items):
        """
        Convert user-provided menu list into a canonical structure.
        将用户提供的菜单列表转换为标准内部结构。

        Supported formats per item:
        每个菜单项支持的格式：
            - (text, callback)                 -> normal item, no icon / 普通项，无图标
            - (text, callback, icon_path)      -> normal item with icon / 普通项，带图标
            - (text, [...])                    -> submenu, no icon / 子菜单，无图标
            - (text, [...], icon_path)         -> submenu with icon / 子菜单，带图标
            - (None, None)                     -> separator / 分隔线

        Each resulting item is a dict:
            - type: 'separator' | 'item' | 'submenu'
            - text: str or None
            - callback: callable or None
            - icon_path: str or None
            - children: list (only for submenu)
        """
        result = []
        for entry in items:
            if not isinstance(entry, (tuple, list)) or len(entry) < 2:
                continue
            # Separator: (None, None)
            if entry[0] is None and len(entry) == 2 and entry[1] is None:
                result.append({"type": "separator"})
                continue

            text = entry[0]
            second = entry[1]
            if isinstance(second, (list, tuple)):
                # submenu
                children = self._normalize_menu(second)
                icon = entry[2] if len(entry) > 2 else None
                result.append({
                    "type": "submenu",
                    "text": str(text),
                    "icon_path": icon,
                    "children": children
                })
            else:
                # normal item
                callback = second
                icon = entry[2] if len(entry) > 2 else None
                result.append({
                    "type": "item",
                    "text": str(text),
                    "callback": callback,
                    "icon_path": icon
                })
        return result

    # ------------------------------------------------------------
    # Window creation
    # 创建窗口
    # ------------------------------------------------------------
    def _create_hidden_window(self):
        """Create a hidden top-level window to receive tray messages.
           创建接收托盘消息的隐藏顶级窗口。"""
        self._hwnd = CreateWindowExW(
            0, self._class_name, "",
            WS_OVERLAPPEDWINDOW,
            0, 0, 1, 1,
            None, None,
            kernel32.GetModuleHandleW(None),
            None
        )
        if not self._hwnd:
            raise ctypes.WinError()
        with _tray_lock:
            _tray_instances[self._hwnd] = self

    # ------------------------------------------------------------
    # Tray icon
    # 托盘图标
    # ------------------------------------------------------------
    def _generate_guid(self):
        """Generate a random 16-byte GUID for the tray icon.
        生成 16 字节随机 GUID 用于托盘图标。"""
        import random
        raw = bytes(random.randint(0, 255) for _ in range(16))
        self._set_guid_raw(raw)

    def set_guid(self, guid):
        """Set a custom GUID (string like '{...}' or raw 16 bytes).
        设置自定义 GUID（字符串或 16 字节原始数据）。"""
        if isinstance(guid, str):
            # Parse GUID string (remove braces and hyphens, then decode hex)
            # 解析 GUID 字符串（移除花括号和连字符后 hex 解码）
            clean = guid.strip('{}').replace('-', '')
            if len(clean) != 32:
                raise ValueError("GUID must be 32 hex digits")
            raw = bytes.fromhex(clean)
            self._set_guid_raw(raw)
        elif isinstance(guid, (bytes, bytearray)) and len(guid) == 16:
            self._set_guid_raw(bytes(guid))
        else:
            raise TypeError("guid must be a 16-byte bytes-like or GUID string")

    def _set_guid_raw(self, raw):
        """Internal: set GUID from 16-byte raw data.
        内部函数：用 16 字节原始数据设置 GUID。"""
        self._guid = raw
        self._guid_str = '{%08X-%04X-%04X-%02X%02X-%02X%02X%02X%02X%02X%02X}' % (
            int.from_bytes(raw[0:4], 'little'),
            int.from_bytes(raw[4:6], 'little'),
            int.from_bytes(raw[6:8], 'little'),
            raw[8], raw[9],
            raw[10], raw[11], raw[12], raw[13], raw[14], raw[15]
        )

    def _add_tray_icon(self):
        """Add the tray icon via Shell_NotifyIcon.
           通过 Shell_NotifyIcon 添加托盘图标。"""
        hicon = self._load_icon()
        self._nid = NOTIFYICONDATAW()
        self._nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        self._nid.hWnd = self._hwnd
        self._nid.uID = self._icon_id
        self._nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        # If GUID is set, use GUID identifier (add NIF_GUID flag)
        # 如果设置了 GUID，则使用 GUID 标识（并附加 NIF_GUID 标志）
        if self._guid:
            ctypes.memmove(self._nid.guidItem, self._guid, 16)
            self._nid.uFlags |= NIF_GUID
        self._nid.uCallbackMessage = self._callback_msg
        self._nid.hIcon = hicon
        self._nid.szTip = self._tooltip
        if not Shell_NotifyIconW(NIM_ADD, ctypes.byref(self._nid)):
            raise ctypes.WinError()

    def _refresh_tray_icon(self):
        """Re-add the tray icon (used after TaskbarCreated).
           重新添加托盘图标（TaskbarCreated 后使用）。"""
        self._add_tray_icon()
        self._build_menu()

    def _on_timer(self, timer_id):
        """Timer callback (handles WM_TIMER).
        定时器回调（WM_TIMER 处理）。"""
        if timer_id == self._animation_timer_id and self._animation_icons:
            self._animation_index = (self._animation_index + 1) % len(self._animation_icons)
            self._set_icon(self._animation_icons[self._animation_index])

    def _set_icon(self, hicon):
        """Change only the icon without triggering other updates.
        仅修改图标，不触发其他更新。"""
        if self._nid:
            self._nid.hIcon = hicon
            self._nid.uFlags = NIF_ICON
            if self._guid:
                self._nid.uFlags |= NIF_GUID
            if not Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(self._nid)):
                raise ctypes.WinError()

    # ------------------------------------------------------------
    # Menu building & display
    # 菜单构建与显示
    # ------------------------------------------------------------
    def _build_menu(self):
        """Build the right-click popup menu from the current menu items.
           根据当前菜单项构建右键弹出菜单。"""
        # Destroy previous menu and icons
        # 销毁之前的菜单和图标
        if self._hmenu:
            DestroyMenu(self._hmenu)
            self._hmenu = None
        self._release_menu_icons()

        self._menu_callbacks.clear()
        self._next_menu_id = 1000
        self._hmenu = CreatePopupMenu()
        self._populate_menu(self._hmenu, self._menu_items)

    def _populate_menu(self, menu_handle, items):
        """Recursively insert items into a menu handle.
        递归地将菜单项插入菜单句柄。"""
        for item in items:                                   # Forward order, keep original order / 正向遍历，保持顺序
            if item["type"] == "separator":
                AppendMenuW(menu_handle, MF_SEPARATOR, 0, None)
            elif item["type"] == "item":
                hbmp = None
                if item["icon_path"]:
                    hbmp = self._load_menu_icon(item["icon_path"])
                    if hbmp:
                        self._menu_icons.append(hbmp)
                cmd_id = self._next_menu_id
                self._next_menu_id += 1
                self._menu_callbacks[cmd_id] = item["callback"]
                self._menu_id_to_text[cmd_id] = item["text"]

                mii = MENUITEMINFOW()
                mii.cbSize = ctypes.sizeof(MENUITEMINFOW)
                mii.fMask = MIIM_ID | MIIM_FTYPE | MIIM_STATE | MIIM_STRING
                if hbmp:
                    mii.fMask |= MIIM_BITMAP
                    mii.hbmpItem = hbmp
                mii.fType = MF_STRING
                mii.fState = 0
                mii.wID = cmd_id
                mii.dwTypeData = item["text"]
                mii.cch = len(item["text"])
                InsertMenuItemW(menu_handle, -1, True, ctypes.byref(mii))  # -1 → append to end / 追加到末尾
            elif item["type"] == "submenu":
                submenu = CreatePopupMenu()
                self._populate_menu(submenu, item["children"])
                hbmp = None
                if item["icon_path"]:
                    hbmp = self._load_menu_icon(item["icon_path"])
                    if hbmp:
                        self._menu_icons.append(hbmp)
                dummy_id = self._next_menu_id
                self._next_menu_id += 1
                mii = MENUITEMINFOW()
                mii.cbSize = ctypes.sizeof(MENUITEMINFOW)
                mii.fMask = MIIM_ID | MIIM_FTYPE | MIIM_STATE | MIIM_STRING | MIIM_SUBMENU
                if hbmp:
                    mii.fMask |= MIIM_BITMAP
                    mii.hbmpItem = hbmp
                mii.fType = MF_STRING
                mii.fState = 0
                mii.wID = dummy_id
                mii.dwTypeData = item["text"]
                mii.cch = len(item["text"])
                mii.hSubMenu = submenu
                InsertMenuItemW(menu_handle, -1, True, ctypes.byref(mii))  # -1 → append to end / 追加到末尾

    def _release_menu_icons(self):
        """Delete all bitmaps we created for menu icons.
           释放所有为菜单图标创建的位图。"""
        for hbmp in self._menu_icons:
            DeleteObject(hbmp)
        self._menu_icons.clear()

    def _show_menu(self):
        """Display the right-click popup menu at the cursor position.
           在鼠标位置显示右键弹出菜单。"""
        if not self._hmenu:
            self._build_menu()
        if not self._hmenu:
            return
        SetForegroundWindow(self._hwnd)
        pt = POINT()
        GetCursorPos(ctypes.byref(pt))
        TrackPopupMenu(self._hmenu, TPM_LEFTALIGN | TPM_BOTTOMALIGN | TPM_RIGHTBUTTON,
                       pt.x, pt.y, 0, self._hwnd, None)
        user32.PostMessageW(self._hwnd, WM_NULL, 0, 0)

    # ------------------------------------------------------------
    # Taskbar restart handling
    # 任务栏重启处理
    # ------------------------------------------------------------
    def _on_taskbar_restart(self):
        """Handle WM_TASKBARCREATED: re-add icon and rebuild menu.
           处理 WM_TASKBARCREATED：重新添加图标并重建菜单。"""
        self._nid = None  # reset to force NIM_ADD / 重置以便执行 NIM_ADD
        self._refresh_tray_icon()

    # ------------------------------------------------------------
    # Message loop
    # 消息循环
    # ------------------------------------------------------------
    def _message_loop(self):
        """Standard GetMessage loop; exits on WM_QUIT.
           标准 GetMessage 循环；收到 WM_QUIT 时退出。"""
        msg = MSG()
        while self._running:
            ret = GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret <= 0:
                break
            TranslateMessage(ctypes.byref(msg))
            DispatchMessageW(ctypes.byref(msg))
        self._cleanup()

    def _cleanup(self):
        """Remove tray icon, destroy window, and release resources.
           移除托盘图标、销毁窗口并释放资源。"""
        if self._nid and self._hwnd:
            # Rebuild a NOTIFYICONDATA for deletion, must contain GUID if used
            # 重新构造一个用于删除的 NOTIFYICONDATA，必须包含 GUID（如果使用了）
            nid = NOTIFYICONDATAW()
            nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
            nid.hWnd = self._hwnd
            nid.uID = self._icon_id
            if self._guid:
                nid.uFlags = NIF_GUID
                ctypes.memmove(nid.guidItem, self._guid, 16)
            Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))
            self._nid = None
        self._release_menu_icons()
        if self._hmenu:
            DestroyMenu(self._hmenu)
            self._hmenu = None
        if self._hwnd:
            with _tray_lock:
                _tray_instances.pop(self._hwnd, None)
            DestroyWindow(self._hwnd)
            self._hwnd = None

    # ------------------------------------------------------------
    # DPI awareness (for crisp menus on high-DPI displays)
    # DPI 感知（使高 DPI 显示器上的菜单清晰）
    # ------------------------------------------------------------
    @staticmethod
    def _set_dpi_awareness():
        """Set process-level DPI awareness to ensure sharp menu text.
           设置进程级 DPI 感知，确保菜单文字清晰。

           Prefers Per-Monitor V2, falls back to System Aware, then to legacy SetProcessDPIAware.
           优先使用 Per-Monitor V2，回退到 System Aware，再回退到旧版 SetProcessDPIAware。
        """
        try:
            # Windows 10 1607+
            if not SetProcessDpiAwarenessContext(
                ctypes.c_void_p(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)
            ):
                # fallback to system aware / 回退到系统感知
                SetProcessDpiAwarenessContext(
                    ctypes.c_void_p(DPI_AWARENESS_CONTEXT_SYSTEM_AWARE)
                )
        except AttributeError:
            # Windows 8.1 or earlier / Windows 8.1 或更早
            SetProcessDPIAware()

    # ------------------------------------------------------------
    # Public API
    # 公共接口
    # ------------------------------------------------------------
    def _run(self):
        """Entry point for the background thread.
           后台线程入口。"""
        self._running = True
        self._create_hidden_window()
        self._build_menu()
        self._add_tray_icon()
        self._message_loop()

    def start(self):
        """Start the tray icon in a new daemon thread.
           在新的守护线程中启动托盘图标。"""
        if self._thread and self._thread.is_alive():
            return

        # Set DPI awareness once per process to avoid blurry menus
        # 每个进程设置一次 DPI 感知，避免菜单模糊
        if not self._dpi_initialized:
            self._set_dpi_awareness()
            LightPyTray._dpi_initialized = True

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the tray icon and wait for the thread to finish.
           停止托盘图标并等待线程结束。

           Can be safely called from any thread.
           可从任何线程安全调用。"""
        if not self._running:
            return
        self._running = False
        if self._hwnd:
            user32.PostMessageW(self._hwnd, WM_DESTROY, 0, 0)
        if self._thread and threading.current_thread() != self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def update_icon(self, new_icon_path=None):
        """Change the tray icon at runtime.
           运行时更换托盘图标。

           :param new_icon_path: Path to .ico file, or None to use default icon.
                                 .ico 文件路径，或 None 使用默认图标。"""
        if not self._running or not self._nid or not self._hwnd:
            raise RuntimeError("Tray is not running")
        self._icon_path = new_icon_path
        hicon = self._load_icon()
        self._nid.uFlags = NIF_ICON
        if self._guid:
            self._nid.uFlags |= NIF_GUID
        self._nid.hIcon = hicon
        if not Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(self._nid)):
            raise ctypes.WinError()

    def update_tooltip(self, new_tooltip):
        """Change the tray tooltip.
           修改托盘提示文字。

           :param new_tooltip: New tooltip string (max 128 chars).
                               新的提示字符串（最长128字符）。"""
        if not self._running or not self._nid or not self._hwnd:
            raise RuntimeError("Tray is not running")
        self._tooltip = new_tooltip
        self._nid.uFlags = NIF_TIP
        if self._guid:
            self._nid.uFlags |= NIF_GUID
        self._nid.szTip = self._tooltip
        if not Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(self._nid)):
            raise ctypes.WinError()

    def update_menu(self, menu_items):
        """Dynamically replace the entire right-click menu.
           动态替换整个右键菜单。

           :param menu_items: New menu structure (see _normalize_menu for format).
                              新的菜单结构（格式参见 _normalize_menu）。"""
        if not self._running:
            raise RuntimeError("Tray is not running")
        self._menu_items = self._normalize_menu(menu_items)
        self._build_menu()

    def show_balloon(self, title, text, icon_type=NIIF_INFO, timeout=5000, no_sound=False, use_large_icon=False):
        """Show a balloon notification.
        显示气球通知。

        :param title: Balloon title / 气球标题
        :param text: Balloon body text / 气球正文
        :param icon_type: NIIF_INFO, NIIF_WARNING, NIIF_ERROR or NIIF_NONE / 图标类型
        :param timeout: Display time in ms / 显示时间（毫秒）
        :param no_sound: Disable notification sound / 静默通知
        :param use_large_icon: Use large balloon icon / 使用大图标
        """
        if not self._nid:
            raise RuntimeError("Tray not started")
        self._nid.uFlags = NIF_INFO
        if self._guid:
            self._nid.uFlags |= NIF_GUID
        self._nid.dwInfoFlags = icon_type
        if no_sound:
            self._nid.dwInfoFlags |= NIIF_NOSOUND
        if use_large_icon:
            self._nid.dwInfoFlags |= NIIF_LARGE_ICON
        self._nid.szInfoTitle = title[:63]
        self._nid.szInfo = text[:255]
        self._nid.uTimeoutOrVersion = timeout
        if not Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(self._nid)):
            raise ctypes.WinError()

    def set_balloon_callbacks(self, show=None, hide=None, timeout=None, user_click=None):
        """Set balloon notification event callbacks.
        设置气球通知事件回调。

        :param show: called when balloon shows / 气球显示时调用
        :param hide: called when balloon hides / 气球消失时调用
        :param timeout: called when balloon times out / 气球超时时调用
        :param user_click: called when user clicks balloon / 用户点击气球时调用
        """
        self._on_balloon_show = show
        self._on_balloon_hide = hide
        self._on_balloon_timeout = timeout
        self._on_balloon_user_click = user_click

    def set_menu_item_state(self, identifier, enabled=None, checked=None, default=None):
        """
        Dynamically modify the state of a menu item.
        动态修改菜单项的状态。

        :param identifier: Menu item text or command ID / 菜单项文本或命令 ID
        :param enabled: True/False to enable/disable, None to leave unchanged / 启用/禁用
        :param checked: True/False to check/uncheck, None to leave unchanged / 勾选/取消勾选
        :param default: True/False to set as default (bold), None to leave unchanged / 设为默认项（粗体）
        """
        # If identifier is a string, find the corresponding cmd_id
        # 如果 identifier 是字符串，查找对应的 cmd_id
        if isinstance(identifier, str):
            cmd_id = None
            for id_, text in self._menu_id_to_text.items():
                if text == identifier:
                    cmd_id = id_
                    break
            if cmd_id is None:
                raise ValueError(f"Menu item '{identifier}' not found")
        elif isinstance(identifier, int):
            cmd_id = identifier
        else:
            raise TypeError("identifier must be str or int")

        # Retrieve current state / 获取当前状态
        mii = MENUITEMINFOW()
        mii.cbSize = ctypes.sizeof(MENUITEMINFOW)
        mii.fMask = MIIM_STATE
        if not GetMenuItemInfoW(self._hmenu, cmd_id, False, ctypes.byref(mii)):
            raise ctypes.WinError()

        # Modify state flags / 修改状态位
        if enabled is not None:
            if enabled:
                mii.fState &= ~(MF_GRAYED | MF_DISABLED)
            else:
                mii.fState |= (MF_GRAYED | MF_DISABLED)
        if checked is not None:
            if checked:
                mii.fState |= MF_CHECKED
            else:
                mii.fState &= ~MF_CHECKED
        if default is not None:
            if default:
                mii.fState |= MF_DEFAULT
            else:
                mii.fState &= ~MF_DEFAULT

        mii.fMask = MIIM_STATE
        if not SetMenuItemInfoW(self._hmenu, cmd_id, False, ctypes.byref(mii)):
            raise ctypes.WinError()

    def start_animation(self, icon_paths, interval_ms=200):
        """
        Start icon animation: cycle through a list of .ico files.
        开始图标动画：循环播放一组 .ico 文件。

        :param icon_paths: List of icon file paths (must exist) / 图标文件路径列表（必须存在）
        :param interval_ms: Switch interval in ms / 切换间隔（毫秒）
        """
        if not self._running:
            raise RuntimeError("Tray not started")
        self.stop_animation()  # stop previous animation / 停止之前的动画

        self._animation_icons = []
        for path in icon_paths:
            if not os.path.isfile(path):
                raise FileNotFoundError(f"Icon not found: {path}")
            hicon = LoadImageW(None, path, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE)
            if not hicon:
                raise ctypes.WinError()
            self._animation_icons.append(hicon)

        self._animation_index = 0
        # Set the first frame / 设置第一帧
        self._set_icon(self._animation_icons[0])

        # Start timer (ID=1) / 启动定时器（ID=1）
        self._animation_timer_id = 1
        SetTimer(self._hwnd, self._animation_timer_id, interval_ms, None)

    def stop_animation(self):
        """Stop animation and restore the original icon.
        停止动画，恢复为原始图标。"""
        if self._animation_timer_id is not None:
            KillTimer(self._hwnd, self._animation_timer_id)
            self._animation_timer_id = None
        # Destroy animation icons / 销毁动画图标
        for hicon in self._animation_icons:
            DestroyIcon(hicon)
        self._animation_icons.clear()
        # Restore original icon / 恢复原始图标
        if self._icon_path:
            self.update_icon(self._icon_path)
        else:
            self.update_icon(None)   # default icon / 默认图标