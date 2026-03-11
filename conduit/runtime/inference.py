import os
import time
from llama_cpp import LlamaTokenizer
from conduit.runtime.loader import ModelLoader
from conduit.commands.path import get_path

MAX_HISTORY = 10


class Engine:

    def __init__(self, model, cfg=None):

        model_dir = get_path()
        model_path = os.path.join(model_dir, f"{model}.gguf")

        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")

        print(f"[runtime] loading {model}")

        loader = (
            ModelLoader(model_path, model, cfg)
            if cfg
            else ModelLoader(model_path, model)
        )
        self.model = loader.run()

        self.tokenizer = LlamaTokenizer(self.model)

        start = time.time()
        print("[runtime] warming up model")

        loader.warmup(self.model)

        elapsed = time.time() - start
        print(f"[runtime] warmup completed in {elapsed:.2f}s")

        self.history = []

    def _build_prompt(self, system, user):

        prompt = f"<|system|>\n{system}\n"

        for role, msg in self.history[-MAX_HISTORY:]:
            prompt += f"<|{role}|>\n{msg}\n"

        prompt += f"<|user|>\n{user}\n<|assistant|>\n"

        return prompt

    def generate(
        self,
        prompt,
        top_k=40,
        top_p=0.9,
        temp=0.7,
        repeat_penalty=1.12,
        max_tokens=2000,
    ):
        try:

            tokens = self.tokenizer.encode(prompt)
            self.model
            self.model.eval(tokens)
            output_tokens = []

            for _ in range(max_tokens):

                token = self.model.sample(
                    top_k=top_k,
                    top_p=top_p,
                    temp=temp,
                    repeat_penalty=repeat_penalty
                )

                if token in [
                    self.model.token_eos(),
                    "<|system|>",
                    "<|user|>",
                    "<|assistant|>",
                ]:
                    break

                self.model.eval([token])

                output_tokens.append(token)

                text = self.tokenizer.decode([token])
                yield text

        except:
            return "\n Error faced on Runtime side."