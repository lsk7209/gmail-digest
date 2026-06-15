from config import FILTERS


def classify_email(email: dict) -> dict | None:
    subject = email["subject"]
    sender = email["sender"]
    body = email["body"]
    text = f"{subject} {body}".lower()

    for rule in FILTERS:
        if rule["sender_contains"].lower() not in sender.lower():
            continue

        # subject_prefix 조건이 있으면 추가 체크
        if "subject_prefix" in rule and rule["subject_prefix"] not in subject:
            continue

        for category, keywords in rule["categories"].items():
            if any(kw.lower() in text for kw in keywords):
                return {
                    **email,
                    "source": rule["name"],
                    "category": category,
                }

    return None
