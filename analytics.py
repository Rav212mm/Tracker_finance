from database import get_expenses_by_category, get_category_trend

# ── Category classification ────────────────────────────────────────────────────
# Essential: fixed obligations that are very hard to reduce
ESSENTIAL = {
    "Czynsz i wynajem",
    "Spłaty rat",
    "Podatki",
    "Spłata karty kredytowej",
    "Rachunki",
}

# Semi-discretionary: necessary but with some room to optimise
SEMI = {
    "Żywność i chemia domowa",
    "Paliwo",
    "Zdrowie i uroda",
    "Opłaty i odsetki",
}

# Discretionary: easiest to cut
DISCRETIONARY = {
    "Sport i hobby",
    "Multimedia, książki i prasa",
    "Osobiste - inne",
    "Wypłata gotówki",
    "Bez kategorii",
    "Remont i ogród",
    "Rozrywka",
    "Hobby",
}


def category_type(category: str) -> str:
    cat = category.strip()
    if cat in ESSENTIAL:
        return "essential"
    if cat in DISCRETIONARY:
        return "discretionary"
    if cat in SEMI:
        return "semi"
    # Unknown categories default to semi-discretionary
    return "semi"


def get_reducible_insights(year_month: str = None) -> list:
    """
    Return a list of non-essential expense categories sorted by reduction priority.
    Each item contains:
        category, total, type ('discretionary' | 'semi'), trend_pct, potential_saving
    """
    all_cats = get_expenses_by_category(year_month, exclude_internal=True)

    insights = []
    for item in all_cats:
        cat = item["category"]
        total = item["total"]
        ctype = category_type(cat)

        if ctype == "essential":
            continue

        # Trend vs previous month (trend_data ordered newest → oldest)
        trend_data = get_category_trend(cat, months=3)
        trend_pct = None
        if len(trend_data) >= 2:
            cur = trend_data[0]["total"]
            prev = trend_data[1]["total"]
            if prev > 0:
                trend_pct = ((cur - prev) / prev) * 100

        insights.append(
            {
                "category": cat,
                "total": total,
                "type": ctype,
                "trend_pct": trend_pct,
                "potential_saving": total * 0.20,  # conservative 20% reduction estimate
            }
        )

    # Discretionary first, then semi; within each group sort by amount descending
    insights.sort(key=lambda x: (0 if x["type"] == "discretionary" else 1, -x["total"]))
    return insights
