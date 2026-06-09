"""
WindowsApi.py – Windows API declarations for LightPyTray.
All constants, structures, and function prototypes used by the tray.

WindowsApi.py – LightPyTray 的 Windows API 声明。
包含托盘所需的所有常量、结构和函数原型。
"""

import ctypes
from ctypes import wintypes

# ------------------------------------------------------------
# Constants / 常量
# ------------------------------------------------------------

# -- Window messages / 窗口消息
WM_APP = 0x8000            # Application-defined message / 应用程序自定义消息
WM_USER = 0x0400           # Private window message / 私有窗口消息
WM_DESTROY = 0x0002        # Window is being destroyed / 窗口正在销毁
WM_COMMAND = 0x0111        # Menu/item command / 菜单/项目命令
WM_LBUTTONDOWN = 0x0201    # Left mouse button down / 鼠标左键按下
WM_LBUTTONUP = 0x0202      # Left mouse button up / 鼠标左键抬起
WM_LBUTTONDBLCLK = 0x0203  # Left mouse button double-click / 鼠标左键双击
WM_RBUTTONDOWN = 0x0204    # Right mouse button down / 鼠标右键按下
WM_RBUTTONUP = 0x0205      # Right mouse button up / 鼠标右键抬起
WM_NULL = 0x0000           # Null message / 空消息
WM_TIMER = 0x0113          # Timer message / 定时器消息

# -- Shell_NotifyIcon messages / Shell_NotifyIcon 消息
NIM_ADD = 0x00000000       # Add icon to tray / 添加托盘图标
NIM_MODIFY = 0x00000001    # Modify tray icon / 修改托盘图标
NIM_DELETE = 0x00000002    # Delete tray icon / 删除托盘图标

# -- Notification icon flags / 通知图标标志
NIF_MESSAGE = 0x00000001   # Callback message is valid / 回调消息有效
NIF_ICON = 0x00000002      # Icon is valid / 图标有效
NIF_TIP = 0x00000004       # Tooltip is valid / 提示文字有效
NIF_STATE = 0x00000008     # State is valid / 状态有效
NIF_INFO = 0x00000010      # Balloon info is valid / 气泡信息有效
NIF_GUID = 0x00000020      # The guidItem is valid / guidItem 有效（标识用 GUID）

# -- LoadImage flags / 加载图像标志
LR_LOADFROMFILE = 0x00000010  # Load from file / 从文件加载
LR_DEFAULTSIZE = 0x00000040   # Use default icon size / 使用默认图标尺寸
IMAGE_ICON = 1               # Load an icon / 加载图标
IMAGE_BITMAP = 0             # Load a bitmap / 加载位图

# -- System metrics / 系统度量
SM_CXSMICON = 49    # Small icon width / 小图标宽度
SM_CYSMICON = 50    # Small icon height / 小图标高度

# -- Menu item flags / 菜单项标志
MF_STRING = 0x00000000     # String menu item / 字符串菜单项
MF_SEPARATOR = 0x00000800  # Menu separator / 菜单分隔线
MF_POPUP = 0x00000010      # Submenu popup / 子菜单弹出

# -- Menu item states (for set_menu_item_state) / 菜单项状态（用于 set_menu_item_state）
MF_GRAYED = 0x00000001     # Grayed (disabled look) / 灰色（禁用外观）
MF_DISABLED = 0x00000002   # Disabled / 禁用
MF_CHECKED = 0x00000008    # Checked (tick mark) / 勾选
MF_DEFAULT = 0x00001000    # Default item (bold) / 默认项（粗体）

# -- Color constants / 颜色常量
COLOR_MENU = 4             # Menu background / 菜单背景

# -- TrackPopupMenu flags / 弹出菜单对齐标志
TPM_LEFTALIGN = 0x0000      # Left align / 左对齐
TPM_BOTTOMALIGN = 0x0020   # Bottom align / 底部对齐
TPM_RIGHTBUTTON = 0x0002   # Right button selects / 右键选择

# -- Menu item info masks / 菜单项信息掩码
MIIM_STATE = 0x00000001    # State is valid / 状态有效
MIIM_ID = 0x00000002       # ID is valid / ID 有效
MIIM_SUBMENU = 0x00000004  # Submenu handle is valid / 子菜单句柄有效
MIIM_STRING = 0x00000040   # Text string is valid / 文本字符串有效
MIIM_FTYPE = 0x00000100    # Item type is valid / 项目类型有效
MIIM_BITMAP = 0x00000080   # Bitmap is valid / 位图有效

