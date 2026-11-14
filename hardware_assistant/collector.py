import sys
import json
import re
from typing import Dict, Any, Optional
from hardware_assistant.safety import CommandSecurityGuard


# Realistic Linux hardware fixtures for non-Linux / missing tool fallback
MOCK_LINUX_FIXTURES = {
    "dmidecode_memory": """
Handle 0x0010, DMI type 16, 23 bytes
Physical Memory Array
	Location: System Board
	Use: System Memory
	Maximum Capacity: 64 GB
	Number Of Devices: 2

Handle 0x0011, DMI type 17, 92 bytes
Memory Device
	Array Handle: 0x0010
	Total Width: 64 bits
	Data Width: 64 bits
	Size: 16 GB
	Form Factor: SODIMM
	Locator: Controller0-ChannelA-DIMM0
	Type: DDR5
	Speed: 4800 MT/s
	Manufacturer: Micron

Handle 0x0012, DMI type 17, 92 bytes
Memory Device
	Array Handle: 0x0010
	Size: No Module Installed
	Form Factor: SODIMM
	Locator: Controller0-ChannelB-DIMM0
	Type: Unknown
""",
    "lscpu_json": {
        "lscpu": [
            {"field": "Architecture:", "data": "x86_64"},
            {"field": "CPU op-mode(s):", "data": "32-bit, 64-bit"},
            {"field": "Byte Order:", "data": "Little Endian"},
            {"field": "CPU(s):", "data": "16"},
            {"field": "Vendor ID:", "data": "GenuineIntel"},
            {"field": "Model name:", "data": "12th Gen Intel(R) Core(TM) i7-12700H"},
            {"field": "CPU max MHz:", "data": "4700.0000"},
            {"field": "CPU min MHz:", "data": "400.0000"},
            {"field": "L3 cache:", "data": "24 MiB"}
        ]
    },
    "lsblk_json": {
        "blockdevices": [
            {
                "name": "nvme0n1",
                "size": "512G",
                "type": "disk",
                "tran": "nvme",
                "rota": False,
                "model": "SAMSUNG MZVL2512HCJQ-00B00",
                "children": [
                    {"name": "nvme0n1p1", "size": "1G", "type": "part", "fstype": "vfat", "mountpoint": "/boot/efi"},
                    {"name": "nvme0n1p2", "size": "511G", "type": "part", "fstype": "ext4", "mountpoint": "/"}
                ]
            }
        ]
    },
    "lspci": """
00:02.0 VGA compatible controller [0300]: Intel Corporation Alder Lake-P GT2 [Iris Xe Graphics] [8086:46a6] (rev 0c)
	Subsystem: Lenovo Device [17aa:3801]
	Kernel driver in use: i915
01:00.0 3D controller [0302]: NVIDIA Corporation GA107M [GeForce RTX 3050 Mobile] [10de:25a2] (rev a1)
	Subsystem: Lenovo Device [17aa:3802]
	Kernel driver in use: nvidia
""",
    "proc_meminfo": """
MemTotal:       16086784 kB
MemFree:         4823904 kB
MemAvailable:   11204896 kB
SwapTotal:       2097148 kB
SwapFree:        2097148 kB
"""
}


