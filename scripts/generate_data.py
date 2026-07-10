"""Generate deterministic synthetic data for the Cabana Collection resort-analytics project.

Everything produced here is 100% synthetic (Faker) - no real, proprietary, or
personally identifiable data of any kind. The generator is seeded, so a fresh run
reproduces byte-identical CSVs; the CSVs are committed so `dbt build` works on a
clean clone without running this script.

The interesting bit: payments intentionally diverge from booked amounts (partial
pay, refunds, overpay, rounding) so the reconciliation mart has a real
booked-vs-recognized revenue variance to surface - the same class of problem the
author solved on the job, reproduced on synthetic data.

Run:  python scripts/generate_data.py
"""
import csv
import os
import random
from datetime import date, timedelta

from faker import Faker

SEED = 42
random.seed(SEED)
fake = Faker("en_US")
Faker.seed(SEED)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "data", "raw"))
os.makedirs(OUT, exist_ok=True)

N_RESORTS = 40
N_AGENTS = 60
N_GUESTS = 3000
N_BOOKINGS = 9000
START = date(2024, 1, 1)
END = date(2025, 12, 31)
SPAN_DAYS = (END - START).days

REGIONS = ["Caribbean", "Gulf Coast", "Pacific", "Mountain", "Mediterranean"]
# room_type -> (tier_rank, base nightly rate in dollars)
ROOM_TYPES = {
    "Standard King": (1, 180),
    "Standard Double": (1, 150),
    "Ocean Suite": (2, 350),
    "Villa": (3, 600),
    "Presidential": (4, 1200),
}
CHANNELS = ["Direct", "OTA", "Travel Agent", "Corporate", "Loyalty"]
CHANNEL_COMMISSION = {
    "Direct": 0.02, "OTA": 0.15, "Travel Agent": 0.10,
    "Corporate": 0.05, "Loyalty": 0.03,
}
LOYALTY = ["None", "Silver", "Gold", "Platinum"]
PAY_METHODS = ["Credit Card", "Debit Card", "Bank Transfer", "Points"]


def _id(prefix, i, width):
    return f"{prefix}{i:0{width}d}"