# -- Window class styles / 窗口类风格
CS_HREDRAW = 0x0002        # Redraw on horizontal resize / 水平尺寸变化时重绘
CS_VREDRAW = 0x0001        # Redraw on vertical resize / 垂直尺寸变化时重绘

# -- Window styles / 窗口风格
WS_OVERLAPPED = 0x00000000        # Overlapped window / 重叠窗口
WS_CAPTION = 0x00C00000           # Title bar / 标题栏
WS_SYSMENU = 0x00080000           # System menu / 系统菜单
WS_THICKFRAME = 0x00040000        # Resizable frame / 可调整大小边框
WS_MINIMIZEBOX = 0x00020000       # Minimize button / 最小化按钮
WS_MAXIMIZEBOX = 0x00010000       # Maximize button / 最大化按钮
WS_OVERLAPPEDWINDOW = (           # Standard overlapped window / 标准重叠窗口
    WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU |
    WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX
)

# -- Standard icon ID / 标准图标 ID
IDI_APPLICATION = 32512    # Default application icon / 默认应用程序图标

# -- Notification events (lParam of callback message) / 通知事件（回调消息的 lParam）
NIN_SELECT = 0x0400            # User clicked the icon (left or right) / 用户点击图标（左键或右键）
NIN_KEYSELECT = 0x0401         # User selected the icon with keyboard / 用户用键盘选择图标
NIN_BALLOONSHOW = 0x0402       # Balloon is being shown / 气球正在显示
NIN_BALLOONHIDE = 0x0403       # Balloon was hidden / 气球已消失
NIN_BALLOONTIMEOUT = 0x0404    # Balloon timed out / 气球超时关闭
NIN_BALLOONUSERCLICK = 0x0405  # User clicked the balloon / 用户点击气球

# -- Balloon icon flags (dwInfoFlags) / 气球图标标志（dwInfoFlags）
NIIF_NONE = 0x00000000          # No icon / 无图标
NIIF_INFO = 0x00000001          # Information icon / 信息图标
NIIF_WARNING = 0x00000002       # Warning icon / 警告图标
NIIF_ERROR = 0x00000003         # Error icon / 错误图标
NIIF_USER = 0x00000004          # Use hBalloonIcon (Windows XP) / 使用 hBalloonIcon（Windows XP）
NIIF_NOSOUND = 0x00000010       # No associated sound / 静默通知
NIIF_LARGE_ICON = 0x00000020    # Use large icon (Windows Vista+) / 使用大图标（Windows Vista+）

# ------------------------------------------------------------
# Type aliases / 类型别名
# ------------------------------------------------------------
WNDPROC = ctypes.WINFUNCTYPE(             # Window procedure callback / 窗口过程回调
    ctypes.c_longlong,                     # LRESULT
    wintypes.HWND,                         # hWnd
    ctypes.c_uint,                         # uMsg
    wintypes.WPARAM,                       # wParam
    wintypes.LPARAM                        # lParam
)
HICON = wintypes.HICON         # Handle to icon / 图标句柄
HWND = wintypes.HWND           # Handle to window / 窗口句柄
HMENU = wintypes.HMENU         # Handle to menu / 菜单句柄
HINSTANCE = wintypes.HINSTANCE # Handle to instance / 实例句柄
HBITMAP = wintypes.HBITMAP     # Handle to bitmap / 位图句柄
HDC = wintypes.HDC             # Handle to device context / 设备上下文句柄
HBRUSH = wintypes.HBRUSH       # Handle to brush / 画刷句柄

# ------------------------------------------------------------
# Structures / 结构体
# ------------------------------------------------------------
class POINT(ctypes.Structure):
    """Screen coordinate point / 屏幕坐标点"""
    _fields_ = [("x", ctypes.c_long),
                ("y", ctypes.c_long)]

class MSG(ctypes.Structure):
    """Windows message structure / Windows 消息结构"""
    _fields_ = [("hwnd", HWND),
                ("message", ctypes.c_uint),
                ("wParam", wintypes.WPARAM),
                ("lParam", wintypes.LPARAM),
                ("time", ctypes.c_ulong),
                ("pt", POINT)]

