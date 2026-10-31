from playwright.sync_api import Page, expect


def open_desk(page: Page) -> None:
    page.goto("/")
    expect(page.locator("#heading")).to_have_text("Northgate Label Desk")


def fill_label(page: Page, recipient, postcode, weight, service) -> None:
    page.fill("#recipient", recipient)
    page.fill("#postcode", postcode)
    page.fill("#weight", weight)
    page.select_option("#service", service)


def wait_for_answer(page: Page) -> None:
    # A refusal and a print both land after the check, so "nothing printed"
    # only means something once "Checking..." has come and gone.
    expect(page.locator("#status")).to_have_text("Checking...")
    expect(page.locator("#status")).to_have_text("")


def test_valid_label_prints(page: Page) -> None:
    open_desk(page)
    fill_label(page, "Ada Lovelace", "02139", "2.5", "Standard")
    page.click("#print")
    wait_for_answer(page)

    expect(page.locator("li.label")).to_have_text(
        ["Ada Lovelace, 02139, 2.5 kg, Standard"]
    )
    expect(page.locator("#recipient")).to_have_value("")
    expect(page.locator("#postcode")).to_have_value("")
    expect(page.locator("#weight")).to_have_value("")


def test_bad_fields_are_reported_together(page: Page) -> None:
    open_desk(page)
    fill_label(page, "   ", "021390", "0", "Standard")
    page.click("#print")
    wait_for_answer(page)

    expect(page.locator("#recipient-error")).to_have_text("Enter a recipient.")
    expect(page.locator("#postcode-error")).to_have_text(
        "Postcode must be five digits."
    )
    expect(page.locator("#weight-error")).to_have_text(
        "Weight must be over 0 and at most 30 kg."
    )
    expect(page.locator("li.label")).to_have_count(0)


def test_weight_tops_out_at_thirty(page: Page) -> None:
    open_desk(page)
    fill_label(page, "Ada Lovelace", "02139", "30", "Standard")
    page.click("#print")
    wait_for_answer(page)
    expect(page.locator("li.label")).to_have_count(1)

    fill_label(page, "Ada Lovelace", "02139", "30.5", "Standard")
    page.click("#print")
    wait_for_answer(page)
    expect(page.locator("#weight-error")).to_have_text(
        "Weight must be over 0 and at most 30 kg."
    )
    expect(page.locator("li.label")).to_have_count(1)


def test_express_takes_five_kg_or_less(page: Page) -> None:
    open_desk(page)
    fill_label(page, "Ada Lovelace", "02139", "5", "Express")
    page.click("#print")
    wait_for_answer(page)
    expect(page.locator("li.label")).to_have_count(1)

    fill_label(page, "Ada Lovelace", "02139", "5.5", "Express")
    page.click("#print")
    wait_for_answer(page)
    expect(page.locator("#service-error")).to_have_text(
        "Express takes 5 kg or less."
    )
    # The weight is fine on its own, so it's the service that gets the blame.
    expect(page.locator("#weight-error")).to_have_text("")
    expect(page.locator("li.label")).to_have_count(1)


def test_fixing_mistakes_clears_the_messages(page: Page) -> None:
    open_desk(page)
    fill_label(page, "Ada Lovelace", "2139", "2.5", "Standard")
    page.click("#print")
    wait_for_answer(page)
    expect(page.locator("#postcode-error")).to_have_text(
        "Postcode must be five digits."
    )

    # A refused label keeps what was typed, so only the postcode is redone.
    page.fill("#postcode", "02139")
    page.click("#print")
    wait_for_answer(page)

    expect(page.locator("li.label")).to_have_count(1)
    expect(page.locator(".field-error")).to_have_text(["", "", "", ""])
