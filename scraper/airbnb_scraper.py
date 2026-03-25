from playwright.sync_api import sync_playwright
import re

def scrape_region(region):
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        url = f"https://www.airbnb.com/s/{region}/homes"
        page.goto(url)
        page.wait_for_timeout(4000)

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

        browser.close()

    return results

if __name__ == "__main__":
    scrape_region("New-York")