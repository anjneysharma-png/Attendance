"""
Fetch absent employees list from etimeoffice.com dashboard.
Login with Company ID, Username, Password -> TotalAbsentEmpList -> Show All -> scrape table.
"""
import os
import logging
from typing import Any

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)

BASE_URL = "https://www.etimeoffice.com"
LOGIN_URL = f"{BASE_URL}/Login/loginCheck"
ABSENT_LIST_URL = f"{BASE_URL}/Dashboard/TotalAbsentEmpList"


def _get_credentials() -> tuple[str, str, str]:
    company_id = os.environ.get("ETIME_COMPANY_ID", "").strip()
    user = os.environ.get("ETIME_USER", "").strip()
    password = os.environ.get("ETIME_PASSWORD", "").strip()
    if not company_id or not user or not password:
        raise ValueError(
            "ETIME_COMPANY_ID, ETIME_USER, and ETIME_PASSWORD must be set"
        )
    return company_id, user, password


def _login(page: Any) -> None:
    """Fill login form (Company ID, Username, Password) and submit."""
    company_id, user, password = _get_credentials()

    # Login form at /Login/loginCheck: 2 text inputs then password.
    # Screenshot: first field (single-person icon), second (multiple-people icon), then password.
    # Plan: Company ID, Username, Password -> we map first text = Company ID, second = Username.
    text_inputs = page.locator('input[type="text"]').all()
    if len(text_inputs) >= 2:
        text_inputs[0].fill(company_id)
        text_inputs[1].fill(user)
    else:
        page.locator('input[type="text"]').first.fill(company_id)
        page.locator('input[type="text"]').nth(1).fill(user)
    page.locator('input[type="password"]').fill(password)

    # Terms checkbox if present (e.g. "agree to terms")
    terms = page.locator('input[type="checkbox"]').first
    if terms.is_visible():
        terms.check()

    # Click Login button
    page.get_by_role("button", name="Login").click()
    page.wait_for_load_state("networkidle", timeout=15000)


def _open_absent_list_and_show_all(page: Any) -> None:
    """Navigate to TotalAbsentEmpList and set Show entries to All."""
    page.goto(ABSENT_LIST_URL, wait_until="networkidle", timeout=20000)

    # Wait for table area; "Show" dropdown is above the table (left side).
    page.wait_for_selector("table", timeout=10000)

    # Set "Show ... entries" to "All" (DataTables-style control above table).
    select = page.locator(".dataTables_length select").first
    if not select.is_visible():
        select = page.locator("select").first
    if select.is_visible():
        # DataTables often uses value "-1" for "All", or option with label "All"
        try:
            select.select_option(label="All")
        except Exception:
            try:
                select.select_option(value="-1")
            except Exception:
                select.select_option(index=select.locator("option").count() - 1)

    # Brief wait for table to re-render with all rows
    page.wait_for_timeout(1500)


def _scrape_table(page: Any) -> list[dict[str, str]]:
    """Scrape table rows into list of dicts: sr_no, emp_code, name, department."""
    rows = page.locator("table tbody tr").all()
    result = []
    for row in rows:
        cells = row.locator("td").all()
        if len(cells) >= 4:
            result.append({
                "sr_no": cells[0].inner_text().strip(),
                "emp_code": cells[1].inner_text().strip(),
                "name": cells[2].inner_text().strip(),
                "department": cells[3].inner_text().strip(),
            })
    return result


def fetch_absent_list(headless: bool = True) -> list[dict[str, str]]:
    """
    Login to etimeoffice, open TotalAbsentEmpList, set Show entries to All, scrape table.
    Returns list of dicts with keys: sr_no, emp_code, name, department.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        )
        page = context.new_page()

        try:
            page.goto(LOGIN_URL, wait_until="networkidle", timeout=20000)
            _login(page)

            # Wait for redirect after login (dashboard or similar)
            page.wait_for_url(f"{BASE_URL}/**", timeout=10000)
            page.wait_for_timeout(2000)

            _open_absent_list_and_show_all(page)
            data = _scrape_table(page)
            logger.info("Fetched %d absent employees", len(data))
            return data

        except PlaywrightTimeout as e:
            logger.exception("Playwright timeout: %s", e)
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from dotenv import load_dotenv
    load_dotenv()
    data = fetch_absent_list(headless=False)
    for row in data:
        print(row)
