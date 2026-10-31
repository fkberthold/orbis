from playwright.sync_api import Dialog, Page, expect


def open_queue(page: Page) -> None:
    page.goto("/")
    expect(page.locator("#heading")).to_have_text("Spoke and Chain Repair Queue")


def job(page: Page, ticket: str):
    # Three rows say "Brake pads", so the ticket is what picks one out.
    return page.locator("li.job").filter(has_text=ticket)


def tickets(page: Page):
    return page.locator("li.job .ticket")


def test_queue_starts_in_priority_order(page: Page) -> None:
    open_queue(page)
    expect(tickets(page)).to_have_text(["#102", "#101", "#104", "#105", "#103"])


def test_raising_priority_resorts(page: Page) -> None:
    open_queue(page)
    job(page, "#105").get_by_label("Priority").select_option("High")

    # #105 joins #102 at High and stays behind it, because #102 is older.
    expect(tickets(page)).to_have_text(["#102", "#105", "#101", "#104", "#103"])


def test_finish_removes_only_that_job(page: Page) -> None:
    open_queue(page)
    messages = []

    def accept(dialog: Dialog) -> None:
        messages.append(dialog.message)
        dialog.accept()

    page.once("dialog", accept)
    job(page, "#103").get_by_role("button", name="Finish").click()

    expect(job(page, "#103")).to_have_count(0)
    expect(page.locator("li.job")).to_have_count(4)
    expect(page.locator("#done li")).to_have_text(["#103 Brake pads (Chen)"])
    assert messages == ["Finish #103 Brake pads for Chen?"]


def test_cancel_keeps_job(page: Page) -> None:
    open_queue(page)
    messages = []

    def dismiss(dialog: Dialog) -> None:
        messages.append(dialog.message)
        dialog.dismiss()

    page.once("dialog", dismiss)
    job(page, "#101").get_by_role("button", name="Finish").click()

    expect(page.locator("li.job")).to_have_count(5)
    expect(job(page, "#101")).to_have_count(1)
    expect(page.locator("#done li")).to_have_count(0)
    assert messages == ["Finish #101 Brake pads for Ruiz?"]
