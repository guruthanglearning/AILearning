"""Static S&P 500 universe registry — composition as of 2025-01-15."""
from __future__ import annotations

COMPOSITION_AS_OF = "2025-01-15"

# S&P 500 constituents as of 2025-01-15.
# 503 share classes / 500 companies (GOOGL+GOOG, BRK.A+BRK.B, FOX+FOXA).
_SP500_SYMBOLS: list[str] = [
    # --- Information Technology (51) ---
    "AAPL", "MSFT", "NVDA", "AVGO", "AMD", "ORCL", "ADBE", "CRM", "NOW", "CSCO",
    "QCOM", "TXN", "IBM", "AMAT", "LRCX", "KLAC", "MCHP", "CDNS", "SNPS", "PANW",
    "FTNT", "ADI", "MU", "APH", "TEL", "GLW", "KEYS", "TDY", "JNPR", "WDC",
    "STX", "NTAP", "HPE", "HPQ", "DELL", "CDW", "IT", "CTSH", "EPAM", "ACN",
    "GPN", "FISV", "FIS", "PYPL", "GDDY", "NET", "DDOG", "ANSS", "SMCI",
    "INTC", "ANET", "NXPI", "MPWR", "ZBRA", "TER", "SWKS", "QRVO", "AKAM",
    "FFIV", "VRSN", "TRMB", "ON", "IPGP",
    "CRWD", "ZS", "WDAY", "VEEV", "TEAM", "PAYC", "APP", "MKTX",
    # --- Communication Services (22) ---
    "GOOGL", "GOOG", "META", "NFLX", "DIS", "CMCSA", "CHTR", "TMUS", "VZ", "T",
    "NWSA", "NWS", "FOX", "FOXA", "PARA", "WBD", "LYV", "TTWO", "EA", "MTCH",
    "ZM", "SNAP", "OMC", "IPG",
    # --- Consumer Discretionary (60) ---
    "AMZN", "TSLA", "HD", "MCD", "BKNG", "LOW", "SBUX", "TJX", "NKE", "GM",
    "F", "APTV", "BWA", "LKQ", "GPC", "AZO", "ORLY", "TSCO", "DECK", "RL",
    "PVH", "TPR", "BBWI", "DRI", "YUM", "CMG", "HLT", "MAR", "WYNN", "MGM",
    "LVS", "CCL", "RCL", "NCLH", "DAL", "UAL", "LUV", "ALK", "AAL",
    "EBAY", "ETSY", "W", "ULTA", "DKS", "FIVE", "BBY", "DG", "DLTR", "TGT",
    "KSS", "JWN", "GPS", "FL", "GRMN", "HAS", "BURL", "MHK", "WHR",
    "POOL", "PHM", "NVR", "LEN", "TOL", "UBER", "ABNB", "CG", "KKR",
    # --- Consumer Staples (32) ---
    "WMT", "COST", "PG", "KO", "PEP", "PM", "MO", "MDLZ", "CL", "KMB",
    "GIS", "K", "SJM", "MKC", "HRL", "CAG", "CPB", "LW", "TSN", "MNST",
    "STZ", "TAP", "HSY", "CHD", "CLX", "EL", "WBA", "KHC", "INGR", "SFM",
    "KVUE", "BG",
    # --- Health Care (52) ---
    "LLY", "UNH", "JNJ", "MRK", "ABBV", "TMO", "ABT", "DHR", "AMGN", "BMY",
    "GILD", "VRTX", "REGN", "ISRG", "BSX", "MDT", "SYK", "EW", "IDXX", "DXCM",
    "HOLX", "BDX", "BAX", "ZBH", "HSIC", "RMD", "ALGN", "MTD", "RVTY",
    "IQV", "CRL", "TECH", "WAT", "MRNA", "BIIB", "HCA", "CI", "HUM",
    "CVS", "MOH", "CNC", "MCK", "CAH", "STE", "COO", "TFX", "PDCO",
    "VTRS", "OGN", "PKI", "GEHC", "DVA",
    # --- Financials (68) ---
    "BRK.B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "C", "AXP",
    "BLK", "SCHW", "CB", "AON", "MMC", "AJG", "TRV", "AFL", "PGR", "ALL",
    "MET", "PRU", "PFG", "LNC", "UNM", "GL", "CINF", "L", "AIG", "HIG",
    "USB", "PNC", "TFC", "FITB", "RF", "HBAN", "CFG", "MTB", "ZION", "KEY",
    "ALLY", "COF", "DFS", "SYF", "NDAQ", "ICE", "CME", "CBOE", "SPGI", "MCO",
    "WTW", "TROW", "BEN", "IVZ", "AMG", "BK", "STT", "NTRS", "FDS", "MSCI",
    "APO", "ACGL", "RNR", "AXS", "RE", "EG", "ORI", "FNF", "FAF", "RJF",
    "LPLA", "SEIC", "VOYA", "HRB",
    # --- Industrials (62) ---
    "GE", "HON", "RTX", "CAT", "DE", "ETN", "EMR", "PH", "ROK", "ITW",
    "MMM", "GWW", "FAST", "PCAR", "CTAS", "ADP", "PAYX", "EXPD", "CHRW", "XPO",
    "GXO", "UPS", "FDX", "NSC", "CSX", "UNP", "WAB", "TT", "CARR", "OTIS",
    "JCI", "GNRC", "HUBB", "AME", "ROP", "LDOS", "J", "STLD", "NUE",
    "RS", "MLM", "VMC", "IR", "AXON", "PWR", "JBHT", "SAIA", "KNX", "WERN",
    "R", "URI", "AL", "GATX", "TDG", "HII", "NOC", "LMT", "BA", "GD",
    "TXT", "ESAB", "CPRT", "RSG", "WM", "LHX", "HEI", "BLDR", "MAS", "LII",
    "AOS", "DOV", "NDSN", "FBIN",
    # --- Energy (28) ---
    "XOM", "CVX", "COP", "EOG", "MPC", "PSX", "VLO", "SLB", "BKR", "HAL",
    "DVN", "FANG", "MRO", "OXY", "CTRA", "APA", "EQT", "OKE", "WMB", "KMI",
    "TRGP", "LNG", "HES", "NOV", "CEG",
    # --- Materials (26) ---
    "LIN", "APD", "ECL", "SHW", "PPG", "IFF", "EMN", "CE", "HUN", "LYB",
    "DOW", "DD", "NEM", "FCX", "ALB", "MOS", "CF", "FMC", "PKG",
    "IP", "AMCR", "BALL", "WRK", "AVY", "ATI", "CMC",
    # --- Real Estate (30) ---
    "PLD", "WELL", "EQIX", "PSA", "EQR", "AVB", "O", "VICI", "SPG", "REG",
    "KIM", "FRT", "ESS", "UDR", "CPT", "IRM", "SBAC", "AMT", "CCI",
    "CBRE", "JLL", "VTR", "HST", "PEAK", "ARE", "BXP", "SUI", "ELS",
    "INVH", "NNN",
    # --- Utilities (27) ---
    "NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL", "WEC", "ES",
    "ETR", "EIX", "PPL", "DTE", "CNP", "NI", "ATO", "CMS", "LNT", "NRG",
    "PCG", "PNW", "EVRG", "AES", "AWK", "OGE", "WTR",
]

# Ensure no duplicates while preserving order
_seen: set[str] = set()
_unique: list[str] = []
for _sym in _SP500_SYMBOLS:
    if _sym not in _seen:
        _seen.add(_sym)
        _unique.append(_sym)
_SP500_SYMBOLS = _unique

TOP_10 = _SP500_SYMBOLS[:10]
TOP_100 = _SP500_SYMBOLS[:100]


def get_sp500() -> list[str]:
    return list(_SP500_SYMBOLS)


def get_top_n(n: int) -> list[str]:
    return _SP500_SYMBOLS[:n]