def _write(name, header, rows):
    path = os.path.join(OUT, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  wrote {name:16} {len(rows):>6} rows")


def gen_resorts():
    rows = []
    for i in range(1, N_RESORTS + 1):
        rows.append([
            _id("R", i, 4),
            f"Cabana {fake.city()}",
            fake.city(),
            fake.state_abbr(),
            "USA",
            random.choice(REGIONS),
            random.randint(80, 600),
            fake.date_between(date(2005, 1, 1), date(2022, 1, 1)).isoformat(),
        ])
    _write("resorts.csv",
           ["resort_id", "resort_name", "city", "state", "country",
            "region", "room_count", "opened_date"], rows)
    return [r[0] for r in rows]


def gen_agents():
    rows = []
    for i in range(1, N_AGENTS + 1):
        rows.append([
            _id("A", i, 4),
            fake.name(),
            fake.date_between(date(2015, 1, 1), date(2024, 6, 1)).isoformat(),
            random.choice(REGIONS),
            random.random() > 0.1,  # ~90% active
        ])
    _write("agents.csv",
           ["agent_id", "agent_name", "hire_date", "territory", "is_active"], rows)
    return [r[0] for r in rows]


def gen_guests():
    rows = []
    for i in range(1, N_GUESTS + 1):
        first, last = fake.first_name(), fake.last_name()
        rows.append([
            _id("G", i, 6),
            first, last,
            f"{first}.{last}.{i}@example.com".lower(),
            fake.country(),
            random.choices(LOYALTY, weights=[50, 25, 18, 7])[0],
            fake.date_time_between(date(2019, 1, 1), date(2024, 1, 1)).isoformat(sep=" "),
        ])
    _write("guests.csv",
           ["guest_id", "first_name", "last_name", "email",
            "country", "loyalty_tier", "created_at"], rows)
    return [r[0] for r in rows]


def gen_bookings_payments_commissions(resort_ids, agent_ids, guest_ids):
    bookings, payments, commissions = [], [], []
    pay_i = com_i = 0
    room_type_names = list(ROOM_TYPES.keys())

    for i in range(1, N_BOOKINGS + 1):
        bid = _id("B", i, 8)
        resort_id = random.choice(resort_ids)
        agent_id = random.choice(agent_ids)
        guest_id = random.choice(guest_ids)
        booking_date = START + timedelta(days=random.randint(0, SPAN_DAYS))
        lead = random.randint(1, 120)
        checkin = booking_date + timedelta(days=lead)
        nights = random.randint(1, 14)
        checkout = checkin + timedelta(days=nights)
        room_type = random.choices(room_type_names, weights=[35, 30, 20, 10, 5])[0]
        _, base_rate = ROOM_TYPES[room_type]
        nightly_rate_cents = int(base_rate * random.uniform(0.85, 1.35)) * 100
        booked_cents = nights * nightly_rate_cents
        channel = random.choices(CHANNELS, weights=[30, 30, 15, 15, 10])[0]
        status = random.choices(
            ["completed", "confirmed", "cancelled", "no_show"],
            weights=[70, 18, 9, 3])[0]

        bookings.append([
            bid, guest_id, resort_id, agent_id,
            booking_date.isoformat(), checkin.isoformat(), checkout.isoformat(),
            room_type, nights, nightly_rate_cents, booked_cents, channel, status,
        ])

        # --- payments: intentionally diverge from booked to create reconciliation variance ---
        pays = []  # (amount_cents, kind: settled|refunded|pending)
        if status == "cancelled":
            if random.random() < 0.6:  # charged then refunded -> nets ~0
                pays.append((booked_cents, "settled"))
                pays.append((-booked_cents, "refunded"))
            # else: never charged -> no payment rows (booked>0, recognized=0)
        elif status == "no_show":
            pays.append((booked_cents, "settled"))  # penalty, full charge
        else:  # completed / confirmed
            r = random.random()
            if r < 0.85:                      # clean full settlement
                pays.append((booked_cents, "settled"))
            elif r < 0.93:                    # partial pay (deposit only)
                paid = int(booked_cents * random.uniform(0.4, 0.8))
                pays.append((paid, "settled"))
                pays.append((booked_cents - paid, "pending"))
            elif r < 0.97:                    # rounding / minor overpay
                pays.append((booked_cents + random.randint(1, 5000), "settled"))
            else:                             # settled then partial refund
                pays.append((booked_cents, "settled"))
                pays.append((-int(booked_cents * random.uniform(0.1, 0.3)), "refunded"))

        for amt, kind in pays:
            pay_i += 1
            pay_date = checkin + timedelta(days=random.randint(-30, 5)) if kind != "refunded" \
                else checkout + timedelta(days=random.randint(1, 20))
            payments.append([
                _id("P", pay_i, 8), bid, pay_date.isoformat(),
                amt, random.choice(PAY_METHODS), kind,
            ])

        # --- commission on booked amount (a few injected mismatches for a data-quality test) ---
        com_i += 1
        rate = CHANNEL_COMMISSION[channel]
        amount = int(booked_cents * rate)
        if random.random() < 0.02:            # 2% recorded wrong -> test should flag drift
            amount = int(amount * random.uniform(1.1, 1.4))
        commissions.append([_id("C", com_i, 8), bid, agent_id, rate, amount])

    _write("bookings.csv",
           ["booking_id", "guest_id", "resort_id", "agent_id", "booking_date",
            "checkin_date", "checkout_date", "room_type", "nights",
            "nightly_rate_cents", "booked_amount_cents", "channel", "status"], bookings)
    _write("payments.csv",
           ["payment_id", "booking_id", "payment_date", "amount_cents",
            "payment_method", "payment_status"], payments)
    _write("commissions.csv",
           ["commission_id", "booking_id", "agent_id",
            "commission_rate", "commission_amount_cents"], commissions)


def main():
    print(f"Generating synthetic data -> {OUT}")
    resort_ids = gen_resorts()
    agent_ids = gen_agents()
    guest_ids = gen_guests()
    gen_bookings_payments_commissions(resort_ids, agent_ids, guest_ids)
    print("Done.")


if __name__ == "__main__":
    main()
