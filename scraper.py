"""
Winnipeg Property Assessed Value Scraper
=========================================
Usage:
    python scraper.py "630 Main"
    python scraper.py "1555 Portage"

Requirements:
    pip install playwright
    playwright install chromium
"""

import sys
from playwright.sync_api import sync_playwright

BASE_URL = "https://assessment.winnipeg.ca/AsmtTax/English/Propertydetails/default.stm"


def get_assessed_value(address: str) -> None:
    parts = address.strip().split(None, 1)
    if len(parts) < 2:
        print("Error: Provide both number and street name, e.g. '630 Main'")
        sys.exit(1)

    street_num = parts[0]
    street_name = parts[1].split()[0]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.locator("input[name='StreetNumber']").fill(street_num)
        page.locator("input[name='StreetName']").fill(street_name)

        with page.expect_navigation(wait_until="domcontentloaded", timeout=15000):
            page.locator("input#SubmitAddress").click()

        # Find the row with 3 cells where last cell contains "$"
        # There are two: 2026 current and 2027 proposed — grab both
        current_value = None
        proposed_value = None
        property_address = None

        for row in page.locator("tr").all():
            cells = row.locator("td").all()
            if len(cells) == 3:
                col0 = cells[0].inner_text().strip()
                col1 = cells[1].inner_text().strip()
                col2 = cells[2].inner_text().strip()
                if "$" in col2:
                    # Check which section this belongs to by looking at preceding header
                    parent_text = row.locator("xpath=../..").inner_text()
                    if "2027" in parent_text and proposed_value is None:
                        proposed_value = (col0, col1, col2)
                    elif current_value is None:
                        current_value = (col0, col1, col2)

        # Get property address from the page
        addr_row = page.locator("tr").filter(has_text="Roll Number").first
        if addr_row.count():
            property_address = addr_row.inner_text().strip().split("\n")[0]

        print()
        print("=" * 55)
        if property_address:
            print(f"  Property       : {property_address}")
            print("-" * 55)
        if current_value:
            print(f"  [2026 Current Assessment]")
            print(f"  Class          : {current_value[0]}")
            print(f"  Status         : {current_value[1]}")
            print(f"  Assessed Value : {current_value[2]}")
        if proposed_value:
            print(f"  [2027 Proposed Assessment]")
            print(f"  Class          : {proposed_value[0]}")
            print(f"  Status         : {proposed_value[1]}")
            print(f"  Assessed Value : {proposed_value[2]}")
        if not current_value and not proposed_value:
            print("  No assessed value found.")
        print("=" * 55)

        browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python scraper.py "630 Main"')
        sys.exit(1)
    get_assessed_value(" ".join(sys.argv[1:]))