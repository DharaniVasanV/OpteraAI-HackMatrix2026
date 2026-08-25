"""
app/services/browser.py

Purpose
-------
Uses Playwright to launch a headless Chromium instance, navigate to a
meeting URL, and click through the join flow for Google Meet, Zoom, or Teams.

Google Meet is always joined as an anonymous guest — no stored Google
session/login is used. If Meet redirects to accounts.google.com, that means
the meeting requires a signed-in account and we fail fast rather than
attempting an automated login.

Flow
----
meeting_joiner.py -> join_meeting(meeting_url, platform, bot_name)
    -> launch_browser()
    -> page.goto(meeting_url)
    -> platform-specific join steps
    -> return (success: bool, browser: Browser | None, page: Page | None)
"""

from playwright.async_api import async_playwright, Browser, Page, BrowserContext, Playwright

try:
    from pyvirtualdisplay import Display
except ImportError:
    Display = None

from app.services import recorder
from app.utils.logger import get_logger

logger = get_logger(__name__)

from typing import Any

_active_playwrights: dict[int, Playwright] = {}
_active_displays: dict[int, Any] = {}

_IN_CALL_SELECTOR = '[aria-label*="Leave call" i], [aria-label*="Leave" i], [aria-label*="hang up" i], button[jsname="CQeAdf"], button[jsname="CQylEf"]'
_DENIED_TEXT_SELECTOR = 'text=/denied your request|can.?t join this call|removed you from the call|no longer available/i'
_INVALID_MEETING_SELECTOR = 'text=/check your meeting code|misspelled or the meeting has ended|invalid meeting/i'

async def launch_browser() -> tuple[Browser, BrowserContext, Page]:
    import sys
    import os
    import base64

    display = None
    if sys.platform != "win32":
        try:
            display = Display(visible=0, size=(1280, 720))
            display.start()
        except Exception as ex:
            logger.warning("Xvfb display not running (continuing without virtual display): %s", ex)

    playwright = await async_playwright().start()
    browser = None
    try:
        launch_kwargs = dict(
            headless=False,
            args=[
                "--use-fake-ui-for-media-stream",
                "--autoplay-policy=no-user-gesture-required",
                "--no-user-gesture-required",
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-features=WebRtcHideLocalIpsWithMdns",
            ],
        )
        try:
            browser = await playwright.chromium.launch(channel="chrome", **launch_kwargs)
        except Exception:
            browser = await playwright.chromium.launch(**launch_kwargs)

        session_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "google_session.json"))

        session_b64 = os.environ.get("GOOGLE_SESSION_B64")
        if session_b64:
            try:
                with open(session_file, "wb") as f:
                    f.write(base64.b64decode(session_b64))
            except Exception:
                pass

        if os.path.exists(session_file):
            context = await browser.new_context(
                storage_state=session_file,
                permissions=["camera", "microphone"],
                viewport={"width": 1280, "height": 720},
                locale="en-US",
            )
        else:
            context = await browser.new_context(
                permissions=["camera", "microphone"],
                viewport={"width": 1280, "height": 720},
                locale="en-US",
            )

        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        await context.add_init_script(recorder._INIT_WEBAUDIO_CAPTURE_JS)
        page = await context.new_page()

        try:
            from playwright_stealth import stealth_async
            await stealth_async(page)
        except ImportError:
            pass

        _active_playwrights[id(browser)] = playwright
        if display:
            _active_displays[id(browser)] = display
        return browser, context, page

    except Exception:
        if browser is not None:
            await browser.close()
        await playwright.stop()
        if display:
            display.stop()
        raise

async def _wait_for_join_outcome(page: Page, timeout_ms: int = 900_000) -> str:
    poll_interval = 2000
    elapsed = 0
    while elapsed < timeout_ms:
        try:
            if await page.locator(_IN_CALL_SELECTOR).first.is_visible():
                return "joined"
        except Exception:
            pass
        try:
            if await page.locator(_DENIED_TEXT_SELECTOR).first.is_visible():
                return "denied"
        except Exception:
            pass
        await page.wait_for_timeout(poll_interval)
        elapsed += poll_interval
    return "timeout"

