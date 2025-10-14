from playwright.sync_api import sync_playwright, expect

def run(playwright):
    browser = playwright.chromium.launch()
    page = browser.new_page()
    try:
        page.goto("http://127.0.0.1:8080", wait_until="domcontentloaded")

        # Wait for the terminal to be initialized and rendered
        # We'll wait for the terminal's viewport to be visible.
        terminal_viewport = page.locator(".xterm-viewport")
        expect(terminal_viewport).to_be_visible(timeout=15000) # Increased timeout for VM boot

        # Add a small delay to ensure rendering is complete
        page.wait_for_timeout(1000)

        page.screenshot(path="jules-scratch/verification/verification.png")
    finally:
        browser.close()

with sync_playwright() as playwright:
    run(playwright)