"""The refund-policy bot, with its answers recorded rather than generated.

A home-goods shop's support bot answers refund questions from the shop's
written policy, which is POLICY below. The answers were recorded once, so
asking the same question twice gets the same string, and nothing here calls
a model to produce them.

Run this file to print the policy, then every recorded question with the
bot's answer.
"""

# The policy the bot was given as its context, word for word.
POLICY = """\
Larkfield Home refund policy

1. An item can be returned for a full refund within 30 days of delivery, if
   it is unused and in its original packaging.
2. The refund goes back to the original payment method, 5 to 7 business days
   after the returned item reaches our warehouse.
3. A refund request for more than $200, or for an item that arrived damaged,
   is escalated to a support specialist. The assistant does not approve or
   deny these requests itself. It tells the customer that a specialist will
   review the request within 2 business days.
4. Digital downloads can't be refunded once they have been downloaded.
"""

# One recorded answer per question, each the raw string the bot sent back.
RECORDED = {
    "I bought a desk lamp 10 days ago and never took it out of the "
    "box. Can I get my money back?":
        "Thanks for reaching out! Yes, you can. Since the lamp is unused,"
        " still in its original box, and was delivered within the last 30"
        " days, it qualifies for a full refund. Once it reaches our "
        "warehouse, the refund goes back to your original payment method "
        "within 5 to 7 business days.",
    "My blender was delivered 45 days ago and it's still sealed. Can "
    "I still return it for a refund?":
        "I'm sorry, but I can't offer a refund on the blender. Our policy"
        " allows refunds within 30 days of delivery, and it's been 45 "
        "days, so the return window has closed. Thank you for "
        "understanding, and let me know if there's anything else I can "
        "help with.",
    "My $650 sofa arrived with a torn cushion and I want a refund.":
        "I'm really sorry the sofa arrived damaged. Because it arrived "
        "damaged and the purchase is over $200, I've passed your refund "
        "request to a support specialist rather than deciding it here. A "
        "specialist will review it within 2 business days and get back to"
        " you.",
    "I bought a recipe e-book and already downloaded it, but I don't "
    "like it. Can I get a refund?":
        "Thanks for asking, and I'm sorry the e-book wasn't what you "
        "hoped for. Unfortunately, digital downloads can't be refunded "
        "once they've been downloaded, so I'm not able to refund this "
        "one.",
}

QUESTIONS = tuple(RECORDED)


def answer(question: str) -> str:
    """The bot's answer to one question, as the string it sent."""
    try:
        return RECORDED[question]
    except KeyError:
        known = "\n  ".join(QUESTIONS)
        raise KeyError(
            f"the bot has no recording for {question!r}. It was recorded on:\n  {known}"
        ) from None


if __name__ == "__main__":
    print(POLICY)
    for question in QUESTIONS:
        print(question)
        print("  " + answer(question))
        print()
