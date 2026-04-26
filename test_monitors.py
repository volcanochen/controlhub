import ctypes
from ctypes import wintypes, Structure, POINTER, byref

# Define necessary structures
class RECT(Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]

class MONITORINFOEX(Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
        ("szDevice", ctypes.c_wchar * 32),
    ]

def callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
    monitors.append(hMonitor)
    return True

monitors = []
MONITORENUMPROC = ctypes.WINFUNCTYPE(
    ctypes.c_bool,
    ctypes.c_void_p,
    ctypes.c_void_p,
    POINTER(RECT),
    ctypes.c_void_p
)

callback_func = MONITORENUMPROC(callback)

user32 = ctypes.windll.user32
result = user32.EnumDisplayMonitors(None, None, callback_func, 0)

print(f"Found {len(monitors)} monitor(s)")

for i, hMonitor in enumerate(monitors):
    mi = MONITORINFOEX()
    mi.cbSize = ctypes.sizeof(MONITORINFOEX)
    user32.GetMonitorInfoW(hMonitor, byref(mi))
    
    print(f"\nMonitor {i+1}:")
    print(f"  Device: {mi.szDevice}")
    print(f"  Position: ({mi.rcMonitor.left}, {mi.rcMonitor.top})")
    print(f"  Size: {mi.rcMonitor.right - mi.rcMonitor.left} x {mi.rcMonitor.bottom - mi.rcMonitor.top}")
    print(f"  Flags: {mi.dwFlags} (1=primary)")
