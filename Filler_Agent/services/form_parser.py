import os
import json
import asyncio
import logging
import concurrent.futures

logger = logging.getLogger(__name__)

MOCK_DEMO_QUESTIONS = [
    {"field_id": "q1_fullname",  "question_text": "What is your full name?",                          "field_type": "short_text", "is_required": True,  "options": []},
    {"field_id": "q2_email",     "question_text": "Email Address",                                    "field_type": "short_text", "is_required": True,  "options": []},
    {"field_id": "q3_phone",     "question_text": "Phone Number",                                     "field_type": "short_text", "is_required": False, "options": []},
    {"field_id": "q4_role",      "question_text": "Preferred Job Role / Title",                       "field_type": "dropdown",   "is_required": True,  "options": ["Software Engineer", "Product Manager", "Data Scientist", "UI/UX Designer", "DevOps Engineer"]},
    {"field_id": "q5_experience","question_text": "Years of Professional Experience",                 "field_type": "radio",      "is_required": True,  "options": ["0-1 Years", "2-4 Years", "5-8 Years", "9+ Years"]},
    {"field_id": "q6_skills",    "question_text": "Technical Skills (Select all that apply)",         "field_type": "checkbox",   "is_required": False, "options": ["Python", "JavaScript / HTML / CSS", "Docker / Kubernetes", "SQL & Databases", "Cloud Platforms (AWS/GCP)"]},
    {"field_id": "q7_bio",       "question_text": "Briefly describe your career goals and background","field_type": "paragraph",  "is_required": False, "options": []},
    {"field_id": "q8_location",  "question_text": "City / Current Location",                          "field_type": "short_text", "is_required": True,  "options": []},
    {"field_id": "q9_resume",    "question_text": "Upload Resume / CV (PDF or DOCX)",                 "field_type": "file",       "is_required": False, "options": []},
]


def _clean_url(form_url: str) -> str:
    url = form_url.strip()
    if "/edit" in url:
        url = url.split("/edit")[0] + "/viewform"
    # Strip usp param — causes forced login even on public forms
    if "?" in url:
        base, params = url.split("?", 1)
        kept = "&".join(p for p in params.split("&") if not p.startswith("usp="))
        url = f"{base}?{kept}" if kept else base
    return url


async def parse_google_form(form_url: str, user_email: str = "default"):
    clean = _clean_url(form_url)
    logger.info(f"Parsing form URL: {clean}")

    if clean.lower() in ["demo", "test", "example"]:
        return {"title": "Job Application & Developer Survey 2026", "description": "", "questions": MOCK_DEMO_QUESTIONS}

    try:
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return await loop.run_in_executor(pool, lambda: asyncio.run(_playwright_parse(clean, user_email)))
    except Exception as err:
        logger.error(f"Form parse error: {err}")
        return {"error": str(err), "title": "Extraction Failed", "questions": []}