class WNDCLASSEXW(ctypes.Structure):
    """Extended window class (Unicode) / 扩展窗口类（Unicode）"""
    _fields_ = [("cbSize", ctypes.c_uint),
                ("style", ctypes.c_uint),
                ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int),
                ("hInstance", HINSTANCE),
                ("hIcon", HICON),
                ("hCursor", wintypes.HANDLE),
                ("hbrBackground", wintypes.HBRUSH),
                ("lpszMenuName", ctypes.c_wchar_p),
                ("lpszClassName", ctypes.c_wchar_p),
                ("hIconSm", HICON)]

class NOTIFYICONDATAW(ctypes.Structure):
    """Tray icon notification data (Unicode) / 托盘图标通知数据（Unicode）"""
    _fields_ = [("cbSize", ctypes.c_uint),
                ("hWnd", HWND),
                ("uID", ctypes.c_uint),
                ("uFlags", ctypes.c_uint),
                ("uCallbackMessage", ctypes.c_uint),
                ("hIcon", HICON),
                ("szTip", ctypes.c_wchar * 128),    # Tooltip text / 提示文字
                ("dwState", ctypes.c_uint),
                ("dwStateMask", ctypes.c_uint),
                ("szInfo", ctypes.c_wchar * 256),   # Balloon text / 气泡文字
                ("uTimeoutOrVersion", ctypes.c_uint),# Balloon timeout / 气球超时时间
                ("szInfoTitle", ctypes.c_wchar * 64),# Balloon title / 气泡标题
                ("dwInfoFlags", ctypes.c_uint),      # Balloon flags / 气球标志
                ("guidItem", ctypes.c_byte * 16),    # Item GUID / 项目 GUID
                ("hBalloonIcon", HICON)]             # Custom balloon icon / 自定义气球图标

class MENUITEMINFOW(ctypes.Structure):
    """Menu item information (Unicode) / 菜单项信息（Unicode）"""
    _fields_ = [("cbSize", ctypes.c_uint),
                ("fMask", ctypes.c_uint),
                ("fType", ctypes.c_uint),
                ("fState", ctypes.c_uint),
                ("wID", ctypes.c_uint),
                ("hSubMenu", HMENU),
                ("hbmpChecked", HBITMAP),
                ("hbmpUnchecked", HBITMAP),
                ("dwItemData", ctypes.c_void_p),
                ("dwTypeData", ctypes.c_wchar_p),
                ("cch", ctypes.c_uint),
                ("hbmpItem", HBITMAP)]      # Bitmap icon beside text / 文字旁位图图标

