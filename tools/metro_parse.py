# -*- coding: utf-8 -*-
"""metro_parse.py -- turns Metro's "Order Book" PDF (LOGIDEC export) into a
compact JSON catalogue the app can use to recognise Metro-listed items.

Usage:  python3 metro_parse.py <order_book.pdf> <out.json>

Each product line in the book looks like:
  CODE(8)  UPC(5-13, no check digit)  DESCRIPTION  FORMAT  CASEPACK  NETCOST  RETAIL  [*]  MARGIN
Vendor header lines (10-digit vendor number) and category header lines
(5-digit category number) sit above the products they apply to.
"""
import re, sys, json, subprocess, datetime

pdf, out = sys.argv[1], sys.argv[2]
txt = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout
lines = [x.replace("\f", "") for x in txt.split("\n")]

# product pages start at the first "PRODUCT LIST" banner
start = next(i for i, l in enumerate(lines) if l.startswith("PRODUCT LIST"))
period = re.search(r"(\d{2}-\d{2}-\d{4})\s+to\s+(\d{2}-\d{2}-\d{4})", lines[start])

# Promo lines carry extra columns: rebate + end-date pairs ("0.56 07/08") after the
# case pack, and trailing promotion type / impact codes ("Z010 06"). Parse from
# the RIGHT so those never confuse the core fields.
PROMO_TAIL = re.compile(r"\s+(?:\d+-)?Z\d{3}(?:\s+\d{2}M?)?\s*$")
MONEY = r"[\d,]*\d\.\d{2}"          # costs >= $1,000 print with a comma (and sometimes lose the leading digit)
RETAIL = r"\d+/\d+\.\d{2}|\d+\.\d{2}"
PRICE_TAIL = re.compile(r"\s+(?P<cost>" + MONEY + r")\s+(?P<retail>" + RETAIL + r")\s*(?P<tax>[*A-Z])?\s*(?P<margin>\d+-?)?\s*$")
RETAIL_ONLY = re.compile(r"\s+(?P<retail>" + RETAIL + r")\s*(?P<tax>[*A-Z])?\s*(?P<margin>\d+-?)?\s*$")
COST_ONLY = re.compile(r"\s+(?P<cost>" + MONEY + r")\s*$")
REBATES = re.compile(r"(?:\s+\d+\.\d{2}(?:\s+\d{2}/\d{2})?)+\s*$")
PACK = re.compile(r"^(?P<body>.*?)\s+(?P<pck>\d+(?:,\d{3})*(?:[xX]\d+)?)\s*$")

def money(tok):
    """'82.68' -> 82.68 ; ',172.50' (leading digit lost to column overlap) -> None."""
    if tok is None or tok.startswith(","):
        return None
    return float(tok.replace(",", ""))

def parse_rest(rest):
    r = PROMO_TAIL.sub("", rest.rstrip())
    cost = retail = None; tax = ""
    m = PRICE_TAIL.search(r)
    if m:
        cost = money(m["cost"])
        retail = m["retail"] if "/" in m["retail"] else float(m["retail"])   # "2/5.50" = multi-buy
        tax = m["tax"] or ""      # "*" taxable; other letters are Metro tax-class flags, kept raw
        r = r[:m.start()]
    else:
        m = RETAIL_ONLY.search(r)
        if m:
            retail = m["retail"] if "/" in m["retail"] else float(m["retail"])
            tax = m["tax"] or ""
            r = r[:m.start()]
        else:
            m = COST_ONLY.search(r)
            if not m: return None
            cost = money(m["cost"]); r = r[:m.start()]
    r = REBATES.sub("", r).rstrip()
    pm = PACK.match(r)
    if not pm: return None
    return pm["body"].rstrip(), pm["pck"].replace(",", ""), cost, retail, tax

FMT = re.compile(r"^\d[\d.,]*(?:[xX]\d[\d.,]*)?(?:ml|l|g|kg|un|cl|oz|lb|ct|pk|ea)$", re.I)
VENDOR = re.compile(r"^\s+(\d{10})\s+(.+?)\s*$")
CATEG = re.compile(r"^\s+(\d{5})\s+(.+?)\s*$")
PRODUCT = re.compile(r"^(\d{8})\s+(?:(\d{5,13})\s+)?(.*)$")

vendors, cats = {}, {}
cur_v = cur_c = None
items, failed = [], []
for l in lines[start:]:
    if l.startswith("PRODUCT LIST") or l.strip().startswith(("Code ", "Date ")) or not l.strip():
        continue
    m = PRODUCT.match(l)
    if m:
        code, upc, rest = m.group(1), m.group(2) or "", m.group(3).rstrip()
        res = parse_rest(rest)
        if not res:
            failed.append(l); continue
        body, pck, cost, retail, tax = res
        fmt = ""
        parts = body.rsplit(None, 1)
        if len(parts) == 2 and FMT.match(parts[1]):
            body, fmt = parts[0].rstrip(), parts[1]
        items.append({
            "c": code, "u": upc, "d": body, "f": fmt, "p": pck,
            "n": cost, "r": retail, "t": tax,
            "v": cur_v, "k": cur_c,
        })
        continue
    mv = VENDOR.match(l)
    if mv:
        cur_v = mv.group(1); vendors[cur_v] = mv.group(2); continue
    mc = CATEG.match(l)
    if mc:
        cur_c = mc.group(1); cats[cur_c] = mc.group(2); continue

print("parsed:", len(items), " failed:", len(failed))
for f in failed[:15]: print("  FAIL:", repr(f[:170]))

# --- collapse to one entry per Metro code; vendors become "offers" -------------
# The same code is listed under several vendors with identical description / pack /
# UPC but sometimes DIFFERENT cost, so keep every (vendor, cost) offer.
by_code = {}
for i in items:
    e = by_code.setdefault(i["c"], {
        "c": i["c"], "u": i["u"], "d": i["d"], "f": i["f"], "p": i["p"],
        "r": i["r"], "t": i["t"], "o": [],
    })
    offer = [i["v"], i["n"]]
    if offer not in e["o"]:
        e["o"].append(offer)
    if e["r"] is None and i["r"] is not None:
        e["r"] = i["r"]
# cheapest known cost first, so offers[0] is the sensible default vendor
for e in by_code.values():
    e["o"].sort(key=lambda o: (o[1] is None, o[1] if o[1] is not None else 0))

used_vendors = {v for e in by_code.values() for v, _ in e["o"] if v}
catalog = {
    "v": 1,
    "period": [period.group(1), period.group(2)] if period else None,
    "built": datetime.date.today().isoformat(),
    "vendors": {v: vendors[v] for v in sorted(used_vendors) if v in vendors},
    "items": list(by_code.values()),
}
json.dump(catalog, open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("catalogue:", len(catalog["items"]), "codes,", len(catalog["vendors"]), "vendors")
