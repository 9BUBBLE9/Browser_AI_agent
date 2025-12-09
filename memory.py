from typing import List, Dict


class ConversationMemory:
    def __init__(self, max_steps_in_memory: int = 10):
        self.max_steps = max_steps_in_memory
        self.steps: List[Dict] = []

    def add_step(self, observation: Dict, action: Dict, result: str):
        self.steps.append(
            {
                "observation": {
                    "url": observation.get("url"),
                    "title": observation.get("title"),
                },
                "action": action,
                "result": (result or "")[:200],
            }
        )
        if len(self.steps) > self.max_steps:
            self.steps = self.steps[-self.max_steps :]

    def as_text(self) -> str:
        if not self.steps:
            return "no previous steps yet"

        lines = []
        for i, step in enumerate(self.steps, 1):
            lines.append(
                f"Step {i}: URL={step['observation']['url']}, "
                f"Action={step['action']}, Result={step['result']}"
            )
        return "\n".join(lines)
