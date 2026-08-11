import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connection import get_connection

def save_listings(listings):
    conn = get_connection()
    cursor = conn.cursor()

    saved = 0
    for listing in listings:
        if listing["price_per_night"] is None:
            continue  # skip listings with no price

        cursor.execute("""
            INSERT INTO properties (title, region, price)
            VALUES (%s, %s, %s)
        """, (
            listing["title"],
            listing["region"],
            listing["price_per_night"]
        ))
        saved += 1

    conn.commit()
    cursor.close()
    conn.close()

    print(f"Saved {saved} listings to database!")