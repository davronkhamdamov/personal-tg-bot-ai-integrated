import subprocess
import json
import re
from datetime import datetime, timedelta


def ask_claude(prompt: str) -> str:
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def generate_plan(messages: list[dict]) -> str:
    if not messages:
        return "No discussion found. Start chatting and then run /plan."

    conversation = "\n".join(
        f"{m['username']}: {m['text']}" for m in messages
    )

    prompt = f"""Based on this group discussion, generate:
1. A concise summary of what was discussed
2. A clear action plan
3. A prioritized TODO list

Discussion:
{conversation}

Format your response clearly with sections: Summary, Action Plan, TODO List."""

    return ask_claude(prompt)


def parse_task(raw_text: str) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""Extract task details from this text and return ONLY valid JSON with no extra text.

Text: "{raw_text}"
Today's date: {today}

Return JSON with these fields:
- description: the task name/description (string)
- assignee: username if mentioned with @ or a name, otherwise null
- deadline: deadline as YYYY-MM-DD if mentioned, otherwise null

Example: {{"description": "Build search feature", "assignee": "john", "deadline": "2024-01-15"}}

JSON only, no explanation:"""

    response = ask_claude(prompt)

    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, AttributeError):
        pass

    return {"description": raw_text, "assignee": None, "deadline": None}
