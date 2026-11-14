"""Flight price tracker: STL -> STT. Pulls prices daily, logs them, builds an Excel workbook, emails on drops."""
import argparse, csv, json, os, smtplib, ssl, sys, random
from datetime import date
from email.message import EmailMessage
from html import escape
from pathlib import Path
import requests
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.chart import LineChart, Reference
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).parent
HISTORY = ROOT / "data" / "price_history.csv"
WORKBOOK = ROOT / "data" / "Flight_Price_Tracker.xlsx"
FIELDS = ["date", "window", "airline", "cabin", "price_total", "price_per_person", "booking_note", "link"]
API = "https://serpapi.com/search.json"


def load_config():
    return json.loads((ROOT / "config.json").read_text())


def acceptable(option, airline_code_name):
    """No overnight layovers, no overnight flight legs, and every leg flown by the chosen airline."""
    if any(l.get("overnight") for l in option.get("layovers", [])):
        return False
    for leg in option.get("flights", []):
        if leg.get("overnight"):
            return False
        if airline_code_name.lower() not in (leg.get("airline") or "").lower():
            return False
    return True


def fetch_live(cfg, win, airline, code, cabin, cabin_code, key):
    params = {"engine": "google_flights", "departure_id": cfg["origin"], "arrival_id": cfg["destination"],
              "outbound_date": win["outbound"], "return_date": win["return"], "type": 1,
              "adults": cfg["adults"], "travel_class": cabin_code, "include_airlines": code,
              "currency": cfg["currency"], "hl": "en", "api_key": key}
    r = requests.get(API, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    options = (data.get("best_flights") or []) + (data.get("other_flights") or [])
    good = [o for o in options if o.get("price") and acceptable(o, airline)]
    if not good:
        return None
    best = min(good, key=lambda o: o["price"])
    link = data.get("search_metadata", {}).get("google_flights_url", "")
    return best["price"], link


def fetch_mock(cfg, win, airline, code, cabin, cabin_code, key, today):
    rnd = random.Random(f"{win['label']}{airline}{cabin}")
    base = 2200 if cabin_code == 3 else 6800
    price = base + rnd.randint(-150, 150) + (150 if airline == "American" else 0)
    day = (today - date(2026, 11, 1)).days
    if day >= 3:
        price = int(price * 0.88)  # simulated holiday drop
    return price, "mock-data"


def read_history():
    if not HISTORY.exists():
        return []
    with HISTORY.open() as f:
        return list(csv.DictReader(f))


def write_history(rows):
    HISTORY.parent.mkdir(exist_ok=True)
    with HISTORY.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def previous_price(rows, new):
    prior = [r for r in rows if r["window"] == new["window"] and r["airline"] == new["airline"]
             and r["cabin"] == new["cabin"] and r["date"] < new["date"]]
    return float(max(prior, key=lambda r: r["date"])["price_total"]) if prior else None


def series_for(rows, r):
    """All logged prices (oldest first) for the same window, airline and cabin as row r, up to and including r's date."""
    same = [x for x in rows if x["window"] == r["window"] and x["airline"] == r["airline"]
            and x["cabin"] == r["cabin"] and x["date"] <= r["date"]]
    return [float(x["price_total"]) for x in sorted(same, key=lambda x: x["date"])]


def trend_stats(rows, r):
    """Returns (lowest_so_far, amount_above_lowest, avg_7day or None, pct_vs_avg or None)."""
    prices = series_for(rows, r)
    p = prices[-1]
    lowest = min(prices)
    avg = sum(prices[-7:]) / 7 if len(prices) >= 7 else None
    return lowest, p - lowest, avg, (p / avg - 1) if avg else None


def trend_phrase(rows, r):
    """Up or down versus the 7-day average, or None until 7 days of data exist for this fare."""
    _, _, avg, pct = trend_stats(rows, r)
    if avg is None:
        return None
    n = round(abs(pct) * 100)
    if n == 0:
        return "about the same as its 7-day average"
    return f"{n}% {'above' if pct > 0 else 'below'} its 7-day average"


def build_workbook(rows, cfg):
    wb = Workbook()
    hdr_fill = PatternFill("solid", fgColor="374151")
    def style_header(ws, ncol):
        for c in range(1, ncol + 1):
            cell = ws.cell(1, c)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = hdr_fill
            cell.alignment = Alignment(horizontal="center", wrap_text=True)
        ws.freeze_panes = "A2"
    ws = wb.active
    ws.title = "Price Log"
    ws.append(["Date checked", "Date window", "Airline", "Cabin", "Total price (all travelers)", "Price per person",
               "Prior price", "Change ($)", "Change (%)", "Drop alert", "Source note"])
    style_header(ws, 11)
    srt = sorted(rows, key=lambda r: (r["date"], r["window"], r["airline"], r["cabin"]))
    thr = cfg["drop_threshold_pct"] / 100
    for r in srt:
        prior = previous_price(srt, r)
        p = float(r["price_total"])
        chg = p - prior if prior else None
        pct = chg / prior if prior else None
        ws.append([r["date"], r["window"], r["airline"], r["cabin"], p, float(r["price_per_person"]), prior, chg, pct,
                   "DROP" if pct is not None and pct <= -thr else "", r["booking_note"]])
    for row in ws.iter_rows(min_row=2):
        for i in (4, 5, 6, 7):
            row[i].number_format = "$#,##0;($#,##0);-"
        row[8].number_format = "0.0%"
        if row[9].value == "DROP":
            row[9].fill = PatternFill("solid", fgColor="C6F6D5")
            row[9].font = Font(bold=True, color="14532D")
    for i, w in enumerate([14, 17, 12, 17, 18, 16, 13, 13, 12, 12, 22], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    s = wb.create_sheet("Summary")
    s.append(["Date window", "Airline", "Cabin", "Latest check", "Latest price", "Lowest price so far",
              "Highest price", "Latest vs lowest (%)", "Amount above lowest ($)", "7-day average price",
              "Latest vs 7-day average (%)", "Checks logged"])
    style_header(s, 12)
    combos = sorted({(r["window"], r["airline"], r["cabin"]) for r in rows})
    for w_, a, c in combos:
        sel = sorted([r for r in rows if (r["window"], r["airline"], r["cabin"]) == (w_, a, c)], key=lambda r: r["date"])
        prices = [float(r["price_total"]) for r in sel]
        lowest, above, avg, pct = trend_stats(rows, sel[-1])
        s.append([w_, a, c, sel[-1]["date"], prices[-1], lowest, max(prices), prices[-1] / lowest - 1, above,
                  avg if avg is not None else "Needs 7 days", pct if pct is not None else "Needs 7 days", len(sel)])
    for row in s.iter_rows(min_row=2):
        for i in (4, 5, 6, 8, 9):
            row[i].number_format = "$#,##0"
        row[7].number_format = "0.0%"
        row[10].number_format = "0.0%"
        row[8].number_format = "$#,##0"
        row[9].number_format = "$#,##0"
    for i, w in enumerate([17, 12, 17, 14, 14, 16, 14, 16, 18, 16, 20, 12], 1):
        s.column_dimensions[get_column_letter(i)].width = w
    s.row_dimensions[1].height = 45
    t = wb.create_sheet("Price Trend")
    dates = sorted({r["date"] for r in rows})
    names = [f"{c[1]} {c[2]}, {c[0].split(',')[0]}" for c in combos]
    t.append(["Date"] + names)
    style_header(t, len(names) + 1)
    lookup = {(r["date"], r["window"], r["airline"], r["cabin"]): float(r["price_total"]) for r in rows}
    for d in dates:
        t.append([d] + [lookup.get((d,) + c) for c in combos])
    for row in t.iter_rows(min_row=2):
        for cell in row[1:]:
            cell.number_format = "$#,##0"
    t.column_dimensions["A"].width = 14
    for i in range(2, len(names) + 2):
        t.column_dimensions[get_column_letter(i)].width = 24
    t.row_dimensions[1].height = 45
    ch = LineChart()
    ch.title = "Daily price by fare"
    ch.y_axis.title = "Total price, 2 travelers ($)"
    ch.x_axis.title = "Date checked"
    ch.y_axis.number_format = "$#,##0"
    ch.add_data(Reference(t, min_col=2, max_col=len(names) + 1, min_row=1, max_row=len(dates) + 1), titles_from_data=True)
    ch.set_categories(Reference(t, min_col=1, min_row=2, max_row=len(dates) + 1))
    ch.height, ch.width = 9, 22
    t.add_chart(ch, f"A{len(dates) + 4}")
    wb.save(WORKBOOK)


def send_email(subject, body, attach, html=None):
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    user, pwd, to = os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"], os.environ["ALERT_EMAIL"]
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, user, to
    msg.set_content(body)
    if html:
        msg.add_alternative(html, subtype="html")
    if attach and attach.exists():
        msg.add_attachment(attach.read_bytes(), maintype="application",
                           subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=attach.name)
    with smtplib.SMTP(host, 587, timeout=30) as s:
        s.starttls(context=ssl.create_default_context())
        s.login(user, pwd)
        s.send_message(msg)


def build_message(today, new_rows, cfg, all_rows):
    """Friendly automated alert email: returns (plain_text, html)."""
    date_text = f"{today.strftime('%B')} {today.day}, {today.year}"
    text_lines, html_lines = [], []
    for win in cfg["date_windows"]:
        items = sorted([r for r in new_rows if r["window"] == win["label"]], key=lambda r: (r["airline"], r["cabin"]))
        if not items:
            continue
        label = win["label"].split(",")[0]
        names = [f"{r['airline']} {r['cabin']} ${float(r['price_total']):,.0f}" for r in items]
        text_lines.append(f"{label}: " + ", ".join(names))
        links = [f'<a href="{escape(r["link"], quote=True)}">{n}</a>' if r.get("link") else n
                 for r, n in zip(items, names)]
        html_lines.append(f"{label}: " + ", ".join(links))
    trend_items = []
    for win in cfg["date_windows"]:
        for r in sorted([r for r in new_rows if r["window"] == win["label"]], key=lambda r: (r["airline"], r["cabin"])):
            phrase = trend_phrase(all_rows, r)
            if phrase:
                trend_items.append(f"{r['airline']} {r['cabin']}, {win['label'].split(',')[0]}: {phrase}")
    trend_wait = ("The attached file shows each day's price change, in dollars and percent. After 7 days of tracking, "
                  "we'll share the overall trend (up or down) here.")
    trend_intro = "Compared with each fare's average over the last 7 days:"
    parts = []
    if cfg.get("target_price_total"):
        parts.append(f"a fare is ${cfg['target_price_total']:,.0f} or less for {cfg['adults']} travelers")
    parts.append(f"a price drops {cfg['drop_threshold_pct']:g}% or more from the day before")
    level = "You'll get this email whenever " + ", or when ".join(parts) + "."
    cabins_found = {r["cabin"] for r in new_rows}
    why = ""
    if "Premium Economy" not in cabins_found:
        why = ("Right now, only Business fares are showing for these flights. Premium Economy isn't being offered "
               "on this route for your dates. If it becomes available, it will appear in this email automatically.")
    head = "This is an automated email from your flight price tracker."
    intro = f"Good news, your fares are in. Here's what we found for St. Louis to St. Thomas today, {date_text}."
    workbook = "The attached workbook shows how each price has moved."
    check_q = "Does the price look right?"
    check_a = "Head to the airline's website now, because fares can change several times throughout the day."
    stop_q = "To stop these emails,"
    stop_a = " reply to this email and Robin will turn them off."
    text = [head, "", intro, ""] + [f"- {l}" for l in text_lines] + ["", "Your alert level: " + level, ""]
    if trend_items:
        text += ["Pricing trend: " + trend_intro] + [f"- {t}" for t in trend_items] + [""]
    else:
        text += ["Pricing trend: " + trend_wait, ""]
    if why:
        text += ["Why only Business? " + why, ""]
    text += [workbook, "", f"{check_q} {check_a}", "", stop_q + stop_a]
    html = [f"<p><b>{head}</b></p>", f"<p>{intro}</p>", "<ul>" + "".join(f"<li>{l}</li>" for l in html_lines) + "</ul>",
            f"<p><b>Your alert level:</b> {level}</p>"]
    if trend_items:
        html.append(f"<p><b>Pricing trend:</b> {trend_intro}</p><ul>" + "".join(f"<li>{t}</li>" for t in trend_items) + "</ul>")
    else:
        html.append(f"<p><b>Pricing trend:</b> {trend_wait}</p>")
    if why:
        html.append(f"<p><b>Why only Business?</b> {why}</p>")
    html += [f"<p>{workbook}</p>", f"<p><b>{check_q}</b> {check_a}</p>", f"<p><b>{stop_q}</b>{stop_a}</p>"]
    return "\n".join(text), "".join(html)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="use fake prices (no API key needed)")
    ap.add_argument("--no-email", action="store_true", help="print alerts instead of emailing")
    ap.add_argument("--date", help="override today's date (YYYY-MM-DD), for testing")
    a = ap.parse_args()
    cfg = load_config()
    today = date.fromisoformat(a.date) if a.date else date.today()
    key = os.environ.get("SERPAPI_KEY")
    if not a.mock and not key:
        sys.exit("Set SERPAPI_KEY (or use --mock).")
    rows = [r for r in read_history() if r["date"] != today.isoformat()]  # rerun-safe
    new_rows, failures = [], []
    for win in cfg["date_windows"]:
        for airline, code in cfg["airlines"].items():
            for cabin, ccode in cfg["cabins"].items():
                try:
                    res = fetch_mock(cfg, win, airline, code, cabin, ccode, key, today) if a.mock \
                        else fetch_live(cfg, win, airline, code, cabin, ccode, key)
                except Exception as e:
                    failures.append(f"{win['label']} {airline} {cabin}: {e}")
                    continue
                if res is None:
                    print(f"No qualifying fare: {win['label']} {airline} {cabin}")
                    continue
                total, link = res
                if not cfg["price_is_total_for_all_travelers"]:
                    total *= cfg["adults"]
                new_rows.append({"date": today.isoformat(), "window": win["label"], "airline": airline, "cabin": cabin,
                                 "price_total": round(total, 2), "price_per_person": round(total / cfg["adults"], 2),
                                 "booking_note": "Google Flights data (SerpApi)" if not a.mock else "mock",
                                 "link": link})
    alerts = []
    for n in new_rows:
        prior = previous_price(rows, n)
        p = n["price_total"]
        if prior and (p - prior) / prior <= -cfg["drop_threshold_pct"] / 100:
            alerts.append(f"DROP  {n['window']} | {n['airline']} {n['cabin']}: ${prior:,.0f} -> ${p:,.0f} ({(p-prior)/prior:.1%})")
        elif cfg.get("target_price_total") and p <= cfg["target_price_total"]:
            alerts.append(f"TARGET {n['window']} | {n['airline']} {n['cabin']}: ${p:,.0f}")
    rows += new_rows
    write_history(rows)
    if rows:
        build_workbook(rows, cfg)
    print(f"Logged {len(new_rows)} prices for {today}.")
    if failures:
        print("Failures:\n" + "\n".join(failures))
    if alerts:
        body, html = build_message(today, new_rows, cfg, rows)
        if a.no_email:
            print(body)
        else:
            send_email("Automated flight price alert: STL to STT, April 2027", body, WORKBOOK, html)
            print("Alert email sent.")
    if failures and len(failures) == len(cfg["date_windows"]) * len(cfg["airlines"]) * len(cfg["cabins"]) and not a.no_email and not a.mock:
        send_email("Flight tracker: all lookups failed", "\n".join(failures), None)


if __name__ == "__main__":
    main()