async def _playwright_parse(clean_url: str, user_email: str = "default"):
    from playwright.async_api import async_playwright
    import os
    # Import the shared cookie loader from form_filler
    try:
        from services.form_filler import _load_google_cookies
    except ImportError:
        from Filler_Agent.services.form_filler import _load_google_cookies

    google_cookies = _load_google_cookies()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-extensions",
            ]
        )

        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="en-US",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/127.0.0.0 Safari/537.36"
            ),
        )

        if google_cookies:
            await context.add_cookies(google_cookies)
            logger.info(f"[parser] Injected {len(google_cookies)} Google cookies.")

        page = await context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

        try:
            response = await page.goto(clean_url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(3000)
            page_title = await page.title()

            if (response and response.status == 404) or "Page not found" in page_title:
                return {"error": "Google Form not found (404). Please check the URL.", "title": "Not Found", "questions": []}

            current_url = page.url.lower()
            if "accounts.google.com" in current_url and "signin" in current_url:
                return {
                    "error": (
                        "Google session expired. Please click 'Connect Bot Session' on the Meeting Agent "
                        "dashboard to refresh your session, then try again."
                    ),
                    "title": "Auth Required",
                    "questions": []
                }

            try:
                await page.wait_for_selector(
                    '[jsmodel], div[data-params], div.freebirdFormviewerViewItemsItemItem, div[role="listitem"]',
                    timeout=15000
                )
            except Exception:
                pass

            form_title = page_title
            try:
                t = await page.query_selector('div[role="heading"], h1, div.freebirdFormviewerViewHeaderHeader')
                if t:
                    txt = (await t.inner_text()).strip()
                    if txt: form_title = txt
            except Exception:
                pass

            questions = await _extract_questions(page)

            if questions:
                return {"title": form_title or "Google Form", "description": "Extracted via Playwright.", "questions": questions}
            else:
                return {"error": "Failed to fetch form questions. Make sure the Google Form URL is valid and accessible.", "title": "Extraction Failed", "questions": []}

        except Exception as err:
            logger.error(f"Playwright parse error: {err}")
            return {"error": f"Failed to fetch form from URL: {err}", "title": "Extraction Failed", "questions": []}
        finally:
            if 'context' in locals() and context:
                await context.close()
            if browser:
                await browser.close()


async def _extract_questions(page) -> list:
    """Try multiple selector strategies to extract questions from Google Forms."""
    questions = []

    # Strategy 1: Find all blocks that have data-params or match standard question item classes
    blocks = await page.query_selector_all('div[data-params], div.geS5ne, div[jsmodel][data-params]')
    if not blocks:
        # Strategy 2: Classic selectors
        blocks = await page.query_selector_all(
            'div.freebirdFormviewerViewItemsItemItem, '
            'div.freebirdFormviewerViewItemsItemItemContainer, '
            'div[role="listitem"], '
            'div.QrShb'
        )
    if not blocks:
        # Strategy 3: Any block containing a heading + input
        blocks = await page.query_selector_all('div[jscontroller]')

    logger.info(f"Found {len(blocks)} question blocks")

    idx = 1
    seen_texts = set()

    for block in blocks:
        try:
            # Try to extract details from data-params first (highly reliable for modern Google Forms)
            data_params_str = await block.get_attribute("data-params")
            parsed_from_params = False
            question_text = ""
            field_type = "short_text"
            options = []

            if data_params_str:
                try:
                    clean_str = data_params_str.strip()
                    # Google Forms prefixes with "%.@." (exactly 4 chars) — try both stripped and raw
                    parsed_data = None
                    for attempt in [clean_str, clean_str[4:] if clean_str.startswith("%.@.") else None]:
                        if attempt is None:
                            continue
                        try:
                            parsed_data = json.loads(attempt)
                            break
                        except Exception:
                            continue

                    if parsed_data and isinstance(parsed_data, list) and len(parsed_data) >= 2:
                        # Structure: [form_id, question_text, description, type_block, choices_block, ...]
                        raw_q_text = str(parsed_data[1] or "")
                        question_text = raw_q_text.replace("*", "").split("\n")[0].strip().rstrip(":")

                        # type_block is parsed_data[3]: can be int or [int, ...] 
                        type_block = parsed_data[3] if len(parsed_data) > 3 else 0
                        if isinstance(type_block, list):
                            type_id = type_block[0] if type_block else 0
                        else:
                            type_id = type_block if isinstance(type_block, int) else 0

                        type_mapping = {
                            0: "short_text",
                            1: "paragraph",
                            2: "radio",
                            3: "dropdown",
                            4: "checkbox",
                            9: "file",
                            10: "date",
                            11: "time",
                        }
                        field_type = type_mapping.get(type_id, "short_text")

                        # Extract choices — structure: parsed_data[4][0][1] = list of [option_text, ...]
                        if type_id in (2, 3, 4) and len(parsed_data) > 4 and parsed_data[4]:
                            try:
                                options_block = parsed_data[4]
                                # Can be [[...]] or [[[option, ...], ...]]
                                if isinstance(options_block[0], list) and len(options_block[0]) > 1:
                                    options_raw = options_block[0][1]
                                else:
                                    options_raw = options_block
                                for opt_item in (options_raw or []):
                                    if opt_item and isinstance(opt_item, list) and len(opt_item) > 0 and opt_item[0]:
                                        options.append(str(opt_item[0]).strip())
                                    elif isinstance(opt_item, str) and opt_item.strip():
                                        options.append(opt_item.strip())
                            except Exception:
                                pass

                        if question_text:
                            parsed_from_params = True
                except Exception as pe:
                    logger.debug(f"data-params parse note (non-critical): {pe}")


            # Fallback to DOM selectors if data-params extraction failed
            if not question_text:
                heading = await block.query_selector(
                    'span.M7eMe, '
                    'div[role="heading"], '
                    'div.freebirdFormviewerViewItemsItemItemTitle, '
                    'div.freebirdFormviewerComponentsQuestionBaseTitle'
                )
                if not heading:
                    continue

                raw = (await heading.inner_text()).strip()
                if not raw or len(raw) < 2:
                    continue

                question_text = raw.replace("*", "").split("\n")[0].strip().rstrip(":")

            if not question_text or question_text in seen_texts:
                continue
            seen_texts.add(question_text)

            # Required check
            req_elem = await block.query_selector('span.vnumgf, span[aria-label*="required" i], span[aria-label*="Required"]')
            is_required = req_elem is not None

            if not parsed_from_params:
                field_type, options = await _detect_field_type(block, page, question_text)

            questions.append({
                "field_id": f"q_{idx}",
                "question_text": question_text,
                "field_type": field_type,
                "is_required": is_required,
                "options": options
            })
            idx += 1

        except Exception as e:
            logger.warning(f"Block parse error: {e}")

    return questions


async def _detect_field_type(block, page, question_text: str) -> tuple:
    q_lower = question_text.lower()
    options = []

    # Date
    if any(k in q_lower for k in ["date of birth", "dob", "birth date", "expiry date", "start date", "end date", "date"]):
        return "date", []
    date_inp = await block.query_selector('input[type="date"], [aria-label*="date" i]')
    if date_inp:
        return "date", []

    # Time
    if "time" in q_lower:
        return "time", []
    time_inp = await block.query_selector('input[type="time"], [aria-label*="time" i]')
    if time_inp:
        return "time", []

    # File upload
    if any(k in q_lower for k in ["upload", "resume", "cv", "attach"]):
        return "file", []
    file_inp = await block.query_selector('input[type="file"], [aria-label*="Add file" i]')
    if file_inp:
        return "file", []

    # Radio
    radios = await block.query_selector_all('div[role="radio"], label input[type="radio"]')
    if radios:
        for r in radios:
            lbl = await r.evaluate('el => el.getAttribute("aria-label") || el.closest("label")?.innerText || el.innerText || ""')
            if lbl and lbl.strip():
                options.append(lbl.strip())
        return "radio", options

    # Checkbox
    checkboxes = await block.query_selector_all('div[role="checkbox"], label input[type="checkbox"]')
    if checkboxes:
        for c in checkboxes:
            lbl = await c.evaluate('el => el.getAttribute("aria-label") || el.closest("label")?.innerText || el.innerText || ""')
            if lbl and lbl.strip():
                options.append(lbl.strip())
        return "checkbox", options

    # Dropdown
    listbox = await block.query_selector('div[role="listbox"], select')
    if listbox:
        opts = await block.query_selector_all('div[role="option"], option')
        for o in opts:
            t = (await o.inner_text()).strip()
            if t and t not in ("Choose", "Select"):
                options.append(t)
        return "dropdown", options

    # Paragraph / long text
    textarea = await block.query_selector('textarea')
    if textarea:
        return "paragraph", []

    # Short text (default)
    return "short_text", []
