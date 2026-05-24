"""
config/keywords.py — Keyword bank for filtering relevant tenders.
Add new keywords here to extend coverage without touching any other file.
"""

KEYWORDS = [
    # ── Artificial Intelligence ────────────────────────────────────────────
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "neural network",
    "natural language processing",
    "nlp",
    "computer vision",
    "generative ai",
    "large language model",
    "llm",
    "ai",

    # ── Data Science & Analytics ───────────────────────────────────────────
    "data science",
    "data analytics",
    "data engineering",
    "business intelligence",
    "bi dashboard",
    "predictive analytics",
    "data warehouse",
    "big data",
    "data lake",
    "etl",

    # ── Software Development ───────────────────────────────────────────────
    "software development",
    "web development",
    "mobile application",
    "mobile app",
    "android app",
    "ios app",
    "erp",
    "enterprise resource planning",
    "crm",
    "custom software",
    "application development",

    # ── Cloud & Infrastructure ─────────────────────────────────────────────
    "cloud computing",
    "cloud migration",
    "cloud infrastructure",
    "aws",
    "azure",
    "google cloud",
    "saas",
    "paas",
    "iaas",
    "devops",
    "kubernetes",
    "docker",

    # ── IT Services ────────────────────────────────────────────────────────
    "it services",
    "it infrastructure",
    "it support",
    "it consulting",
    "managed services",
    "network infrastructure",
    "server",
    "datacenter",
    "data centre",
    "help desk",
    "it security",

    # ── Cybersecurity ─────────────────────────────────────────────────────
    "cybersecurity",
    "cyber security",
    "information security",
    "infosec",
    "soc",
    "security operations",
    "penetration testing",
    "vapt",
    "firewall",
    "encryption",
    "siem",

    # ── Electronics & Embedded Systems ────────────────────────────────────
    "electronics",
    "embedded systems",
    "embedded software",
    "firmware",
    "microcontroller",
    "plc",
    "scada",
    "iot",
    "internet of things",
    "sensors",
    "hardware integration",

    # ── Automation ────────────────────────────────────────────────────────
    "automation",
    "robotic process automation",
    "rpa",
    "workflow automation",
    "process automation",
    "intelligent automation",

    # ── Digital Infrastructure ─────────────────────────────────────────────
    "digital platform",
    "digital transformation",
    "e-governance",
    "egovernance",
    "smart city",
    "digital india",
    "common service centre",
    "csc",
    "digital payment",
    "upi",
    "api integration",

    # ── Telecom & Networking ───────────────────────────────────────────────
    "networking",
    "fiber optic",
    "5g",
    "wi-fi",
    "wifi",
    "lan",
    "wan",
    "vpn",
    "telecommunications",

    # ── GIS & Mapping ─────────────────────────────────────────────────────
    "gis",
    "geographic information",
    "satellite imagery",
    "remote sensing",
    "geospatial",

    # ── Blockchain & Emerging ─────────────────────────────────────────────
    "blockchain",
    "distributed ledger",
    "drone",
    "uav",
    "surveillance system",
    "cctv",
    "video analytics",
]

# ── Exclusion Keywords ─────────────────────────────────────────────────────
# Tenders that match these will be EXCLUDED even if they match above keywords
EXCLUSION_KEYWORDS = [
    "printing",
    "stationery",
    "furniture",
    "canteen",
    "housekeeping",
    "civil work",
    "construction",
    "tiling",
    "flooring",
    "painting",
    "plumbing",
    "vehicle",
    "uniform",
]
