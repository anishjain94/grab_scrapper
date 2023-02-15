import asyncio

import playwright
from fp.fp import FreeProxy
from playwright.async_api import BrowserContext, Page, Route, async_playwright


def GetProxy() -> str:
    proxy = FreeProxy(country_id="SG", timeout=1).get()
    print(proxy)
    return proxy


currentIdx = 0
data = {}


async def handle_route(route: Route) -> None:
    response = await route.fetch()
    body = await response.text()
    global currentIdx
    print(body)
    data[currentIdx] = body
    currentIdx += 1
    await route.fulfill(
        response=response,
        body=body,
        headers=response.headers,
    )


async def main():
    async with async_playwright() as playwright:
        vendor = playwright.chromium
        vendorInstance = await vendor.launch(
            slow_mo=1000, headless=False,
            proxy={
                "server": GetProxy(),
            }
        )

        ctx = await vendorInstance.new_context(geolocation={"longitude": 48.858455, "latitude": 2.294474},
                                               permissions=["geolocation"])
        await ctx.grant_permissions(["geolocation"], origin="https://food.grab.com")
        browser = ctx.browser

        page = await browser.new_page()

        await page.goto("https://food.grab.com/sg/en/restaurants", timeout=1000000)

        await page.get_by_text("Type your location").click()

        await page.route("**/search", handle_route)

        await page.keyboard.type(
            "Embassy Of The Republic Of The Philippines", delay=20)
        await page.wait_for_timeout(5000)
        await page.keyboard.press("ArrowDown")
        await page.keyboard.press("Enter")

        await page.wait_for_load_state('networkidle', timeout=100000)
        await page.mouse.wheel(0, 1500)

        await page.wait_for_timeout(100000)

        print(data.keys())

        while data.get(currentIdx-1) != None:
            print(data.keys())
            await page.mouse.wheel(0, 1000)
            await page.wait_for_timeout(10000)

        await browser.close()


asyncio.run(main())
