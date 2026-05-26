# encoding=utf-8
"""
requires openai == 1.25.0
"""
import os
import re
from datetime import datetime

from litellm import completion
from retry import retry

wrapper = None


class DebugLogger:
    def __init__(self, enabled=False, api_key=None):
        self.enabled = enabled
        self._api_key = api_key
        self.log_file = None
        self._label = None
        if enabled:
            try:
                import colorama
                colorama.init()
            except ImportError:
                pass
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            log_path = os.path.join(os.getcwd(), "logs", f"gen_linter_debug_{timestamp}.log")
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            self.log_file = open(log_path, "w", encoding="utf-8")
            self._file(f"Debug log started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def _mask_key(self, text):
        if not self._api_key:
            return text
        return text.replace(self._api_key, "***API_KEY***")

    def _file(self, msg):
        if self.log_file:
            self.log_file.write(msg + "\n")
            self.log_file.flush()

    def separator(self, char="=", length=60):
        if not self.enabled:
            return
        line = char * length
        self._file(line)
        try:
            import colorama
            print(colorama.Style.DIM + line + colorama.Style.RESET_ALL)
        except ImportError:
            pass

    def step(self, title):
        if not self.enabled:
            return
        msg = f">>>>> {title}"
        self._file(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")
        try:
            import colorama
            print(colorama.Fore.YELLOW + colorama.Style.BRIGHT + msg + colorama.Style.RESET_ALL)
        except ImportError:
            print(msg)

    def sub_step(self, label):
        if not self.enabled:
            return
        self._label = label

    def prompt(self, model, messages):
        if not self.enabled:
            return
        full = self._messages_to_text(messages)
        masked = self._mask_key(full)
        tag = f"PROMPT [{self._label}]" if self._label else "PROMPT"
        self._file(f"{tag} (model: {model}):\n{masked}")
        try:
            import colorama
            preview = masked[:200]
            if len(masked) > 200:
                preview += "\n...(truncated, see log file for full content)"
            print(colorama.Fore.CYAN + colorama.Style.BRIGHT + f"──── {tag} ────" + colorama.Style.RESET_ALL)
            print(colorama.Fore.CYAN + preview + colorama.Style.RESET_ALL)
            print(colorama.Fore.CYAN + "──────────────" + colorama.Style.RESET_ALL)
        except ImportError:
            pass

    def response(self, model, text):
        if not self.enabled:
            return
        masked = self._mask_key(text)
        tag = f"RESPONSE [{self._label}]" if self._label else "RESPONSE"
        self._file(f"{tag} (model: {model}):\n{masked}")
        try:
            import colorama
            preview = masked[:500]
            if len(masked) > 500:
                preview += "\n...(truncated, see log file for full content)"
            print(colorama.Fore.GREEN + colorama.Style.BRIGHT + f"──── {tag} ────" + colorama.Style.RESET_ALL)
            print(colorama.Fore.GREEN + preview + colorama.Style.RESET_ALL)
            print(colorama.Fore.GREEN + "────────────────" + colorama.Style.RESET_ALL)
        except ImportError:
            pass

    def _messages_to_text(self, messages):
        parts = []
        for m in messages:
            role = m.get("role", "unknown")
            content = m.get("content", "")
            parts.append(f"<{role}>\n{content}\n</{role}>")
        return "\n".join(parts)

    def close(self):
        if self.log_file:
            self._file(f"Debug log ended at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.log_file.close()
            self.log_file = None


class GPTAgent:
    def __init__(self, api_key=None, debug=False) -> None:
        self._api_key = api_key
        self.debugger = DebugLogger(enabled=debug, api_key=api_key)

    @retry(delay=0, tries=6, backoff=1, max_delay=120)
    def ask(self, content, examples=None, model="deepseek/deepseek-v4-flash", temperature=0, previous_msg=[]):
        messages = []
        if isinstance(previous_msg, list):
            for i, each_prompt in enumerate(previous_msg):
                role = "user" if i % 2 else "assistant"
                messages.append({"role": role, "content": each_prompt})

        if examples:
            for user_prompt, response in examples:
                messages.extend([
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": str(response)}])

        messages.append({"role": "user", "content": content})

        self.debugger.separator()
        self.debugger.prompt(model, messages)

        try:
            kwargs = {"model": model, "messages": messages, "temperature": temperature, "timeout": 120}
            if self._api_key:
                kwargs["api_key"] = self._api_key
            response = completion(**kwargs)
        except Exception as e:
            print(f"Error calling model {model} : {e}")
            raise e

        answer = response.choices[0].message.content
        self.debugger.response(model, answer)
        return answer

    def get_response(self, prompt, examples=None, model="deepseek/deepseek-v4-flash", temperature=0, previous_msg=[]):
        answer = self.ask(prompt, examples, model, temperature, previous_msg)
        return answer

