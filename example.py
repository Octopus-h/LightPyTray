import time
from lightpytray import LightPyTray

ANIMATION_FRAMES = ["example.ico", "example2.ico"]

# ---------- 回调函数 ----------
def on_left():
    tray.update_tooltip("example2.ico")
    print("[Tray] 左键单击")

def on_quit():
    print("[Tray] 退出")
    tray.stop()

def on_balloon_click():
    print("[气球] 用户点击了通知")

def on_balloon_timeout():
    print("[气球] 通知已超时消失")

def switch_menu_b():
    print("切换到菜单 B")
    tray.update_menu(menu_b)

def switch_menu_a():
    print("切换到菜单 A")
    tray.update_menu(menu_a)

def show_balloon_demo():
    print("发送气球通知...")
    tray.show_balloon("你好 👋", "这是一条带大图标的通知", icon_type=1,
                        timeout=3000, use_large_icon=True)

def disable_switch_a():
    tray.set_menu_item_state("切换到菜单A", enabled=False)
    print("“切换到菜单A”已禁用")

def enable_switch_a():
    tray.set_menu_item_state("切换到菜单A", enabled=True)
    print("“切换到菜单A”已启用")

def toggle_check():
    # 切换“模式”菜单项的勾选状态（演示 checked 属性）
    import random
    checked = random.choice([True, False])
    tray.set_menu_item_state("模式", checked=checked)
    print(f"“模式”勾选状态 → {checked}")

def start_anim():
    try:
        tray.start_animation(ANIMATION_FRAMES, interval_ms=400)
        print("动画已启动")
    except Exception as e:
        print(f"动画启动失败: {e}（请检查图标文件是否存在）")

def stop_anim():
    tray.stop_animation()
    print("动画已停止")

# ---------- 菜单定义 ----------
quit_item = ("退出", on_quit)

menu_a = [
    ("Main A", lambda: print("Main A clicked"), "example.ico"),
    (None, None),                     # 分隔线
    ("显示气球通知", show_balloon_demo),
    ("开始动画", start_anim),
    ("停止动画", stop_anim),
    (None, None),
    ("切换到菜单B", switch_menu_b),
    quit_item,
]

menu_b = [
    ("Main B", lambda: print("Main B clicked")),
    (None, None),
    ("模式", lambda: print("切换")),   # 用于演示 checked 修改
    ("禁用“切换到菜单A”", disable_switch_a),
    ("启用“切换到菜单A”", enable_switch_a),
    (None, None),
    ("切换勾选“模式”", toggle_check),
    (None, None),
    ("切换到菜单A", switch_menu_a),
    quit_item,
]

# ---------- 创建托盘 ----------
tray = LightPyTray(
    icon_path="example.ico",          # None 则使用默认系统图标
    tooltip="动态菜单 + 动画 + 气球演示",
    menu_items=menu_a,
    on_left_click=on_left,
    quit_button=(None, None)          # 手动管理退出项
)

# 设置气球通知回调
tray.set_balloon_callbacks(
    user_click=on_balloon_click,
    timeout=on_balloon_timeout
)

tray.start()
print("托盘已启动。")
print("  - 右键菜单可切换菜单A/B")
print("  - 点击“显示气球通知”查看带大图标的气泡")
print("  - 菜单B中可动态禁用/启用、切换勾选状态")
print("  - “开始/停止动画”让图标轮播")

try:
    while tray._thread and tray._thread.is_alive():
        time.sleep(0.5)
except KeyboardInterrupt:
    tray.stop()