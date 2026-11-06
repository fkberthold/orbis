"""The order-status bot, with its answers recorded rather than generated.

A shop's support bot is asked where an order is, and it answers in JSON so
the shop's page can show the order. The answers below were recorded once, so
asking the same question twice gets the same string, and no run here calls a
model.

Run this file to print every recorded question with the bot's answer.
"""

# One recorded answer per question, each the raw string the bot sent back.
RECORDED = {
    "Where is order A-1042?":
        '{"order_id": "A-1042", "status": "shipped", "eta": "2026-11-12"}',
    "When will order A-1077 arrive?":
        '{"order_id": "A-1077", "status": "processing", "eta": "2026-11-19"}',
    "Has order A-1103 been delivered yet?":
        '{"order_id": "A-1103", "status": "delivered", "eta": "2026-11-03"}',
    "Where is order A-2000?":
        '{"order_id": "A-2000", "status": "not_found", "eta": null}',
}

QUESTIONS = tuple(RECORDED)


def answer(question: str) -> str:
    """The bot's answer to one question, as the JSON string it sent."""
    try:
        return RECORDED[question]
    except KeyError:
        known = "\n  ".join(QUESTIONS)
        raise KeyError(
            f"the bot has no recording for {question!r}. It was recorded on:\n  {known}"
        ) from None


if __name__ == "__main__":
    for question in QUESTIONS:
        print(question)
        print("  " + answer(question).replace("\n", "\n  "))
