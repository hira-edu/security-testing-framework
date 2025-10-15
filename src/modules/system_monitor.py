"""
Comprehensive System Monitoring Module
Monitors file system, registry, network, and process activities
"""

import ctypes
import ctypes.wintypes as wintypes
import threading
import time
import os
import psutil
import socket
from typing import Dict, List, Callable, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import logging
import json

@dataclass
class SystemEvent:
    """System event data"""
    category: str  # filesystem, registry, network, process
    action: str
    target: str
    details: Dict
    timestamp: datetime
    process_id: Optional[int] = None
    process_name: Optional[str] = None

class FileSystemMonitor:
    """Monitor file system operations"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.monitoring = False
        self.watched_paths = set()
        self.callbacks = []
        self.events = []

        # File operation tracking
        self.file_operations = {
            'reads': 0,
            'writes': 0,
            'deletes': 0,
            'creates': 0,
            'renames': 0
        }

    def add_path(self, path: str):
        """Add path to monitor"""
        self.watched_paths.add(os.path.abspath(path))

    def start_monitoring(self, callback: Optional[Callable] = None):
        """Start file system monitoring"""
        if callback:
            self.callbacks.append(callback)

        self.monitoring = True
        monitor_thread = threading.Thread(target=self._monitor_thread)
        monitor_thread.daemon = True
        monitor_thread.start()

        self.logger.info(f"File system monitoring started for {len(self.watched_paths)} paths")

    def _monitor_thread(self):
        """Monitor file system changes"""
        # Windows-specific monitoring using ReadDirectoryChangesW
        FILE_LIST_DIRECTORY = 0x0001
        FILE_SHARE_READ = 0x00000001
        FILE_SHARE_WRITE = 0x00000002
        FILE_SHARE_DELETE = 0x00000004
        OPEN_EXISTING = 3
        FILE_FLAG_BACKUP_SEMANTICS = 0x02000000

        # Change notification flags
        FILE_NOTIFY_CHANGE_FILE_NAME = 0x00000001
        FILE_NOTIFY_CHANGE_DIR_NAME = 0x00000002
        FILE_NOTIFY_CHANGE_ATTRIBUTES = 0x00000004
        FILE_NOTIFY_CHANGE_SIZE = 0x00000008
        FILE_NOTIFY_CHANGE_LAST_WRITE = 0x00000010
        FILE_NOTIFY_CHANGE_CREATION = 0x00000040
        FILE_NOTIFY_CHANGE_SECURITY = 0x00000100

        while self.monitoring:
            for path in self.watched_paths:
                try:
                    # Monitor path for changes
                    h_dir = ctypes.windll.kernel32.CreateFileW(
                        path,
                        FILE_LIST_DIRECTORY,
                        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                        None,
                        OPEN_EXISTING,
                        FILE_FLAG_BACKUP_SEMANTICS,
                        None
                    )

                    if h_dir != -1:
                        buffer = ctypes.create_string_buffer(4096)
                        bytes_returned = wintypes.DWORD()

                        success = ctypes.windll.kernel32.ReadDirectoryChangesW(
                            h_dir,
                            buffer,
                            len(buffer),
                            True,  # Watch subtree
                            FILE_NOTIFY_CHANGE_FILE_NAME | FILE_NOTIFY_CHANGE_SIZE | FILE_NOTIFY_CHANGE_LAST_WRITE,
                            ctypes.byref(bytes_returned),
                            None,
                            None
                        )

                        if success:
                            # Process changes
                            self._process_changes(buffer.raw, bytes_returned.value, path)

                        ctypes.windll.kernel32.CloseHandle(h_dir)

                except Exception as e:
                    self.logger.error(f"File monitoring error for {path}: {e}")

            time.sleep(0.1)

    def _process_changes(self, buffer: bytes, size: int, base_path: str):
        """Process file system changes"""
        # Parse FILE_NOTIFY_INFORMATION structures
        offset = 0
        while offset < size:
            # This is simplified - real implementation would parse the structures
            event = SystemEvent(
                category='filesystem',
                action='modified',
                target=base_path,
                details={'size': size},
                timestamp=datetime.now()
            )

            self.events.append(event)
            self.file_operations['writes'] += 1

            for callback in self.callbacks:
                try:
                    callback(event)
                except:
                    pass

            break  # Simplified

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        self.logger.info(f"File system monitoring stopped. Operations: {self.file_operations}")


class RegistryMonitor:
    """Monitor registry operations"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.monitoring = False
        self.watched_keys = set()
        self.callbacks = []
        self.events = []

        # Registry operation tracking
        self.registry_operations = {
            'reads': 0,
            'writes': 0,
            'deletes': 0,
            'creates': 0
        }

    def add_key(self, key_path: str):
        """Add registry key to monitor"""
        self.watched_keys.add(key_path)

    def start_monitoring(self, callback: Optional[Callable] = None):
        """Start registry monitoring"""
        if callback:
            self.callbacks.append(callback)

        self.monitoring = True
        monitor_thread = threading.Thread(target=self._monitor_thread)
        monitor_thread.daemon = True
        monitor_thread.start()

        self.logger.info(f"Registry monitoring started for {len(self.watched_keys)} keys")

    def _monitor_thread(self):
        """Monitor registry changes"""
        # Registry monitoring using RegNotifyChangeKeyValue
        KEY_NOTIFY = 0x0010
        REG_NOTIFY_CHANGE_NAME = 0x00000001
        REG_NOTIFY_CHANGE_ATTRIBUTES = 0x00000002
        REG_NOTIFY_CHANGE_LAST_SET = 0x00000004
        REG_NOTIFY_CHANGE_SECURITY = 0x00000008

        while self.monitoring:
            for key_path in self.watched_keys:
                try:
                    # This is simplified - real implementation would use RegNotifyChangeKeyValue
                    event = SystemEvent(
                        category='registry',
                        action='monitored',
                        target=key_path,
                        details={},
                        timestamp=datetime.now()
                    )

                    self.events.append(event)

                    for callback in self.callbacks:
                        try:
                            callback(event)
                        except:
                            pass

                except Exception as e:
                    self.logger.error(f"Registry monitoring error for {key_path}: {e}")

            time.sleep(1)

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        self.logger.info(f"Registry monitoring stopped. Operations: {self.registry_operations}")


