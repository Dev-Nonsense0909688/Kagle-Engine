import os
import re
import sys
import time
import psutil
import threading
from datetime import datetime
from colorama import init, Fore, Style
from brain import KagleAIBrain

init(autoreset=True)


class KagleAICLI:

    def __init__(self, model_path="qwen.gguf"):
        self.brain = KagleAIBrain(model_path)
        self.running = True

        self.commands = {
            "/help": self.cmd_help,
            "/exit": self.cmd_exit,
            "/analyze": self.cmd_analyze,
            "/read": self.cmd_read,
            "/scan": self.cmd_scan,
            "/stats": self.cmd_stats,
            "/clear": self.cmd_clear,
            "/reload": self.cmd_reload,
            "/context": self.cmd_context,
            "/write": self.cmd_write,
        }

    # ---------------- UI ---------------- #

    def header(self):
        print(
            Fore.CYAN + Style.BRIGHT + "\n╔══════════════════════════════╗\n"
            "║        KAGLE AI ENGINE       ║\n"
            "╚══════════════════════════════╝\n"
        )

    def success(self, text):
        print(Fore.GREEN + "✔ " + text)

    def error(self, text):
        print(Fore.RED + "✖ " + text)

    def info(self, text):
        print(Fore.YELLOW + text)

    # ------------- Streaming Helper ------------- #

    def stream_model(self, sys_prompt, user_prompt, tokens=512):

        output = ""

        for token in self.brain.generate(sys_prompt, user_prompt, tokens=tokens):
            sys.stdout.write(token)
            sys.stdout.flush()
            output += token

        print()
        return output.strip()

    # ---------------- Commands ---------------- #

    def cmd_help(self, args=None):
        print(
            Fore.MAGENTA
            + Style.BRIGHT
            + """
Available Commands:
/help               Show this help
/exit               Exit engine
/analyze <file>     Analyze file architecture
/read <file>        Summarize file
/scan               Scan directory tree
/stats              Show system stats
/clear              Clear chat history
/context <n>        Set context memory
/reload             Reload model
/write              Generate file with AI
"""
        )

    def cmd_exit(self, args=None):
        self.success("Shutting down engine...")
        self.running = False

    def cmd_write(self, args=None):

        self.info("Describe the file you want to create.")
        prompt = input(Fore.GREEN + "File request > ")

        if not prompt:
            self.error("No request provided.")
            return

        sys_prompt = open("prompts/write.txt").read()

        print(Fore.MAGENTA + "\nAI:", end="")

        response = self.stream_model(sys_prompt, prompt, tokens=1024)

        pattern = re.compile(
            r"<WRITE_FILE>\s*(.*?)\s*CODE:\s*(.*?)\s*</WRITE_FILE>", re.DOTALL
        )

        match = pattern.search(response)

        if not match:
            self.error("AI did not return a valid WRITE_FILE block.")
            return

        filename = match.group(1).strip()
        code = match.group(2)

        try:
            if "/" in filename:
                os.makedirs(os.path.dirname(filename), exist_ok=True)

            with open(filename, "w", encoding="utf-8") as f:
                f.write(code)

            self.success(f"File written: {filename}")

        except Exception as e:
            self.error(f"Failed to write file: {e}")

    # -------- File Analysis -------- #

    def cmd_analyze(self, args):

        if not args:
            self.error("Usage: /analyze <file>")
            return

        file = args.strip()

        if not os.path.exists(file):
            self.error("File not found.")
            return

        content = open(file, "r", encoding="utf-8", errors="ignore").read()
        sys_prompt = open("prompts/analyze.txt").read()

        self.info("Analyzing file architecture...\n")

        self.stream_model(sys_prompt, content, tokens=512)

    # -------- File Summary -------- #

    def cmd_read(self, args):

        if not args:
            self.error("Usage: /read <file>")
            return

        file = args.strip()

        if not os.path.exists(file):
            self.error("File not found.")
            return

        content = open(file, "r", encoding="utf-8", errors="ignore").read()
        sys_prompt = open("prompts/summerize.txt").read()

        self.info("Summarizing file...\n")

        self.stream_model(sys_prompt, content, tokens=256)

    # -------- Directory Scan -------- #

    def cmd_scan(self, args=None):

        self.info("Scanning directory...\n")

        for root, _, files in os.walk("."):
            for f in files:
                print(Fore.CYAN + os.path.join(root, f))

    # -------- System Stats -------- #

    def cmd_stats(self, args=None):

        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.5)

        print(Fore.BLUE + Style.BRIGHT + "\nSystem Stats:")
        print(Fore.GREEN + f"RAM Usage : {mem.percent}%")
        print(Fore.YELLOW + f"CPU Usage : {cpu}%")
        print(Fore.CYAN + f"Time      : {datetime.now().strftime('%H:%M:%S')}")

    # -------- Memory -------- #

    def cmd_clear(self, args=None):
        self.brain.clear_memory()
        self.success("Memory cleared.")

    def cmd_reload(self, args=None):
        self.info("Reloading model...")
        self.brain.reload()
        self.success("Model reloaded.")

    def cmd_context(self, args):

        if not args or not args.isdigit():
            self.error("Usage: /context <number>")
            return

        self.brain.set_context(int(args))
        self.success(f"Context set to {args}")

    # ---------------- Main Loop ---------------- #

    def loop(self):

        self.header()
        self.info("Kagle AI Ready. Type /help\n")

        while self.running:

            user_input = input(
                Fore.GREEN + Style.BRIGHT + "> " + Style.RESET_ALL
            ).strip()

            if not user_input:
                continue

            if user_input.startswith("/"):

                parts = user_input.split(" ", 1)
                cmd = parts[0].lower()
                args = parts[1] if len(parts) > 1 else None

                if cmd in self.commands:
                    self.commands[cmd](args)
                else:
                    self.error("Unknown command.")

            elif user_input == "clear":

                os.system("cls" if os.name == "nt" else "clear")
                self.header()
                self.info("Kagle AI Ready. Type /help\n")

            else:

                sys_prompt = open("prompts/chat.txt").read()

                print(Fore.MAGENTA + "\nAI:", end="")

                self.stream_model(sys_prompt, user_input, tokens=1024)

        self.brain.stop()
        self.success("Engine stopped.")