class RECT(ctypes.Structure):
    """Rectangle structure / 矩形结构"""
    _fields_ = [("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long)]

# ------------------------------------------------------------
# DLL loading and function prototypes / DLL 加载与函数原型
# ------------------------------------------------------------
user32 = ctypes.windll.user32         # User32.dll / 用户接口
shell32 = ctypes.windll.shell32       # Shell32.dll / Shell 接口
kernel32 = ctypes.windll.kernel32     # Kernel32.dll / 内核接口
gdi32 = ctypes.windll.gdi32           # Gdi32.dll / 图形设备接口

# -- Window management / 窗口管理
RegisterClassExW = user32.RegisterClassExW              # Register window class / 注册窗口类
RegisterClassExW.argtypes = [ctypes.POINTER(WNDCLASSEXW)]
RegisterClassExW.restype = ctypes.c_ushort

CreateWindowExW = user32.CreateWindowExW                # Create window / 创建窗口
CreateWindowExW.argtypes = [
    ctypes.c_ulong, ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_ulong,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    HWND, HMENU, HINSTANCE, ctypes.c_void_p
]
CreateWindowExW.restype = HWND

DefWindowProcW = user32.DefWindowProcW                  # Default window procedure / 默认窗口过程
DefWindowProcW.argtypes = [HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM]
DefWindowProcW.restype = ctypes.c_longlong

DestroyWindow = user32.DestroyWindow                    # Destroy a window / 销毁窗口
DestroyWindow.argtypes = [HWND]
DestroyWindow.restype = ctypes.c_bool

GetMessageW = user32.GetMessageW                        # Retrieve a message from queue / 从队列获取消息
GetMessageW.argtypes = [ctypes.POINTER(MSG), HWND, ctypes.c_uint, ctypes.c_uint]
GetMessageW.restype = ctypes.c_bool

TranslateMessage = user32.TranslateMessage              # Translate virtual-key messages / 转换虚拟键消息
TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
TranslateMessage.restype = ctypes.c_bool

DispatchMessageW = user32.DispatchMessageW              # Dispatch message to window proc / 分派消息到窗口过程
DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
DispatchMessageW.restype = ctypes.c_longlong

PostQuitMessage = user32.PostQuitMessage                # Post WM_QUIT to end message loop / 发送 WM_QUIT 结束消息循环
PostQuitMessage.argtypes = [ctypes.c_int]
PostQuitMessage.restype = None

# -- Shell notification / Shell 通知
Shell_NotifyIconW = shell32.Shell_NotifyIconW           # Add/modify/delete tray icon / 添加/修改/删除托盘图标
Shell_NotifyIconW.argtypes = [ctypes.c_uint, ctypes.POINTER(NOTIFYICONDATAW)]
Shell_NotifyIconW.restype = ctypes.c_bool

# -- Icon loading / 图标加载
LoadImageW = user32.LoadImageW                          # Load icon/cursor/bitmap / 加载图标/光标/位图
LoadImageW.argtypes = [HINSTANCE, ctypes.c_wchar_p, ctypes.c_uint,
                       ctypes.c_int, ctypes.c_int, ctypes.c_uint]
LoadImageW.restype = wintypes.HANDLE

LoadIconW = user32.LoadIconW                            # Load a predefined icon / 加载预定义图标
LoadIconW.argtypes = [HINSTANCE, ctypes.c_void_p]
LoadIconW.restype = HICON

# -- Cursor / 光标
GetCursorPos = user32.GetCursorPos                      # Get cursor screen position / 获取光标屏幕位置
GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
GetCursorPos.restype = ctypes.c_bool

SetForegroundWindow = user32.SetForegroundWindow        # Bring window to foreground / 将窗口设为前台
SetForegroundWindow.argtypes = [HWND]
SetForegroundWindow.restype = ctypes.c_bool

# -- Menu functions / 菜单函数
CreatePopupMenu = user32.CreatePopupMenu                # Create a popup menu / 创建弹出菜单
CreatePopupMenu.restype = HMENU

AppendMenuW = user32.AppendMenuW                        # Append item to menu (legacy) / 向菜单追加项目（旧版）
AppendMenuW.argtypes = [HMENU, ctypes.c_uint, ctypes.c_uint, ctypes.c_wchar_p]
AppendMenuW.restype = ctypes.c_bool

InsertMenuItemW = user32.InsertMenuItemW                # Insert menu item with full info / 插入带完整信息的菜单项
InsertMenuItemW.argtypes = [HMENU, ctypes.c_uint, ctypes.c_bool, ctypes.POINTER(MENUITEMINFOW)]
InsertMenuItemW.restype = ctypes.c_bool

TrackPopupMenu = user32.TrackPopupMenu                  # Show a popup menu at given coordinates / 在指定坐标显示弹出菜单
TrackPopupMenu.argtypes = [HMENU, ctypes.c_uint, ctypes.c_int, ctypes.c_int,
                           ctypes.c_int, HWND, ctypes.c_void_p]
TrackPopupMenu.restype = ctypes.c_bool

DestroyMenu = user32.DestroyMenu                        # Destroy a menu and free memory / 销毁菜单并释放内存
DestroyMenu.argtypes = [HMENU]
DestroyMenu.restype = ctypes.c_bool

GetMenuItemInfoW = user32.GetMenuItemInfoW              # Get menu item info / 获取菜单项信息
GetMenuItemInfoW.argtypes = [HMENU, ctypes.c_uint, ctypes.c_bool, ctypes.POINTER(MENUITEMINFOW)]
GetMenuItemInfoW.restype = ctypes.c_bool

SetMenuItemInfoW = user32.SetMenuItemInfoW              # Set menu item info / 设置菜单项信息
SetMenuItemInfoW.argtypes = [HMENU, ctypes.c_uint, ctypes.c_bool, ctypes.POINTER(MENUITEMINFOW)]
SetMenuItemInfoW.restype = ctypes.c_bool

# -- GDI / bitmap functions / GDI/位图函数
GetDC = user32.GetDC                                    # Get device context for window / 获取窗口设备上下文
GetDC.argtypes = [HWND]
GetDC.restype = HDC

ReleaseDC = user32.ReleaseDC                            # Release device context / 释放设备上下文
ReleaseDC.argtypes = [HWND, HDC]
ReleaseDC.restype = ctypes.c_bool

CreateCompatibleDC = gdi32.CreateCompatibleDC           # Create memory DC compatible with screen / 创建兼容的内存 DC
CreateCompatibleDC.argtypes = [HDC]
CreateCompatibleDC.restype = HDC

CreateCompatibleBitmap = gdi32.CreateCompatibleBitmap   # Create bitmap compatible with DC / 创建兼容位图
CreateCompatibleBitmap.argtypes = [HDC, ctypes.c_int, ctypes.c_int]
CreateCompatibleBitmap.restype = HBITMAP

SelectObject = gdi32.SelectObject                       # Select GDI object into DC / 将 GDI 对象选入 DC
SelectObject.argtypes = [HDC, wintypes.HGDIOBJ]
SelectObject.restype = wintypes.HGDIOBJ

DeleteDC = gdi32.DeleteDC                               # Delete a device context / 删除设备上下文
DeleteDC.argtypes = [HDC]
DeleteDC.restype = ctypes.c_bool

DeleteObject = gdi32.DeleteObject                       # Delete a GDI object (pen, brush, bitmap, etc.) / 删除 GDI 对象
DeleteObject.argtypes = [wintypes.HGDIOBJ]
DeleteObject.restype = ctypes.c_bool

FillRect = user32.FillRect                              # Fill rectangle with brush / 用画刷填充矩形
FillRect.argtypes = [HDC, ctypes.POINTER(RECT), HBRUSH]
FillRect.restype = ctypes.c_bool

GetSysColorBrush = user32.GetSysColorBrush              # Get brush for system color / 获取系统颜色对应的画刷
GetSysColorBrush.argtypes = [ctypes.c_int]
GetSysColorBrush.restype = HBRUSH

DrawIconEx = user32.DrawIconEx                          # Draw icon with advanced options / 绘制图标（高级选项）
DrawIconEx.argtypes = [HDC, ctypes.c_int, ctypes.c_int, HICON,
                       ctypes.c_int, ctypes.c_int, ctypes.c_uint,
                       HBRUSH, ctypes.c_uint]
DrawIconEx.restype = ctypes.c_bool

DestroyIcon = user32.DestroyIcon                        # Destroy icon and free memory / 销毁图标并释放内存
DestroyIcon.argtypes = [HICON]
DestroyIcon.restype = ctypes.c_bool

# -- Timer / 定时器
SetTimer = user32.SetTimer                              # Create a timer / 创建定时器
SetTimer.argtypes = [HWND, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p]
SetTimer.restype = ctypes.c_uint

KillTimer = user32.KillTimer                            # Destroy a timer / 销毁定时器
KillTimer.argtypes = [HWND, ctypes.c_uint]
KillTimer.restype = ctypes.c_bool

# -- DPI Awareness (for high-DPI crisp menus) / DPI 感知（使高 DPI 菜单清晰）
DPI_AWARENESS_CONTEXT_UNAWARE = -1              # DPI unaware / 无 DPI 感知
DPI_AWARENESS_CONTEXT_SYSTEM_AWARE = -2         # System DPI aware / 系统 DPI 感知
DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE = -3    # Per-monitor DPI aware / 每显示器 DPI 感知
DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4 # Per-monitor V2 (best) / 每显示器 V2（最佳）

SetProcessDpiAwarenessContext = user32.SetProcessDpiAwarenessContext  # Set process DPI mode / 设置进程 DPI 模式
SetProcessDpiAwarenessContext.argtypes = [wintypes.HANDLE]
SetProcessDpiAwarenessContext.restype = wintypes.BOOL

SetProcessDPIAware = user32.SetProcessDPIAware                       # Legacy DPI aware call / 旧版 DPI 感知调用
SetProcessDPIAware.argtypes = []
SetProcessDPIAware.restype = wintypes.BOOL

# -- System information / 系统信息
GetSystemMetrics = user32.GetSystemMetrics          # Retrieve system metric / 获取系统度量值
GetSystemMetrics.argtypes = [ctypes.c_int]
GetSystemMetrics.restype = ctypes.c_int

RegisterWindowMessageW = user32.RegisterWindowMessageW  # Define a new window message unique system-wide / 注册系统唯一的窗口消息
RegisterWindowMessageW.argtypes = [ctypes.c_wchar_p]
RegisterWindowMessageW.restype = ctypes.c_uint