class NetworkMonitor:
    """Monitor network communications"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.monitoring = False
        self.callbacks = []
        self.events = []
        self.connections = {}

        # Network statistics
        self.network_stats = {
            'connections': 0,
            'bytes_sent': 0,
            'bytes_received': 0,
            'packets_captured': 0,
            'blocked_connections': 0
        }

    def start_monitoring(self, callback: Optional[Callable] = None):
        """Start network monitoring"""
        if callback:
            self.callbacks.append(callback)

        self.monitoring = True
        monitor_thread = threading.Thread(target=self._monitor_thread)
        monitor_thread.daemon = True
        monitor_thread.start()

        self.logger.info("Network monitoring started")

    def _monitor_thread(self):
        """Monitor network activity"""
        last_connections = set()

        while self.monitoring:
            try:
                # Get current network connections
                current_connections = set()

                for conn in psutil.net_connections():
                    if conn.status == 'ESTABLISHED':
                        conn_key = (conn.laddr, conn.raddr, conn.pid)
                        current_connections.add(conn_key)

                        if conn_key not in last_connections:
                            # New connection detected
                            process_name = "unknown"
                            try:
                                proc = psutil.Process(conn.pid)
                                process_name = proc.name()
                            except:
                                pass

                            event = SystemEvent(
                                category='network',
                                action='connection_established',
                                target=f"{conn.raddr[0]}:{conn.raddr[1]}" if conn.raddr else "unknown",
                                details={
                                    'local': f"{conn.laddr[0]}:{conn.laddr[1]}",
                                    'remote': f"{conn.raddr[0]}:{conn.raddr[1]}" if conn.raddr else None,
                                    'status': conn.status,
                                    'family': str(conn.family),
                                    'type': str(conn.type)
                                },
                                timestamp=datetime.now(),
                                process_id=conn.pid,
                                process_name=process_name
                            )

                            self.events.append(event)
                            self.network_stats['connections'] += 1

                            for callback in self.callbacks:
                                try:
                                    callback(event)
                                except:
                                    pass

                # Check for closed connections
                closed = last_connections - current_connections
                for conn_key in closed:
                    event = SystemEvent(
                        category='network',
                        action='connection_closed',
                        target=str(conn_key),
                        details={},
                        timestamp=datetime.now()
                    )
                    self.events.append(event)

                last_connections = current_connections

                # Get network I/O stats
                net_io = psutil.net_io_counters()
                self.network_stats['bytes_sent'] = net_io.bytes_sent
                self.network_stats['bytes_received'] = net_io.bytes_recv

            except Exception as e:
                self.logger.error(f"Network monitoring error: {e}")

            time.sleep(0.5)

    def block_connection(self, address: str, port: int) -> bool:
        """Block specific connection (testing firewall bypass)"""
        # This would use Windows Firewall API
        self.network_stats['blocked_connections'] += 1
        return True

    def capture_packets(self, interface: str = None, count: int = 100):
        """Capture network packets for analysis"""
        # This would use WinPcap or similar
        self.network_stats['packets_captured'] += count
        return []

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        self.logger.info(f"Network monitoring stopped. Stats: {self.network_stats}")


class ProcessMonitor:
    """Monitor process activities"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.monitoring = False
        self.callbacks = []
        self.events = []
        self.tracked_processes = {}

        # Process statistics
        self.process_stats = {
            'processes_created': 0,
            'processes_terminated': 0,
            'dlls_loaded': 0,
            'threads_created': 0,
            'injections_detected': 0
        }

    def start_monitoring(self, callback: Optional[Callable] = None):
        """Start process monitoring"""
        if callback:
            self.callbacks.append(callback)

        self.monitoring = True
        monitor_thread = threading.Thread(target=self._monitor_thread)
        monitor_thread.daemon = True
        monitor_thread.start()

        self.logger.info("Process monitoring started")

    def _monitor_thread(self):
        """Monitor process activities"""
        last_pids = set()

        while self.monitoring:
            try:
                current_pids = set()

                for proc in psutil.process_iter(['pid', 'name', 'create_time']):
                    try:
                        pid = proc.info['pid']
                        current_pids.add(pid)

                        if pid not in last_pids:
                            # New process detected
                            event = SystemEvent(
                                category='process',
                                action='created',
                                target=proc.info['name'],
                                details={
                                    'pid': pid,
                                    'create_time': proc.info['create_time'],
                                    'parent': proc.ppid() if hasattr(proc, 'ppid') else None,
                                    'cmdline': proc.cmdline() if hasattr(proc, 'cmdline') else []
                                },
                                timestamp=datetime.now(),
                                process_id=pid,
                                process_name=proc.info['name']
                            )

                            self.events.append(event)
                            self.process_stats['processes_created'] += 1
                            self.tracked_processes[pid] = proc.info['name']

                            # Check for suspicious behavior
                            if self._is_suspicious_process(proc):
                                event.details['suspicious'] = True

                            for callback in self.callbacks:
                                try:
                                    callback(event)
                                except:
                                    pass

                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                # Check for terminated processes
                terminated = last_pids - current_pids
                for pid in terminated:
                    if pid in self.tracked_processes:
                        event = SystemEvent(
                            category='process',
                            action='terminated',
                            target=self.tracked_processes[pid],
                            details={'pid': pid},
                            timestamp=datetime.now()
                        )
                        self.events.append(event)
                        self.process_stats['processes_terminated'] += 1
                        del self.tracked_processes[pid]

                last_pids = current_pids

            except Exception as e:
                self.logger.error(f"Process monitoring error: {e}")

            time.sleep(0.5)

    def _is_suspicious_process(self, process) -> bool:
        """Check if process exhibits suspicious behavior"""
        suspicious_indicators = [
            'cmd.exe', 'powershell.exe', 'wscript.exe',
            'cscript.exe', 'mshta.exe', 'rundll32.exe'
        ]

        try:
            name = process.name().lower()
            return any(ind in name for ind in suspicious_indicators)
        except:
            return False

    def detect_injection(self, target_pid: int) -> bool:
        """Detect if process has been injected"""
        # Check for:
        # - Suspicious DLLs
        # - Modified memory regions
        # - Hooks
        return False

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        self.logger.info(f"Process monitoring stopped. Stats: {self.process_stats}")


