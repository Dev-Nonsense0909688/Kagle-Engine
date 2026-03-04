from llama_cpp import Llama
import psutil
import subprocess
import os
import platform
import re
import time
import json


os.environ["LLAMA_CPP_LOG_LEVEL"] = "ERROR"


def get_ram_type():
    try:
        output = subprocess.check_output(
            [
                "powershell",
                "-Command",
                "Get-CimInstance Win32_PhysicalMemory | Select-Object SMBIOSMemoryType",
            ],
            text=True,
        )
        match = re.search(r"\d+", output)
        if not match:
            return "unknown"
        code = int(match.group())
        return {20: "DDR", 21: "DDR2", 24: "DDR3", 26: "DDR4", 34: "DDR5"}.get(
            code, "unknown"
        )
    except:
        return "unknown"


class ModelLoader:
    def __init__(self, model_file: str):
        if not os.path.exists(model_file):
            raise FileNotFoundError("Model file not found.")

        self.model_file = model_file
        self.model_size = os.path.getsize(model_file) / (1024**3)
        self.total_ram = psutil.virtual_memory().total / (1024**3)
        self.physical = psutil.cpu_count(logical=False) or 1
        self.logical = psutil.cpu_count(logical=True) or self.physical
        self.system = platform.system()
        self.cpu_name = self._get_cpu_name()
        self.ram_type = get_ram_type()

        self._llm = None
        self.profile_path = "profiles/lowram_profile.json"
        self.profile = self._load_profile()

    def _get_cpu_name(self):
        try:
            if self.system == "Windows":
                output = subprocess.check_output(
                    ["wmic", "cpu", "get", "name"], text=True
                )
                lines = [
                    l.strip()
                    for l in output.splitlines()
                    if l.strip() and "Name" not in l
                ]
                return lines[0] if lines else "unknown"
            return platform.processor()
        except:
            return "unknown"

    def _load_profile(self):
        if os.path.exists(self.profile_path):
            try:
                with open(self.profile_path, "r") as f:
                    data = json.load(f)
                if "threads" in data and "ctx" in data:
                    return data
            except:
                pass
        return {}

    def _save_profile(self, threads, ctx):
        with open(self.profile_path, "w") as f:
            json.dump({"threads": threads, "ctx": ctx}, f)
        self.profile = {"threads": threads, "ctx": ctx}

    def _memory_pressure(self):
        return psutil.virtual_memory().percent > 88

    def select_ctx(self):
        usable = max(0.5, self.total_ram - 1.8)
        kv_available = max(0.2, usable - self.model_size)
        per_1k = 0.5 if self.model_size >= 2 else 0.35
        ctx = int((kv_available / per_1k) * 1000)
        ctx = max(1024, min(ctx, 4096))
        if self._memory_pressure():
            ctx = max(1024, int(ctx * 0.7))
        return ctx

    def _benchmark_threads(self, ctx):
        best_t = 1
        best_speed = 0

        for t in range(1, self.physical + 1):
            try:
                llm = Llama(
                    model_path=self.model_file,
                    n_threads=t,
                    n_ctx=ctx,
                    verbose=False,
                )
                start = time.time()
                result = llm("Hello", max_tokens=64)
                elapsed = time.time() - start
                tokens = result["usage"]["completion_tokens"]
                speed = tokens / elapsed if elapsed > 0 else 0
                if speed > best_speed:
                    best_speed = speed
                    best_t = t
                del llm
            except:
                continue

        return best_t

    def select_threads(self, ctx):
        if self.profile:
            return self.profile["threads"]

        if "Pentium" in self.cpu_name:
            return self.physical

        return self._benchmark_threads(ctx)

    def run(self):
        if self._llm:
            return self._llm

        ctx = self.select_ctx()
        threads = self.select_threads(ctx)

        while ctx >= 1024:
            try:
                self._llm = Llama(
                    model_path=self.model_file,
                    n_threads=threads,
                    n_ctx=ctx,
                    verbose=False,
                    logits_all=False,
                )
                break
            except:
                ctx = int(ctx * 0.75)

        if not self.profile:
            self._save_profile(threads, ctx)

        self._llm("Warmup", max_tokens=16)

        return self._llm

    def stop(self):
        if self._llm:
            del self._llm
            self._llm = None


if __name__ == "__main__":
    loader = ModelLoader("qwen.gguf")
    print("Booting LowRAM Engine...")
    llm = loader.run()
