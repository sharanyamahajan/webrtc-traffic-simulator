import asyncio
import os
import random  # Handles random name and proxy selection
import sys
from playwright.async_api import async_playwright

# Import urllib to fetch the free proxy list dynamically
import urllib.request

# =====================================================================
# SYSTEM CONFIGURATION: DYNAMIC API PROXY LINK
# Replace this string with your exact raw text/TXT export URL from advanced.name
# =====================================================================
FREE_PROXY_API_URL = "https://advanced.name/freeproxy/6a084c352c83b?type=http"

# Global proxy pool variable that will be populated at runtime
PROXY_POOL = []


def fetch_live_proxies():
    """Dynamically downloads the raw text proxy list and prepares it for the bots"""
    global PROXY_POOL
    try:
        print("[*] Contacting advanced.name API to fetch fresh proxies...")
        req = urllib.request.Request(
            FREE_PROXY_API_URL, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            raw_text = response.read().decode("utf-8")

            # Split text by lines and clean up any empty spacing
            lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

            for line in lines:
                # Public lists are usually format: "192.168.1.1:8080"
                # Playwright needs the protocol prepended: "http://192.168.1.1:8080"
                if "http" not in line.lower():
                    PROXY_POOL.append(f"http://{line}")
                else:
                    PROXY_POOL.append(line)

        print(
            f"[SUCCESS] Loaded {len(PROXY_POOL)} working proxies into the cluster pool!"
        )
    except Exception as e:
        print(
            f"[WARNING] Failed to fetch proxy list via link. Falling back to default cloud routing. Error: {e}"
        )


# =====================================================================
# INDIAN NAMES POOL
# =====================================================================
INDIAN_NAMES = [
    "Aarav Sharma",
    "Vivaan Patel",
    "Aditya Mishra",
    "Vihaan Gupta",
    "Arjun Joshi",
    "Sai Reddy",
    "Reyansh Kumar",
    "Aayan Singh",
    "Krishna Murthy",
    "Ishaan Choudhury",
    "Ananya Iyer",
    "Diya Nair",
    "Pari Saxena",
    "Pihu Banerjee",
    "Isha Malhotra",
    "Aadhya Rao",
    "Avani Verma",
    "Saanvi Kulkarni",
    "Ahana Chatterjee",
    "Prisha Shah",
    "Rahul Mehta",
    "Amit Das",
    "Vikram Goel",
    "Sanjay Dutt",
    "Deepak Kapur",
    "Rohan Hegde",
    "Neha Trivedi",
    "Priya Deshmukh",
    "Anjali Kapoor",
    "Sneha Gill",
    "Rohan Sharma",
    "Manish Pandey",
    "Abhishek Bisht",
    "Siddharth Roy",
    "Karan Johar",
    "Divya Khosla",
    "Pooja Bhatt",
    "Kriti Sanon",
    "Riya Sen",
    "Shruti Haasan",
]


async def launch_bot(bot_id, meet_url, proxy_server=None):
    """Launches an isolated instance with stealth masking and custom routing"""
    async with async_playwright() as p:

        browser_args = [
            "--use-fake-ui-for-media-stream",
            "--use-fake-device-for-media-stream",
            "--mute-audio",
            "--disable-gpu",
            "--disable-blink-features=AutomationControlled",
        ]

        # Apply proxy if one was successfully provided to this thread
        if proxy_server:
            browser_args.append(f"--proxy-server={proxy_server}")
            print(f"[Bot {bot_id}] Masking traffic via proxy: {proxy_server}")

        try:
            browser = await p.chromium.launch(headless=True, args=browser_args)
        except Exception as e:
            print(f"[Bot {bot_id}] Browser launch crash (bad proxy configuration?): {e}")
            return

        context = await browser.new_context(
            permissions=["microphone", "camera"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            locale="en-US",
        )

        page = await context.new_page()
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        try:
            print(f"[Bot {bot_id}] Routing to network stream target...")
            await page.goto(meet_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(6000)

            # --- STEP 1: IDENTITY INPUT (RANDOM INDIAN NAME) ---
            name_selector = "input[aria-label='Your name'], input[placeholder='Your name'], input[type='text']"
            input_element = page.locator(name_selector).first

            await input_element.wait_for(state="attached", timeout=20000)

            random_name = random.choice(INDIAN_NAMES)

            await input_element.evaluate(
                f"(el) => {{ el.value = '{random_name}'; el.dispatchEvent(new Event('input', {{ bubbles: true }})); el.dispatchEvent(new Event('change', {{ bubbles: true }})); }}"
            )
            print(
                f"[Bot {bot_id}] Assigned identity successfully: {random_name}"
            )
            await page.wait_for_timeout(1000)

            # --- STEP 2: OPEN ENTRY SUBMISSION ---
            join_selectors = [
                "button:has-text('Join now')",
                "button:has-text('Ask to join')",
                "button:has-text('Join')",
                "[jsname='Qx7uId']",
            ]

            target_button = None
            for selector in join_selectors:
                locator = page.locator(selector).first
                if await locator.count() > 0:
                    target_button = locator
                    break

            if target_button:
                await target_button.wait_for(state="attached", timeout=25000)
                await target_button.click(force=True)
                print(f"[Bot {bot_id}] Sent connection/handshake payload.")
            else:
                raise Exception(
                    "No active entry submission element discovered."
                )

            # --- STEP 3: THE KEEP-ALIVE LOOP ---
            print(
                f"[Bot {bot_id}] Successfully inside room. Starting keep-alive cycle."
            )
            for _ in range(120):
                await page.wait_for_timeout(10000)
                await page.evaluate("window.scrollTo(0, 1);")

        except Exception as e:
            try:
                err_title = await page.title()
                print(
                    f"[Bot {bot_id}] Terminated on page: '{err_title}'. Details: {e}"
                )
            except:
                print(f"[Bot {bot_id}] Exception encountered: {e}")
        finally:
            await context.close()
            await browser.close()


async def main():
    meet_url = os.environ.get("MEET_URL")
    batch_num = int(os.environ.get("BATCH_NUM", 0))

    if not meet_url:
        print("[CRITICAL] Missing target destination link.")
        sys.exit(1)

    # Automatically call our dynamic proxy fetch tool
    fetch_live_proxies()

    start_id = batch_num * 10
    print(
        f"[*] Initializing Container Node Batch. Range: [{start_id} to {start_id + 9}]"
    )

    tasks = []
    for i in range(10):
        bot_id = start_id + i

        # Pick a proxy out of the dynamically loaded list if available
        # Public free proxies fail often; shuffling them ensures bots don't share identical failing channels
        current_proxy = (
            random.choice(PROXY_POOL) if len(PROXY_POOL) > i else None
        )

        tasks.append(launch_bot(bot_id, meet_url, current_proxy))
        await asyncio.sleep(5)

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
