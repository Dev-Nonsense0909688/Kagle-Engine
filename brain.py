import sys
from model_loader import ModelLoader


class KagleAIBrain:
    def __init__(self, model_path="qwen.gguf"):
        self.model_path = model_path
        self.loader = ModelLoader(model_path)
        self.llm = self.loader.run()

        self.chat_history = []
        self.context_window = 5


    def generate(self, system_prompt, user_input, tokens=256, grammar=None):
        prompt = f"{system_prompt}\nUser: {user_input}\nAssistant:"

        stream = self.llm(prompt, max_tokens=tokens, stream=True, grammar=grammar)

        full_output = ""

        for chunk in stream:
            text = chunk["choices"][0]["text"]
            full_output += text
            yield text

        self.chat_history.append(("User", user_input))
        self.chat_history.append(("Assistant", full_output.strip()))

    def clear_memory(self):
        self.chat_history.clear()

    def set_context(self, n):
        self.context_window = max(1, n)

    def reload(self):
        self.loader.stop()
        self.loader = ModelLoader(self.model_path)
        self.llm = self.loader.run()

    def stop(self):
        self.loader.stop()
