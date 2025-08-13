SQL_QUERIES = {
    # Providers & Receivers
    "Providers per city":
        "SELECT City, COUNT(*) AS total_providers FROM providers GROUP BY City ORDER BY total_providers DESC",
    "Receivers per city":
        "SELECT City, COUNT(*) AS total_receivers FROM receivers GROUP BY City ORDER BY total_receivers DESC",
    "Top food provider types":
        "SELECT Type, COUNT(*) AS contributions FROM providers GROUP BY Type ORDER BY contributions DESC",
    "Provider contacts by city (use sidebar filter)":
        "SELECT Name, Type, Contact FROM providers WHERE City = ? ORDER BY Name",
    "Top receivers by claims":
        """SELECT r.Name, COUNT(c.Claim_ID) AS claims
           FROM receivers r JOIN claims c ON r.Receiver_ID = c.Receiver_ID
           GROUP BY r.Name ORDER BY claims DESC""",

    # Listings & Availability
    "Total food quantity available":
        "SELECT SUM(Quantity) AS total_quantity FROM food_listings",
    "City with most food listings":
        """SELECT Location, COUNT(*) AS listings
           FROM food_listings GROUP BY Location ORDER BY listings DESC LIMIT 5""",
    "Most common food types":
        "SELECT Food_Type, COUNT(*) AS count FROM food_listings GROUP BY Food_Type ORDER BY count DESC",
    "Most common meal types":
        "SELECT Meal_Type, COUNT(*) AS count FROM food_listings GROUP BY Meal_Type ORDER BY count DESC",

    # Claims & Distribution
    "Claims per food item":
        """SELECT f.Food_Name, COUNT(c.Claim_ID) AS total_claims
           FROM claims c JOIN food_listings f ON c.Food_ID = f.Food_ID
           GROUP BY f.Food_Name ORDER BY total_claims DESC""",
    "Top provider by successful claims":
        """SELECT p.Name, COUNT(*) AS success_claims
           FROM claims c
           JOIN food_listings f ON c.Food_ID = f.Food_ID
           JOIN providers p ON f.Provider_ID = p.Provider_ID
           WHERE c.Status='Completed'
           GROUP BY p.Name ORDER BY success_claims DESC LIMIT 5""",
    "Claim status percentage":
        """SELECT Status,
                  ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM claims), 2) AS percentage
           FROM claims GROUP BY Status""",
    "Average quantity claimed per receiver (proxy by item qty)":
        """SELECT r.Name, ROUND(AVG(f.Quantity),2) AS avg_quantity
           FROM claims c
           JOIN food_listings f ON c.Food_ID = f.Food_ID
           JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
           GROUP BY r.Name ORDER BY avg_quantity DESC""",
    "Most claimed meal type":
        """SELECT f.Meal_Type, COUNT(*) AS claims
           FROM food_listings f JOIN claims c ON f.Food_ID = c.Food_ID
           GROUP BY f.Meal_Type ORDER BY claims DESC""",
    "Total food donated by each provider":
        """SELECT p.Name, SUM(f.Quantity) AS total_donated
           FROM providers p JOIN food_listings f ON p.Provider_ID = f.Provider_ID
           GROUP BY p.Name ORDER BY total_donated DESC""",
    # Extra (15th): Top cities by completed claims
    "Top cities by completed claims":
        """SELECT f.Location AS City, COUNT(*) AS completed_claims
           FROM claims c JOIN food_listings f ON c.Food_ID = f.Food_ID
           WHERE c.Status='Completed'
           GROUP BY f.Location ORDER BY completed_claims DESC"""
}
