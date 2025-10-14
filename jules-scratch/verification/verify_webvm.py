from playwright.sync_api import Page, expect

def test_webvm_terminal(page: Page):
    """
    This test verifies that the WebVM terminal interface loads correctly.
    """
    # 1. Arrange: Go to the local server.
    page.goto("http://127.0.0.1:8080")

    # 2. Assert: Confirm the terminal container is visible.
    terminal_container = page.locator("#terminal-container")
    expect(terminal_container).to_be_visible()

    # 3. Screenshot: Capture the final result for visual verification.
    page.screenshot(path="jules-scratch/verification/verification.png")