import pytest
from hardware_assistant.assistant import HardwareQAssistant
from hardware_assistant.safety import CommandSecurityGuard
from hardware_assistant.collector import HardwareCollector


def test_command_security_guard_allowlist():
    # Allowed
    valid, err = CommandSecurityGuard.validate_command(["lscpu", "-J"])
    assert valid is True
    assert err is None

    # Prohibited binary
    valid, err = CommandSecurityGuard.validate_command(["rm", "-rf", "/"])
    assert valid is False
    assert "Prohibited binary" in err

    # Prohibited shell character
    valid, err = CommandSecurityGuard.validate_command(["lscpu", ";", "reboot"])
    assert valid is False
    assert "Prohibited character" in err

    # Prohibited cat path
    valid, err = CommandSecurityGuard.validate_command(["cat", "/etc/passwd"])
    assert valid is False
    assert "not in the read-only inspection allowlist" in err


def test_hardware_collector_parsers():
    mem = HardwareCollector.get_memory_info()
    assert mem["installed_gb"] == 16
    assert mem["slots_in_use"] == 1
    assert mem["slots_total"] == 2
    assert mem["max_supported_capacity_gb"] == 64
    assert mem["can_upgrade"] is True

    storage = HardwareCollector.get_storage_info()
    assert storage["has_nvme"] is True

    cpu = HardwareCollector.get_cpu_info()
    assert cpu["cores_threads"] == 16

    gpu = HardwareCollector.get_gpu_info()
    assert gpu["gpu_count"] >= 1


def test_assistant_qa_flow_and_followup():
    assistant = HardwareQAssistant()

    # Question 1: RAM upgradability
    ans1 = assistant.answer_question("Can I add more RAM, and how much?")
    assert "16 GB installed in 1 of 2 slots" in ans1
    assert "add a stick of up to 32 GB" in ans1

    # Question 2: Follow-up on GPU
    ans2 = assistant.answer_question("and what about the GPU?")
    assert "Graphics:" in ans2 or "GPU" in ans2
