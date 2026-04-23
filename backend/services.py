import os
import re
from typing import Optional

from dotenv import load_dotenv
from openai import APIConnectionError, OpenAI

load_dotenv()

BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
MODEL = os.getenv("OPENAI_MODEL", "llama3.2:3b")
API_KEY = os.getenv("OPENAI_API_KEY", "ollama")

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


def _build_prompt(data, sender_name: str, company: Optional[str], role: Optional[str]) -> str:
    sender_line = sender_name or "[Your Name]"
    if role and company:
        sender_context = f"{sender_line}, {role} at {company}"
    elif company:
        sender_context = f"{sender_line} from {company}"
    elif role:
        sender_context = f"{sender_line}, {role}"
    else:
        sender_context = sender_line

    return f"""
    Generate a professional sales email.

    Product: {data.product}
    Audience: {data.audience}
    Tone: {data.tone}
    Length: {data.length}
    Sender: {sender_context}

    Sign the email off using the sender's name above. Do not use placeholders
    like "[Your Name]" — use the real sender name provided.

    Format:
    Subject:
    Email:
    CTA:
    """


def _call_llm(prompt: str):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return {"result": response.choices[0].message.content}

    except APIConnectionError:
        return {
            "error": (
                f"Could not reach model backend at {BASE_URL}. "
                "If using Ollama, make sure it is installed and running "
                "(open the Ollama app, or run `ollama serve`), and that the "
                f"model '{MODEL}' has been pulled with `ollama pull {MODEL}`."
            )
        }
    except Exception as e:
        return {"error": str(e)}


def generate_email_content(
    data,
    sender_name: str = "",
    company: Optional[str] = None,
    role: Optional[str] = None,
):
    return _call_llm(_build_prompt(data, sender_name, company, role))


def _parse_subject_lines(raw: str, want: int = 5) -> list[str]:
    subjects: list[str] = []
    line_re = re.compile(r"^\s*(?:\d+[\.\)]|[-*•])\s*(.+?)\s*$")
    for line in raw.splitlines():
        m = line_re.match(line)
        if not m:
            continue
        text = m.group(1).strip()
        text = re.sub(r"^(subject\s*\d*\s*:\s*)", "", text, flags=re.IGNORECASE)
        text = text.strip().strip('"').strip("'").strip("*").strip()
        if text:
            subjects.append(text)
    seen, deduped = set(), []
    for s in subjects:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(s)
    return deduped[:want]


def improve_email_content(
    draft: str,
    tone: Optional[str] = None,
    sender_name: str = "",
    company: Optional[str] = None,
    role: Optional[str] = None,
) -> dict:
    sender_bits = [b for b in [sender_name, role, company] if b]
    sender_line = ", ".join(sender_bits) if sender_bits else "(unspecified sender)"
    tone_line = f"\n    - Target tone: {tone}" if tone else ""

    prompt = f"""
    You are an expert sales-email editor. Rewrite the draft below to be clearer,
    more concise, and more likely to get a reply.

    DRAFT:
    \"\"\"
    {draft}
    \"\"\"

    Guidelines:
    - Keep the sender's core intent and facts intact.
    - Tighten language: cut fluff, strengthen verbs, shorten sentences.
    - Ensure a clear subject, body, and call-to-action.
    - Sign off with the sender's real name: {sender_line}. Never use "[Your Name]".{tone_line}

    Output ONLY the polished email in this exact format:

    Subject:
    Email:
    CTA:
    """
    return _call_llm(prompt)


def generate_subject_lines(
    data,
    sender_name: str = "",
    company: Optional[str] = None,
    role: Optional[str] = None,
) -> dict:
    sender_bits = [b for b in [sender_name, role, company] if b]
    sender_line = ", ".join(sender_bits) if sender_bits else "(unspecified sender)"

    prompt = f"""
    Generate EXACTLY 5 different sales-email subject lines.

    Product: {data.product}
    Audience: {data.audience}
    Tone: {data.tone}
    Sender: {sender_line}

    Requirements:
    - Each subject line should use a DIFFERENT angle:
      1. Direct benefit / value
      2. Curiosity / question hook
      3. Specific / data-driven
      4. Pain point or friction
      5. Low-friction meeting / casual
    - Under 60 characters each.
    - No emojis. No ALL CAPS. No clickbait.
    - Output ONLY the 5 subject lines, one per line, numbered "1." through "5.".
    - No preamble, no explanations, no quotes around the subjects.
    """

    result = _call_llm(prompt)
    if "error" in result:
        return result

    subjects = _parse_subject_lines(result["result"], want=5)
    if not subjects:
        return {"error": "Could not parse subject lines from the model's response."}
    return {"subjects": subjects}


def generate_followup_content(
    original,
    days_since_sent: int,
    note: Optional[str],
    sender_name: str = "",
    company: Optional[str] = None,
    role: Optional[str] = None,
):
    sender_line = sender_name or "[Your Name]"
    if role and company:
        sender_context = f"{sender_line}, {role} at {company}"
    elif company:
        sender_context = f"{sender_line} from {company}"
    elif role:
        sender_context = f"{sender_line}, {role}"
    else:
        sender_context = sender_line

    extra = f"\n    Additional context from sender: {note}" if note else ""

    prompt = f"""
    You previously wrote the sales email below. No reply was received after
    {days_since_sent} day(s). Write a polite, concise follow-up email.

    ORIGINAL EMAIL:
    \"\"\"
    {original.result}
    \"\"\"

    Context:
    - Product: {original.product}
    - Audience: {original.audience}
    - Tone: {original.tone}
    - Sender: {sender_context}{extra}

    Guidelines:
    - Keep the follow-up noticeably SHORTER than the original (2-3 short
      paragraphs max).
    - Briefly reference the original without repeating it.
    - Add a single, clear, low-friction call-to-action (e.g. "15-min call",
      "reply with yes/no", "share the right person").
    - Sign off with the sender's real name above — never "[Your Name]".

    Format:
    Subject:
    Email:
    CTA:
    """
    return _call_llm(prompt)