async def _join_google_meet(page: Page, meeting_url: str, bot_name: str) -> bool:
    try:
        await page.goto(meeting_url, wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(3000)

        if "accounts.google.com" in page.url:
            return False

        invalid = page.locator(_INVALID_MEETING_SELECTOR)
        if await invalid.count() > 0 and await invalid.first.is_visible():
            return False

        for popup_text in ["Got it", "Dismiss", "Continue without", "Close", "Allow"]:
            try:
                pop = page.locator(f'button:has-text("{popup_text}")')
                if await pop.count() > 0 and await pop.first.is_visible():
                    await pop.first.click(force=True, timeout=2000)
            except Exception:
                pass

        for device in ["microphone", "camera"]:
            try:
                off_btn = page.locator(f'button[aria-label*="Turn off {device}" i], div[role="button"][aria-label*="Turn off {device}" i], button[data-tooltip*="Turn off {device}" i]').first
                if await off_btn.count() > 0 and await off_btn.is_visible():
                    await off_btn.click(timeout=2000)
                    await page.wait_for_timeout(300)
            except Exception:
                pass

        await page.wait_for_timeout(2000)
        try:
            name_input = page.locator('input[placeholder*="name" i], input[aria-label*="name" i]')
            if await name_input.count() > 0 and await name_input.first.is_visible():
                await name_input.first.fill(bot_name)
                await name_input.first.press("Tab")
                await page.wait_for_timeout(1000)
        except Exception:
            pass

        join_btn = page.locator('button:has-text("Ask to join"):visible, [role="button"]:has-text("Ask to join"):visible, button:has-text("Join now"):visible, [role="button"]:has-text("Join now"):visible')
        try:
            await join_btn.first.wait_for(state="visible", timeout=90_000)
        except Exception:
            all_buttons = page.locator('button:visible, [role="button"]:visible')
            count = await all_buttons.count()
            found = None
            for i in range(count):
                txt = ((await all_buttons.nth(i).inner_text()) or "").strip().lower()
                if "join" in txt or "ask to" in txt:
                    found = all_buttons.nth(i)
                    break
            if found is None:
                return False
            join_btn = found

        clicked = False
        try:
            box = await join_btn.first.bounding_box()
            if box:
                x = box["x"] + box["width"] / 2
                y = box["y"] + box["height"] / 2
                await page.mouse.move(x, y)
                await page.wait_for_timeout(200)
                await page.mouse.click(x, y)
                clicked = True
            else:
                await join_btn.first.click(force=True, timeout=5000)
                clicked = True
        except Exception:
            pass

        if not clicked:
            return False

        outcome = await _wait_for_join_outcome(page, timeout_ms=900_000)
        if outcome == "joined":
            return True
        return False

    except Exception:
        return False

async def _join_zoom(page: Page, meeting_url: str, bot_name: str) -> bool:
    try:
        await page.goto(meeting_url, wait_until="domcontentloaded", timeout=30_000)
        frame = page
        for f in page.frames:
            if "zoom" in f.url:
                frame = f
                break
        name_input = frame.locator('input#inputname, input[name="uname"]')
        if await name_input.count() > 0:
            await name_input.first.fill(bot_name)
        join_btn = frame.locator('button:has-text("Join"), #joinBtn')
        await join_btn.first.click(timeout=20_000)
        await page.locator('button[aria-label*="leave" i]').first.wait_for(timeout=60_000)
        return True
    except Exception:
        return False

async def _join_teams(page: Page, meeting_url: str, bot_name: str) -> bool:
    try:
        await page.goto(meeting_url, wait_until="domcontentloaded", timeout=30_000)
        cont = page.locator('a:has-text("Continue on this browser"), button:has-text("Continue on this browser")')
        if await cont.count() > 0:
            await cont.first.click(timeout=5000)
        name_input = page.locator('input[data-tid="prejoin-display-name-input"]')
        if await name_input.count() > 0:
            await name_input.first.fill(bot_name)
        join_btn = page.locator('button[data-tid="prejoin-join-button"]')
        await join_btn.first.click(timeout=20_000)
        await page.locator('[data-tid="hangup-leave-button"]').first.wait_for(timeout=60_000)
        return True
    except Exception:
        return False

_PLATFORM_HANDLERS = {
    "google_meet": _join_google_meet,
    "zoom": _join_zoom,
    "teams": _join_teams,
}

async def join_meeting(meeting_url: str, platform: str, bot_name: str) -> tuple[bool, Browser | None, Page | None]:
    handler = _PLATFORM_HANDLERS.get(platform)
    if handler is None:
        return False, None, None
    browser, context, page = await launch_browser()
    success = await handler(page, meeting_url, bot_name)

    if not success:
        await context.close()
        await leave_meeting(browser)
        return False, None, None
    return True, browser, page

async def leave_meeting(browser: Browser | None) -> None:
    if browser is None:
        return
    playwright = _active_playwrights.pop(id(browser), None)
    display = _active_displays.pop(id(browser), None)
    try:
        await browser.close()
    finally:
        if playwright is not None:
            await playwright.stop()
        if display is not None:
            display.stop()

async def ensure_muted(page: Page | None) -> None:
    if not page or page.is_closed():
        return
    try:
        for device in ["microphone", "camera"]:
            off_btn = page.locator(f'button[aria-label*="Turn off {device}" i], button[data-tooltip*="Turn off {device}" i]').first
            if await off_btn.count() > 0 and await off_btn.is_visible():
                await off_btn.click(timeout=1000)
    except Exception:
        pass

async def is_meeting_active(page: Page | None, platform: str) -> bool:
    if not page or page.is_closed():
        return False
    try:
        if platform == "google_meet":
            url = (page.url or "").lower()
            if "landing" in url or (url.startswith("https://meet.google.com") and len(url.rstrip("/").split("/")) <= 3):
                return False

            import time
            if not hasattr(page, "_joined_timestamp"):
                setattr(page, "_joined_timestamp", time.time())

            elapsed_since_join = time.time() - getattr(page, "_joined_timestamp", time.time())

            try:
                ended = await page.evaluate('''() => {
                    try {
                        let text = document.body ? document.body.innerText.toLowerCase() : "";
                        if (text.includes("return to home screen") || text.includes("ended this meeting") || text.includes("ended the call") || text.includes("has ended") || text.includes("call ended") || text.includes("you left the meeting") || text.includes("someone removed you")) return true;
                        return false;
                    } catch(e) { return false; }
                }''')
                if ended:
                    return False

                if elapsed_since_join > 15:
                    is_alone = await page.evaluate('''() => {
                        try {
                            let nodes = document.querySelectorAll('[data-participant-id], [data-requested-participant-id]');
                            let ids = new Set([...nodes].map(el => el.getAttribute('data-participant-id') || el.getAttribute('data-requested-participant-id')).filter(Boolean));
                            return ids.size === 1;
                        } catch(e) { return false; }
                    }''')
                    if is_alone:
                        return False
            except Exception:
                pass
            return True
        elif platform == "teams":
            return await page.locator('[data-tid="hangup-leave-button"]').count() > 0
    except Exception:
        pass
    return False

async def connect_bot_session() -> str:
    """
    Opens a visible browser window so the user can log in to Google manually.
    Once sign-in is detected (SID / HSID cookies appear), saves the session
    to google_session.json in Playwright storage_state format.
    Uses pure Playwright — no undetected_chromedriver / ChromeDriver needed.
    """
    import os
    import json
    import asyncio
    from playwright.async_api import async_playwright

    session_file = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "google_session.json")
    )

    logger.info("Opening browser for Google sign-in (Playwright)...")

    async with async_playwright() as p:
        # Try real Chrome first, fall back to Playwright's bundled Chromium
        try:
            browser = await p.chromium.launch(
                channel="chrome",
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
            )
        except Exception:
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
            )

        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/127.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        # Bypass webdriver flag detection
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )

        await page.goto("https://accounts.google.com/signin", wait_until="domcontentloaded")
        logger.info("Browser opened. Waiting for user to complete Google sign-in (up to 3 minutes)...")

        # Poll every second for auth cookies for up to 180 seconds
        signed_in = False
        for _ in range(180):
            await asyncio.sleep(1)
            try:
                cookies = await context.cookies()
                cookie_names = [c["name"] for c in cookies]
                current_url = page.url.lower()
                if (
                    any(k in cookie_names for k in ["SID", "HSID", "SSID", "__Secure-1PSID"])
                    and "accounts.google.com" not in current_url
                ):
                    logger.info("Google sign-in detected! Saving session...")
                    signed_in = True
                    await asyncio.sleep(1.5)
                    break
            except Exception:
                pass

        if not signed_in:
            await browser.close()
            raise RuntimeError(
                "Sign-in timed out after 3 minutes. Please try again and complete the login promptly."
            )

        # Save in Playwright storage_state format (compatible with add_cookies)
        cookies = await context.cookies()
        fixed_cookies = []
        for c in cookies:
            cookie = {
                "name": c["name"],
                "value": c["value"],
                "domain": c.get("domain", ".google.com"),
                "path": c.get("path", "/"),
                "httpOnly": c.get("httpOnly", False),
                "secure": c.get("secure", True),
                "sameSite": c.get("sameSite", "None") if c.get("sameSite") in ("Strict", "Lax", "None") else "None",
            }
            if c.get("expires") and c["expires"] > 0:
                cookie["expires"] = c["expires"]
            fixed_cookies.append(cookie)

        state = {"cookies": fixed_cookies, "origins": []}
        os.makedirs(os.path.dirname(session_file), exist_ok=True)
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

        await browser.close()

    logger.info("Google session saved to %s (%d cookies)", session_file, len(fixed_cookies))
    return session_file