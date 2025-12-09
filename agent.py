from typing import List, Dict, Any
import json
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, MAX_STEPS
from browser_controller import BrowserController
from memory import ConversationMemory
from tools import get_tool_schemas, execute_tool
import json


class AutonomousAgent:
    def __init__(self, browser: BrowserController):
        self.browser = browser
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.memory = ConversationMemory(max_steps_in_memory=10)

    def _build_system_prompt(self) -> str:
        return (
            "You are an autonomous web-browsing assistant. "
            "Your goal is to complete the user's task in a real browser.\n"
            "You only see a compressed observation of the page: URL, title, "
            "body_text, clickable_elements and input_elements.\n\n"

            "You must choose your own actions at each step. "
            "Do NOT follow any site-specific hard-coded script or assume fixed URLs. "
            "At every step decide what to do based only on the user's goal and "
            "the current observation.\n\n"

            "Before calling finish_task, you should normally try several concrete "
            "interactions that move towards the goal: navigating to relevant pages, "
            "using search fields, or interacting with prominent clickable elements.\n\n"

            "When the user asks to order or buy something (they use verbs like "
            "'закажи', 'купи', 'оформи', 'добавь в корзину'), treat the task as an "
            "ordering flow with several abstract stages:\n"
            "- search/list stage: you see mostly a list of items or categories;\n"
            "- product stage: you see details of one main item (image, price, description);\n"
            "- cart stage: you see a list of chosen items with quantities and some total amount;\n"
            "- checkout/payment/login stage: the site clearly asks for personal, login or payment data.\n\n"

            "At each step, first decide which stage you are currently in, based only "
            "on the observation, and then choose a tool call that moves you to the "
            "next reasonable stage towards payment. For example:\n"
            "- from search/list → choose a relevant item or open its details;\n"
            "- from product → use the main prominent action near the item/price to "
            "add or advance the order, not just close the page;\n"
            "- from cart → use the main prominent action that continues the order "
            "(for example proceeding to checkout or payment);\n"
            "- from checkout/payment/login → you may stop only if further progress "
            "requires user credentials or payment details.\n\n"

            "Do NOT call finish_task while you are still at a search/list or product "
            "stage if there are visible actions that can move the order forward. "
            "Only call finish_task after you have reached a cart or checkout-like "
            "stage and either progressed to a login/payment form or clearly cannot "
            "progress further despite trying several different reasonable actions.\n\n"

            "If several tool calls in a row fail with errors (timeouts, elements not "
            "visible, overlays etc.), change your strategy (try other elements, inputs "
            "or navigation) instead of repeating the same failing action.\n\n"

            "Do not rely on specific labels, selectors or URLs. Base all decisions "
            "only on the visible texts, structure and on the observations you receive.\n"
        )
    def _make_model_call(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
    ):
        return self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
    def run(self, user_task: str):
        tools = get_tool_schemas()
        system_prompt = self._build_system_prompt()

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"User task: {user_task}\n"
                    "You will receive observations of the current page and "
                    "must use tools to achieve the goal."
                ),
            },
        ]

        for step in range(1, MAX_STEPS + 1):
            observation = self.browser.get_observation()
            memory_text = self.memory.as_text()

            obs_content = (
                f"STEP {step}.\n"
                f"Task: {user_task}\n\n"
                f"Short memory of previous steps:\n{memory_text}\n\n"
                f"Current page:\n"
                f"URL: {observation['url']}\n"
                f"Title: {observation['title']}\n"
                f"Body (truncated): {observation['body_text']}\n\n"
                f"Clickable elements (index, tag, text, href):\n"
            )

            for el in observation["clickable_elements"]:
                obs_content += (
                    f"  [{el['index']}] <{el['tag']}> "
                    f"text='{el['text']}' href={el['href']}\n"
                )

            obs_content += "\nInput elements (index, type, placeholder, label, name):\n"
            for inp in observation.get("input_elements", []):
                obs_content += (
                    f"  [{inp['index']}] type={inp['type']} "
                    f"placeholder='{inp['placeholder']}' "
                    f"label='{inp['label']}' "
                    f"name='{inp['name']}'\n"
                )

            messages.append({"role": "user", "content": obs_content})
            #print(obs_content)

            response = self._make_model_call(messages, tools)
            msg = response.choices[0].message

            assistant_message: Dict[str, Any] = {
                "role": "assistant",
                "content": msg.content or "",
            }

            if msg.tool_calls:
                assistant_message["tool_calls"] = []
                for tc in msg.tool_calls:
                    assistant_message["tool_calls"].append(
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                    )

            messages.append(assistant_message)

            if not msg.tool_calls:
                if msg.content:
                    print(f"[MODEL] {msg.content}")
                continue

            tool_call = msg.tool_calls[0]
            tool_name = tool_call.function.name
            args_dict: Dict[str, Any] = json.loads(tool_call.function.arguments or "{}")

            print(f"[AGENT] Calling tool {tool_name} with args {args_dict}")
            result_text = execute_tool(self.browser, tool_name, args_dict)
            print(f"[TOOL RESULT] {result_text}")

            self.memory.add_step(
                observation=observation,
                action={"tool": tool_name, "args": args_dict},
                result=result_text,
            )

            messages.append(
                {
                    "role": "tool",
                    "name": tool_name,
                    "tool_call_id": tool_call.id,
                    "content": result_text,
                }
            )

            if result_text.startswith("TASK_FINISHED:"):
                print("\n[AGENT] Task finished.")
                print(result_text)
                return

        print("\n[AGENT] Reached max steps without explicitly finishing the task.")
