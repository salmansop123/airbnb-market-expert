# from playwright.sync_api import sync_playwright
# import re
# import sys
# import os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from database.save_listings import save_listings

# def scrape_region(region):
#     results = []

#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False)
#         page = browser.new_page()

#         url = f"https://www.airbnb.com/s/{region}/homes"
#         page.goto(url)
#         page.wait_for_timeout(4000)

#         titles = page.query_selector_all("[data-testid='listing-card-title']")
#         prices = page.query_selector_all("[aria-label*='for']")

#         print(f"Titles found: {len(titles)}")
#         print(f"Prices found: {len(prices)}\n")

#         for i in range(min(len(titles), len(prices))):
#             title = titles[i].inner_text()
#             raw_label = prices[i].get_attribute("aria-label")
#             match = re.search(r'\$[\d,]+', raw_label)
            
#             if match:
#                 price_total = float(match.group().replace('$','').replace(',',''))
#                 price_per_night = round(price_total / 5, 2)
#             else:
#                 price_per_night = None

#             listing = {
#                 "title": title,
#                 "price_per_night": price_per_night,
#                 "region": region
#             }
            
#             results.append(listing)
#             print(listing)

#         browser.close()

#     save_listings(results)
#     return results

# if __name__ == "__main__":
#     scrape_region("New-York")



from playwright.sync_api import sync_playwright
import re
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.save_listings import save_listings

def scrape_region(region):
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US"
        )

        # Hide automation fingerprint
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        url = f"https://www.airbnb.com/s/{region}/homes"
        print(f"Opening: {url}")

        page.goto(url)

        # Wait for prices to appear specifically
        print("Waiting for prices to load...")
        page.wait_for_timeout(6000)

        # Scroll slowly like a human
        page.evaluate("window.scrollBy(0, 400)")
        page.wait_for_timeout(1000)
        page.evaluate("window.scrollBy(0, 400)")
        page.wait_for_timeout(1000)
        page.evaluate("window.scrollBy(0, 400)")
        page.wait_for_timeout(2000)

        titles = page.query_selector_all("[data-testid='listing-card-title']")
        prices = page.query_selector_all("[aria-label*='for']")

        print(f"Titles found: {len(titles)}")
        print(f"Prices found: {len(prices)}\n")

        for i in range(min(len(titles), len(prices))):
            title = titles[i].inner_text()
            raw_label = prices[i].get_attribute("aria-label")
            match = re.search(r'\$[\d,]+', raw_label)

            if match:
                price_total = float(match.group().replace('$','').replace(',',''))
                price_per_night = round(price_total / 5, 2)
            else:
                price_per_night = None

            listing = {
                "title": title,
                "price_per_night": price_per_night,
                "region": region
            }

            results.append(listing)
            print(listing)

        save_listings(results)
        browser.close()

    return results

if __name__ == "__main__":
    regions = [
        "New-York",
        "Los-Angeles",
        "Chicago",
        "Miami",
        "San-Francisco"
    ]
    
    for region in regions:
        print(f"\n========== Scraping {region} ==========")
        scrape_region(region)