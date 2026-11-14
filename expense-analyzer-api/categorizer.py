import re
import unicodedata

from rapidfuzz.distance import DamerauLevenshtein


MERCHANTS = {
    "Groceries": (
        "Lidl", "Kaufland", "Billa", "Tesco", "COOP Jednota", "Jednota", "Terno",
        "Kraj potraviny", "Kraj potravín", "Fresh potraviny", "Fresh Plus", "Yeme", "Biedronka",
        "Moja samoška", "Milk Agro", "Wolt Market", "Bolt Market",
    ),
    "Transport": (
        "Bolt", "Uber", "ZSSK", "Slovakrail", "Slovak Lines", "RegioJet", "Leo Express",
        "DPB", "Dopravný podnik", "IDS BK", "IDSBK", "ARRIVA", "Slovnaft", "OMV",
        "Shell", "Orlen", "eZnámka",
    ),
    "Subscriptions": (
        "Spotify", "Netflix", "Disney Plus", "HBO Max", "YouTube Premium",
        "Apple Music", "iCloud", "Voyo", "Skylink", "Wolt Plus", "Bolt Plus",
    ),
    "Dining": (
        "Bolt Food", "Uber Eats", "Wolt", "Bistro.sk", "McDonald’s",
        "McDonalds", "KFC", "Burger King", "Starbucks",
    ),
    "Shopping": (
        "Alza", "NAY", "Datart", "Mall.sk", "IKEA", "Decathlon", "Pepco",
        "Action", "KiK", "dm", "dm drogerie", "Teta drogéria", "Notino",
    ),
    "Health": (
        "Dr. Max", "DrMax", "BENU", "Pilulka", "Union zdravotná poisťovňa",
        "Dôvera", "VšZP", "Golem Club",
    ),
    "Entertainment": (
        "Cinema City", "Cinemax", "Ticketportal", "Predpredaj.sk", "GoOut",
        "Steam", "PlayStation Store",
    ),
}

CATEGORY_KEYWORDS = {
    "Groceries": (
        "potraviny", "potravín", "potravinách", "nákup potravín", "supermarket", "hypermarket",
        "samoobsluha", "večierka", "pekáreň",
    ),
    "Transport": (
        "taxi", "MHD", "električenka", "cestovný lístok", "cestovné lístky",
        "predplatné MHD", "predplatné na MHD", "predplatný cestovný lístok",
        "vlak", "autobus", "letenka", "parkovné", "parkovanie", "diaľničná známka",
        "čerpacia stanica", "tankovanie", "benzín", "nafta", "gas station",
    ),
    "Subscriptions": (
        "predplatné", "mesačné predplatné", "subscription",
    ),
    "Dining": (
        "reštaurácia", "reštaurácii", "kaviareň", "kaviarni", "bistro",
        "pizzéria", "pizza", "jedáleň", "donáška jedla", "obed", "večera",
        "cafe", "restaurant", "bar",
    ),
    "Shopping": (
        "drogéria", "oblečenie", "obuv", "elektronika", "kníhkupectvo", "purchase",
    ),
    "Health": (
        "lekáreň", "lekárne", "lekárni", "lekár", "zubár", "zubára", "ambulancia",
        "stomatológia", "fyzioterapia", "lieky", "fitness", "posilňovňa",
        "pharmacy", "apteka", "gym",
    ),
    "Entertainment": (
        "kino", "kiná", "divadlo", "koncert", "festival", "vstupenka",
        "vstupenky", "cinema", "tickets",
    ),
}


def normalized_words(text: str) -> list[str]:
    text = text.casefold().replace("+", " plus ")
    decomposed = unicodedata.normalize("NFKD", text)
    plain_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.findall(r"[^\W\d_]+|\d+", plain_text)


def keyword_index(categories: dict[str, tuple[str, ...]]) -> list[tuple[str, str]]:
    keywords = [
        (" ".join(normalized_words(keyword)), category)
        for category, names in categories.items()
        for keyword in names
    ]
    return sorted(keywords, key=lambda entry: (entry[0].count(" "), len(entry[0])), reverse=True)


MERCHANT_RULES = keyword_index(MERCHANTS)
KEYWORD_RULES = keyword_index(CATEGORY_KEYWORDS)
FUZZY_RULES = {
    (keyword, category)
    for rules in (MERCHANT_RULES, KEYWORD_RULES)
    for keyword, category in rules
    if keyword.isalpha() and len(keyword) >= 7
}


def categorize(description: object) -> str:
    if not isinstance(description, str):
        return "Other"

    words = normalized_words(description)
    normalized = f" {' '.join(words)} "
    # Specific product names come before their parent brands, then generic terms.
    for rules in (MERCHANT_RULES, KEYWORD_RULES):
        for keyword, category in rules:
            if f" {keyword} " in normalized:
                return category

    # Match a single typo within a word, including adjacent swapped letters.
    # Short labels like BAR or MHD must match exactly.
    candidates = {word for word in words if word.isalpha() and len(word) >= 6}
    matches = {
        category
        for word in candidates
        for keyword, category in FUZZY_RULES
        if DamerauLevenshtein.distance(word, keyword, score_cutoff=1) <= 1
    }
    return matches.pop() if len(matches) == 1 else "Other"


if __name__ == "__main__":
    for description in (
        "LIDL0312 Žilina",
        "COOP*JEDNOTA",
        "Bolt Food Bratislava",
        "ZSSK - cestovný lístok",
        "Wolt+",
        "LEKAREN Pri stanici",
        "KAUFLNAD",
        "Barclays",
    ):
        print(f"{description} -> {categorize(description)}")
