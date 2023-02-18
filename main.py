import asyncio
import csv
import json

from fp.fp import FreeProxy
from playwright.async_api import Page, Route, async_playwright


def GetProxy() -> str:
    proxy = FreeProxy(country_id="SG", timeout=1).get()
    print(proxy)
    return proxy


currentIdx = 0
data = {}
field_names = ['name', 'latitude', 'longitude']

location = [
    "Signature Park Condominium - 46A Toh Tuck Road, Singapore, 596738", "Embassy Of Japan - 16 Nassim Road, Singapore", ]


async def handle_route(route: Route) -> None:
    response = await route.fetch()
    body = await response.text()
    global currentIdx
    data[currentIdx] = json.loads(body)
    print(data)
    await route.fulfill(
        response=response,
        body=body,
        headers=response.headers,
    )
    await StoreData(data)
    currentIdx += 1


async def StoreData(data: dict):
    locationInfo = list()

    for restaurants in data[currentIdx]["searchResult"]["searchMerchants"]:
        locationInfo.append(
            {field_names[0]: restaurants["chainName"], field_names[1]: restaurants["latlng"]["latitude"], field_names[2]: restaurants["latlng"]["longitude"]})

    with open('locationInfo.csv', 'a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(locationInfo)
        csvfile.close()


async def searchNewArea(page: Page, location: str):
    await page.get_by_text("Type your location").click()

    await page.keyboard.type(
        location, delay=20)
    await page.wait_for_timeout(10000)
    await page.keyboard.press("ArrowDown")
    await page.keyboard.press("Enter")

    await page.wait_for_load_state('networkidle', timeout=100000)
    await page.mouse.wheel(0, 1500)

    await page.wait_for_timeout(100000)


async def StartSearch(location: list, currentLocationIdx: int):

    if currentLocationIdx >= len(location):
        return

    async with async_playwright() as playwright:
        vendor = playwright.chromium
        vendorInstance = await vendor.launch(
            slow_mo=2500, headless=False,
            proxy={
                "server": "http://8.219.97.248:80"  # GetProxy(),
            }
        )

        ctx = await vendorInstance.new_context(geolocation={"longitude": 48.858455, "latitude": 2.294474},
                                               permissions=["geolocation"])
        await ctx.grant_permissions(["geolocation"], origin="https://food.grab.com")
        browser = ctx.browser

        page = await browser.new_page()

        await page.goto("https://food.grab.com/sg/en/restaurants", timeout=1000000)
        await page.route("**/search", handle_route)

        await searchNewArea(page, location[currentIdx])

        while data.get(currentIdx-1) != None:
            await page.mouse.wheel(0, 1000)
            await page.wait_for_timeout(10000)
            StartSearch(location, currentLocationIdx+1)
            await browser.close()


asyncio.run(StartSearch(location, 0))