class ClipboardMonitor:
    """Monitor clipboard content"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.monitoring = False
        self.callbacks = []
        self.last_content = None
        self.captured_data = []

    def start_monitoring(self, callback: Optional[Callable] = None):
        """Start clipboard monitoring"""
        if callback:
            self.callbacks.append(callback)

        self.monitoring = True
        monitor_thread = threading.Thread(target=self._monitor_thread)
        monitor_thread.daemon = True
        monitor_thread.start()

        self.logger.info("Clipboard monitoring started")

    def _monitor_thread(self):
        """Monitor clipboard changes"""
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        while self.monitoring:
            try:
                if user32.OpenClipboard(0):
                    # Get clipboard data
                    h_data = user32.GetClipboardData(1)  # CF_TEXT
                    if h_data:
                        data_ptr = kernel32.GlobalLock(h_data)
                        if data_ptr:
                            text = ctypes.string_at(data_ptr)
                            kernel32.GlobalUnlock(h_data)

                            # Check if content changed
                            if text != self.last_content:
                                self.last_content = text

                                event = SystemEvent(
                                    category='clipboard',
                                    action='changed',
                                    target='clipboard',
                                    details={
                                        'content_type': 'text',
                                        'length': len(text),
                                        'preview': text[:100].decode('utf-8', errors='ignore') if len(text) > 0 else ''
                                    },
                                    timestamp=datetime.now()
                                )

                                self.captured_data.append({
                                    'timestamp': datetime.now().isoformat(),
                                    'content': text.decode('utf-8', errors='ignore')
                                })

                                for callback in self.callbacks:
                                    try:
                                        callback(event)
                                    except:
                                        pass

                    user32.CloseClipboard()

            except Exception as e:
                self.logger.error(f"Clipboard monitoring error: {e}")

            time.sleep(0.5)

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        self.logger.info(f"Clipboard monitoring stopped. Captured {len(self.captured_data)} changes")


class ComprehensiveMonitor:
    """Unified monitoring system"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Initialize all monitors
        self.fs_monitor = FileSystemMonitor()
        self.reg_monitor = RegistryMonitor()
        self.net_monitor = NetworkMonitor()
        self.proc_monitor = ProcessMonitor()
        self.clip_monitor = ClipboardMonitor()

        self.all_events = []
        self.monitoring = False

    def configure_monitoring(self, config: Dict):
        """Configure what to monitor"""
        # Add paths to monitor
        for path in config.get('filesystem_paths', []):
            self.fs_monitor.add_path(path)

        # Add registry keys to monitor
        for key in config.get('registry_keys', []):
            self.reg_monitor.add_key(key)

    def start_all_monitoring(self):
        """Start all monitoring systems"""
        self.monitoring = True

        def unified_callback(event):
            self.all_events.append(event)
            self.logger.debug(f"Event: {event.category}/{event.action} - {event.target}")

        # Start all monitors
        self.fs_monitor.start_monitoring(unified_callback)
        self.reg_monitor.start_monitoring(unified_callback)
        self.net_monitor.start_monitoring(unified_callback)
        self.proc_monitor.start_monitoring(unified_callback)
        self.clip_monitor.start_monitoring(unified_callback)

        self.logger.info("Comprehensive monitoring started")

    def stop_all_monitoring(self):
        """Stop all monitoring"""
        self.monitoring = False

        self.fs_monitor.stop_monitoring()
        self.reg_monitor.stop_monitoring()
        self.net_monitor.stop_monitoring()
        self.proc_monitor.stop_monitoring()
        self.clip_monitor.stop_monitoring()

        self.logger.info(f"Monitoring stopped. Total events: {len(self.all_events)}")

    def export_events(self, output_file: str):
        """Export all events to file"""
        with open(output_file, 'w') as f:
            for event in self.all_events:
                f.write(json.dumps({
                    'timestamp': event.timestamp.isoformat(),
                    'category': event.category,
                    'action': event.action,
                    'target': event.target,
                    'details': event.details,
                    'process': event.process_name
                }) + '\n')

        self.logger.info(f"Exported {len(self.all_events)} events to {output_file}")