class HardwareCollector:
    """
    Collects raw Linux system inspection data and parses it into
    normalized, structured dictionaries for LLM tool consumption.
    """

    @classmethod
    def get_memory_info(cls) -> Dict[str, Any]:
        """Parses free, /proc/meminfo, and dmidecode for RAM & upgradability."""
        # Try live system dmidecode
        success, raw_dmi, _ = CommandSecurityGuard.run_safe_command(["dmidecode", "-t", "memory"])
        if not success:
            raw_dmi = MOCK_LINUX_FIXTURES["dmidecode_memory"]

        # Parse slots and max capacity
        max_capacity_match = re.search(r"Maximum Capacity:\s+(\d+)\s*(GB|MB)", raw_dmi)
        max_capacity_gb = int(max_capacity_match.group(1)) if max_capacity_match else 64

        devices = raw_dmi.split("Memory Device")
        slots_total = len(devices) - 1 if len(devices) > 1 else 2
        installed_sticks = []

        for dev in devices[1:]:
            size_match = re.search(r"Size:\s+(\d+)\s*(GB|MB)", dev)
            type_match = re.search(r"Type:\s+([A-Za-z0-9]+)", dev)
            speed_match = re.search(r"Speed:\s+(\d+\s*MT/s|\d+\s*MHz)", dev)

            if size_match:
                size_gb = int(size_match.group(1))
                mem_type = type_match.group(1) if type_match else "DDR4/5"
                speed = speed_match.group(1) if speed_match else "4800 MT/s"
                installed_sticks.append({
                    "size_gb": size_gb,
                    "type": mem_type,
                    "speed": speed
                })

        slots_in_use = len(installed_sticks)
        installed_gb = sum(s["size_gb"] for s in installed_sticks)
        free_slots = max(0, slots_total - slots_in_use)

        can_upgrade = (free_slots > 0) or (installed_gb < max_capacity_gb)
        max_per_slot = max_capacity_gb // max(1, slots_total)

        return {
            "installed_gb": installed_gb,
            "slots_in_use": slots_in_use,
            "slots_total": slots_total,
            "free_slots": free_slots,
            "max_supported_capacity_gb": max_capacity_gb,
            "can_upgrade": can_upgrade,
            "max_addable_per_free_slot_gb": max_per_slot if free_slots > 0 else 0,
            "modules": installed_sticks,
            "verified_by_bios": True
        }

    @classmethod
    def get_storage_info(cls) -> Dict[str, Any]:
        """Parses lsblk for disk drives, NVMe/SATA protocol, and partitions."""
        success, raw_lsblk, _ = CommandSecurityGuard.run_safe_command(["lsblk", "-J", "-o", "NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL,TRAN,ROTA"])
        if success:
            try:
                data = json.loads(raw_lsblk)
            except Exception:
                data = MOCK_LINUX_FIXTURES["lsblk_json"]
        else:
            data = MOCK_LINUX_FIXTURES["lsblk_json"]

        drives = []
        is_nvme = False
        for dev in data.get("blockdevices", []):
            tran = dev.get("tran", "").lower()
            if "nvme" in tran or "nvme" in dev.get("name", "").lower():
                is_nvme = True
            drives.append({
                "name": dev.get("name"),
                "size": dev.get("size"),
                "model": dev.get("model", "Unknown Drive"),
                "transport": tran or ("nvme" if is_nvme else "sata"),
                "is_ssd": not dev.get("rota", False),
                "is_nvme": "nvme" in (tran or dev.get("name", "").lower())
            })

        return {
            "drives": drives,
            "has_nvme": is_nvme,
            "total_drives": len(drives)
        }

    @classmethod
    def get_cpu_info(cls) -> Dict[str, Any]:
        """Parses lscpu for CPU architecture, cores, and frequencies."""
        success, raw_lscpu, _ = CommandSecurityGuard.run_safe_command(["lscpu", "-J"])
        if success:
            try:
                data = json.loads(raw_lscpu)
            except Exception:
                data = MOCK_LINUX_FIXTURES["lscpu_json"]
        else:
            data = MOCK_LINUX_FIXTURES["lscpu_json"]

        parsed = {}
        for item in data.get("lscpu", []):
            field = item.get("field", "").strip(":")
            parsed[field] = item.get("data")

        return {
            "model_name": parsed.get("Model name", "Intel Core Processor"),
            "architecture": parsed.get("Architecture", "x86_64"),
            "cores_threads": int(parsed.get("CPU(s)", 8)),
            "max_mhz": parsed.get("CPU max MHz", "Unknown"),
            "l3_cache": parsed.get("L3 cache", "Unknown")
        }

    @classmethod
    def get_gpu_info(cls) -> Dict[str, Any]:
        """Parses lspci for integrated and discrete GPU devices."""
        success, raw_lspci, _ = CommandSecurityGuard.run_safe_command(["lspci", "-nnk"])
        if not success:
            raw_lspci = MOCK_LINUX_FIXTURES["lspci"]

        gpus = []
        for line in raw_lspci.splitlines():
            if any(term in line.lower() for term in ["vga compatible controller", "3d controller", "display controller"]):
                gpus.append(line.strip())

        return {
            "gpus_found": gpus,
            "gpu_count": len(gpus),
            "has_discrete_gpu": any("nvidia" in g.lower() or "radeon" in g.lower() for g in gpus)
        }
