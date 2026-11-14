from typing import List, Dict, Any, Optional
from hardware_assistant.collector import HardwareCollector


class HardwareQAssistant:
    """
    Context-aware Hardware Q&A assistant for Linux laptops.
    Uses strict function-calling instead of guessing or hallucinating.
    Maintains multi-turn conversational context for follow-up questions.
    """

    AVAILABLE_TOOLS = {
        "memory": HardwareCollector.get_memory_info,
        "storage": HardwareCollector.get_storage_info,
        "cpu": HardwareCollector.get_cpu_info,
        "gpu": HardwareCollector.get_gpu_info,
    }

    def __init__(self):
        self.history: List[Dict[str, str]] = []
        self.last_hardware_topic: Optional[str] = None

    def route_question_to_tools(self, user_question: str) -> List[str]:
        """
        Determines which hardware inspection tools to invoke based on user prompt
        and conversational context (resolves follow-ups like 'what about the GPU?').
        """
        q = user_question.lower()
        tools_needed = set()

        if any(w in q for w in ["ram", "memory", "slots", "stick", "upgrade memory", "dimm"]):
            tools_needed.add("memory")
            self.last_hardware_topic = "memory"

        if any(w in q for w in ["ssd", "nvme", "disk", "storage", "drive", "hard drive", "capacity"]):
            tools_needed.add("storage")
            self.last_hardware_topic = "storage"

        if any(w in q for w in ["cpu", "processor", "cores", "threads", "clock", "frequency", "cache"]):
            tools_needed.add("cpu")
            self.last_hardware_topic = "cpu"

        if any(w in q for w in ["gpu", "graphics", "video card", "nvidia", "intel iris", "radeon", "display"]):
            tools_needed.add("gpu")
            self.last_hardware_topic = "gpu"

        # Handle follow-up queries with implicit references (e.g. "and what about the GPU?")
        if not tools_needed and self.last_hardware_topic:
            if "gpu" in q or "graphics" in q:
                tools_needed.add("gpu")
                self.last_hardware_topic = "gpu"
            elif "ram" in q or "memory" in q:
                tools_needed.add("memory")
                self.last_hardware_topic = "memory"
            else:
                tools_needed.add(self.last_hardware_topic)

        return list(tools_needed)

    def answer_question(self, user_question: str) -> str:
        """
        Gathers verified system specs via tools and formulates
        a factual, hallucination-free response.
        """
        tools_to_call = self.route_question_to_tools(user_question)

        if not tools_to_call:
            return (
                "I couldn't identify the specific hardware component from your question. "
                "You can ask me about RAM/memory upgradability, SSD/NVMe storage, CPU specs, or GPU graphics cards."
            )

        tool_results: Dict[str, Any] = {}
        for tool_name in tools_to_call:
            fn = self.AVAILABLE_TOOLS.get(tool_name)
            if fn:
                tool_results[tool_name] = fn()

        # Build grounded response based on tool results
        q_lower = user_question.lower()
        response_parts = []

        if "memory" in tool_results:
            mem = tool_results["memory"]
            installed = mem["installed_gb"]
            in_use = mem["slots_in_use"]
            total_slots = mem["slots_total"]
            max_cap = mem["max_supported_capacity_gb"]
            free = mem["free_slots"]
            max_stick = mem["max_addable_per_free_slot_gb"]

            if any(term in q_lower for term in ["add", "upgrade", "more ram", "slots"]):
                if free > 0:
                    response_parts.append(
                        f"You have {installed} GB installed in {in_use} of {total_slots} slots. "
                        f"The motherboard supports up to {max_cap} GB, so you can add a stick of up to {max_stick} GB into the empty slot."
                    )
                else:
                    response_parts.append(
                        f"You have {installed} GB installed with all {total_slots} slots populated. "
                        f"To upgrade towards the board limit of {max_cap} GB, you would need to replace existing sticks."
                    )
            else:
                response_parts.append(
                    f"You have {installed} GB RAM installed across {in_use} of {total_slots} slots. "
                    f"Maximum motherboard capacity is {max_cap} GB."
                )

        if "storage" in tool_results:
            st = tool_results["storage"]
            if "nvme" in q_lower:
                if st["has_nvme"]:
                    drives = [d for d in st["drives"] if d.get("is_nvme")]
                    drive_names = ", ".join(f"{d['name']} ({d['size']}, {d['model']})" for d in drives)
                    response_parts.append(f"Yes, your primary SSD is NVMe: {drive_names}.")
                else:
                    response_parts.append("No NVMe drive was detected; your storage uses SATA or eMMC.")
            else:
                drives_summary = "; ".join(f"{d['name']} ({d['size']}, {d['transport'].upper()})" for d in st["drives"])
                response_parts.append(f"Installed storage drives: {drives_summary}.")

        if "cpu" in tool_results:
            cpu = tool_results["cpu"]
            response_parts.append(
                f"Your CPU is an {cpu['model_name']} ({cpu['architecture']}) with {cpu['cores_threads']} logical cores/threads."
            )

        if "gpu" in tool_results:
            gpu = tool_results["gpu"]
            if gpu["gpu_count"] > 0:
                gpu_str = " | ".join(gpu["gpus_found"])
                response_parts.append(f"Detected Graphics: {gpu_str}.")
            else:
                response_parts.append("No active GPU was detected in the PCI controller listing.")

        answer = " ".join(response_parts)
        self.history.append({"user": user_question, "assistant": answer})
        return answer
