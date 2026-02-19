ABBR_PATTERNS = [
    {
        "pattern": r"\bc\.(\s*\d{1,4})",
        "title": "circa",
        "abbr": "c.",
        "suffix_group": 1,
    },
    {
        "pattern": r"\b(PLI)(\s*:)",
        "title": "Poor Law Institution",
        "abbr_group": 1,
        "suffix_group": 2,
    },
    {
        "pattern": r"\b(LA)(\s*:)",
        "title": "Local Authority",
        "abbr_group": 1,
        "suffix_group": 2,
    },
    {"pattern": r"\b(AC)(\s*:)", "title": "Acute", "abbr_group": 1, "suffix_group": 2},
    {
        "pattern": r"\b(GER)(\s*:)",
        "title": "Geriatric",
        "abbr_group": 1,
        "suffix_group": 2,
    },
    {
        "pattern": r"\b(LRO)(\s*:)",
        "title": "Local Record Office",
        "abbr_group": 1,
        "suffix_group": 2,
    },
    {
        "pattern": r"\b(AR)(\s*:)",
        "title": "Repository",
        "abbr_group": 1,
        "suffix_group": 2,
    },
    {
        "pattern": r"\b(NRA)(\s*:)",
        "title": "National Register of Archives",
        "abbr_group": 1,
        "suffix_group": 2,
    },
    {
        "pattern": r"\b(C)(\s*:)",
        "title": "Children",
        "abbr_group": 1,
        "suffix_group": 2,
    },
    {
        "pattern": r"\b(CAT)(\s*:)",
        "title": "Catalogue",
        "abbr_group": 1,
        "suffix_group": 2,
    },
    {
        "pattern": r"\b(VOL)(\s*:)",
        "title": "Voluntary",
        "abbr_group": 1,
        "suffix_group": 2,
    },
    {
        "pattern": r"\b(MNT)(\s*:)",
        "title": "Mental",
        "abbr_group": 1,
        "suffix_group": 2,
    },
]