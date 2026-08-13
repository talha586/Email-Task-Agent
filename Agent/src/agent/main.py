
from .fetchEmails import fetch_Email_Data

def main() -> None:
    """Entry point for the agent package.

    Calls `fetch_Email_Data()` and prints the fetched messages (subject + body)
    if any are returned. Keeps behavior minimal to stay compatible with current
    code logic.
    """
    try:
        messages = fetch_Email_Data()
    except Exception as exc:
        print(f"Error fetching messages: {exc}")
        return

    if not messages:
        print("Data not fetched from the function!")
        return

    print(f"Fetched {len(messages)} messages")
    for i, m in enumerate(messages, start=1):
        print("---")
        print(f"Message {i}: {m.get('subject', '(no subject)')}")
        body = m.get("body", "")
        print(body)


if __name__ ==  "__main__":
    main()


