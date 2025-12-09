from typing import Any, Dict
from config import SECURITY_CONFIRM_WORDS
from browser_controller import BrowserController


def is_potentially_destructive(action_name: str, params: Dict[str, Any]) -> bool:
    if action_name == "finish_task":
        return False

    name = action_name.lower()
    return any(word in name for word in SECURITY_CONFIRM_WORDS)




def get_tool_schemas():
    return [
        {
            "type": "function",
            "function": {
                "name": "navigate",
                "description": "Open a URL in the browser.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "Absolute URL to open.",
                        }
                    },
                    "required": ["url"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "click_element",
                "description": "Click one of the clickable elements by index.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "index": {
                            "type": "integer",
                            "description": "Index from clickable_elements list.",
                        }
                    },
                    "required": ["index"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "type_into_selector",
                "description": "Type text into an element selected by a CSS selector.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "selector": {
                            "type": "string",
                            "description": "CSS selector of input element.",
                        },
                        "text": {
                            "type": "string",
                            "description": "Text to type.",
                        },
                        "press_enter": {
                            "type": "boolean",
                            "description": "Whether to press Enter after typing.",
                            "default": False,
                        },
                    },
                    "required": ["selector", "text"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "type_into_input_index",
                "description": (
                    "Type text into an input or textarea field chosen by its index "
                    "from input_elements."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "index": {
                            "type": "integer",
                            "description": "Index from input_elements list.",
                        },
                        "text": {
                            "type": "string",
                            "description": "Text to type into the field.",
                        },
                        "press_enter": {
                            "type": "boolean",
                            "description": "Whether to press Enter after typing.",
                            "default": False,
                        },
                    },
                    "required": ["index", "text"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "press_key",
                "description": "Press a keyboard key (e.g. Enter, Escape).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Key to press, e.g. Enter, Escape.",
                        }
                    },
                    "required": ["key"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "finish_task",
                "description": "Call this when the task is completed. Provide short report.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "What was done and current status.",
                        }
                    },
                    "required": ["summary"],
                },
            },
        },
    ]


def execute_tool(
    browser: BrowserController, tool_name: str, tool_args: Dict[str, Any]
) -> str:
    if is_potentially_destructive(tool_name, tool_args):
        answer = input(
            f"[SECURITY] Модель хочет выполнить потенциально опасное действие "
            f"{tool_name}({tool_args}). Разрешить? [y/N]: "
        ).strip().lower()
        if answer not in ("y", "yes", "д", "да"):
            return "User denied destructive action."

    try:
        if tool_name == "navigate":
            browser.goto(tool_args["url"])
            return f"Navigated to {tool_args['url']}"

        elif tool_name == "click_element":
            browser.click_by_element_index(tool_args["index"])
            return f"Clicked element with index {tool_args['index']}"

        elif tool_name == "type_into_selector":
            browser.type_text(
                tool_args["selector"],
                tool_args["text"],
                tool_args.get("press_enter", False),
            )
            return (
                f"Typed into {tool_args['selector']} text='{tool_args['text']}' "
                f"press_enter={tool_args.get('press_enter', False)}"
            )

        elif tool_name == "type_into_input_index":
            browser.type_into_input_index(
                tool_args["index"],
                tool_args["text"],
                tool_args.get("press_enter", False),
            )
            return (
                f"Typed into input index {tool_args['index']} "
                f"text='{tool_args['text']}' "
                f"press_enter={tool_args.get('press_enter', False)}"
            )

        elif tool_name == "press_key":
            browser.press_key(tool_args["key"])
            return f"Pressed key {tool_args['key']}"

        elif tool_name == "finish_task":
            return f"TASK_FINISHED: {tool_args['summary']}"

        else:
            return f"Unknown tool {tool_name}"

    except Exception as e:
        return f"ERROR executing {tool_name}: {e}"
