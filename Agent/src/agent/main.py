
from .fetchEmails import fetch_Email_Data
from .FetchTasks import Fetch_Tasks


def main() -> None:
    """Fetch emails, extract tasks from each, and print results."""
    try:
        messages = fetch_Email_Data()
    except Exception as exc:
        print(f"Error fetching messages: {exc}")
        return

    if not messages:
        print("Data not fetched from the function!")
        return

    print(f"Fetched {len(messages)} messages\n")

    all_tasks: list[dict] = []
    for i, message in enumerate(messages, start=1):
        subject = message.get("subject", "(no subject)")
        body = message.get("body", "")
        # print("---")
        # print(f"Message {i}: {subject}")
        # print(body)

        email_text = f"Subject: {subject}\n\n{body}"
        try:
            tasks = Fetch_Tasks(email_text)
        except Exception as exc:
            print(f"  Task extraction failed: {exc}")
            continue

        if not tasks:
            print("  No tasks found.")
            continue

        print(f"  Found {len(tasks)} task(s):")
        for j, task in enumerate(tasks, start=1):
            print(f"    {j}. {task.get('title', '(untitled)')}")
            if task.get("description"):
                print(f"       {task['description']}")
            if task.get("due_date"):
                print(f"       Due: {task['due_date']}")
            if task.get("priority"):
                print(f"       Priority: {task['priority']}")
            # if task.get("confidence") is not None:
            #     print(f"       Confidence: {task['confidence']:.0%}")
            all_tasks.append(task)

    print("\n=== Summary ===")
    print(f"Total tasks extracted: {len(all_tasks)}")


if __name__ == "__main__":
    main()
