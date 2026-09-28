"""Enterprise Customer & Invoice Database Generator.

Generates:
1. data/customers.csv & web/data/customers.json:
   Comprehensive enterprise CRM customer profiles for all 600+ real customers
   (including plan tier, monthly spend, ACV, SLA level, assigned account executive,
   billing country, payment method, contract renewal, industry, and address).

2. data/invoices.csv & web/data/invoices.json:
   Realistic multi-year invoice history linking back to customers, including
   exact matching for all invoice IDs referenced in customer support tickets.
"""

import csv
import json
import os
import random
import re
from datetime import datetime, timedelta

random.seed(42)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
WEB_DATA_DIR = os.path.join(BASE_DIR, "web", "data")
TICKETS_CSV = os.path.join(DATA_DIR, "customer_support_tickets_1000.csv")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(WEB_DATA_DIR, exist_ok=True)

# Account managers pool
ENTERPRISE_MANAGERS = [
    "Sarah Jenkins (VIP Lead)",
    "David Chen (Enterprise AE)",
    "Elena Rostova (Strategic Accounts)",
    "Marcus Brody (Director of CS)",
    "Sophia Al-Mansoor (VIP Partner Lead)",
    "Alexander Vance (Principal Executive Lead)",
]
PRO_MANAGERS = [
    "Growth Account Desk (US-East)",
    "Pro Support Tier 2 (EMEA)",
    "Customer Success Hub (APAC)",
    "Self-serve Pro Automated Lead",
]
FREE_MANAGERS = [
    "Community Tier Automated Bot",
    "Self-Serve (Unassigned)",
    "Community Support Forum",
]

COUNTRIES_CITIES = [
    ("US", "San Francisco, CA", "+1-415-555-"),
    ("US", "New York, NY", "+1-212-555-"),
    ("US", "Austin, TX", "+1-512-555-"),
    ("US", "Seattle, WA", "+1-206-555-"),
    ("UK", "London", "+44-20-7946-"),
    ("DE", "Berlin", "+49-30-555-"),
    ("DE", "Munich", "+49-89-555-"),
    ("JP", "Tokyo", "+81-3-555-"),
    ("FR", "Paris", "+33-1-455-"),
    ("CA", "Toronto, ON", "+1-416-555-"),
    ("SG", "Singapore", "+65-6555-"),
    ("AU", "Sydney, NSW", "+61-2-555-"),
    ("CH", "Zurich", "+41-44-555-"),
]

INDUSTRIES = [
    "Fintech & Payments",
    "Healthcare & Life Sciences",
    "Cloud Infrastructure & DevOps",
    "Enterprise Logistics & Supply Chain",
    "Cybersecurity & Identity",
    "Data Analytics & AI",
    "E-Commerce & Retail",
    "Biotechnology",
    "Media & Streaming",
    "Aerospace & Defense",
]

PAYMENT_METHODS = [
    "Visa ending 4242",
    "Visa ending 8819",
    "Mastercard ending 9182",
    "Mastercard ending 5012",
    "AMEX Corporate ending 1004",
    "AMEX Corporate ending 3091",
    "ACH Direct Corporate Transfer (Silicon Valley Bank)",
    "ACH Direct Corporate Transfer (JPMorgan Chase)",
    "Wire Transfer (SEPA / SWIFT Net 30)",
]

# Baseline core customers from test suite and mock data
SEED_CUSTOMERS = [
    {
        "customer_id": "CUST-001",
        "name": "Alice Smith",
        "email": "alice@acme-corp.com",
        "company": "Acme Corp Global",
        "tier": "pro",
        "industry": "Cloud Infrastructure & DevOps",
        "monthly_spend": 49.00,
        "annual_contract_value": 588.00,
        "account_manager": "Growth Account Desk (US-East)",
        "sla_level": "Priority Business (4h Business Hours SLA)",
        "joined_date": "2023-04-12",
        "renewal_date": "2025-04-12",
        "account_status": "active",
        "billing_country": "US",
        "billing_city": "San Francisco, CA",
        "phone": "+1-415-555-0192",
        "payment_method": "Visa ending 4242",
        "credit_balance": 0.00,
        "active_licenses": 10,
    },
    {
        "customer_id": "CUST-002",
        "name": "Bob Miller",
        "email": "bmiller@globalenterprise.io",
        "company": "GlobalEnterprise Holdings",
        "tier": "enterprise",
        "industry": "Fintech & Payments",
        "monthly_spend": 499.00,
        "annual_contract_value": 5988.00,
        "account_manager": "Sarah Jenkins (VIP Lead)",
        "sla_level": "Enterprise Critical (15min 24/7 SLA • 99.99% Uptime Guarantee)",
        "joined_date": "2022-01-15",
        "renewal_date": "2025-01-15",
        "account_status": "active",
        "billing_country": "US",
        "billing_city": "New York, NY",
        "phone": "+1-212-555-0833",
        "payment_method": "ACH Direct Corporate Transfer (JPMorgan Chase)",
        "credit_balance": 500.00,
        "active_licenses": 250,
    },
    {
        "customer_id": "CUST-003",
        "name": "Charlie Davis",
        "email": "charlie.d@gmail.com",
        "company": "Davis Independent Tech",
        "tier": "free",
        "industry": "Data Analytics & AI",
        "monthly_spend": 0.00,
        "annual_contract_value": 0.00,
        "account_manager": "Community Tier Automated Bot",
        "sla_level": "Standard Community (48h SLA)",
        "joined_date": "2024-02-20",
        "renewal_date": "2025-02-20",
        "account_status": "active",
        "billing_country": "US",
        "billing_city": "Austin, TX",
        "phone": "+1-512-555-0341",
        "payment_method": "None (Free Tier)",
        "credit_balance": 0.00,
        "active_licenses": 1,
    },
    {
        "customer_id": "CUST-004",
        "name": "Diana Prince",
        "email": "diana@themyscira-logistics.com",
        "company": "Themyscira Logistics Global",
        "tier": "pro",
        "industry": "Enterprise Logistics & Supply Chain",
        "monthly_spend": 250.00,
        "annual_contract_value": 3000.00,
        "account_manager": "Elena Rostova (Strategic Accounts)",
        "sla_level": "Priority Business (4h Business Hours SLA)",
        "joined_date": "2023-09-01",
        "renewal_date": "2024-09-01",
        "account_status": "churn_risk",
        "billing_country": "US",
        "billing_city": "Seattle, WA",
        "phone": "+1-206-555-0774",
        "payment_method": "Mastercard ending 9182",
        "credit_balance": 50.00,
        "active_licenses": 35,
    },
]


def extract_customer_info_from_tickets():
    """Extracts all unique customers and ticket invoice references from tickets CSV."""
    customers_map = {}
    invoices_from_tickets = []

    if not os.path.exists(TICKETS_CSV):
        print(f"Warning: {TICKETS_CSV} not found.")
        return customers_map, invoices_from_tickets

    with open(TICKETS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["customer_id"].strip().upper()
            if cid not in customers_map:
                customers_map[cid] = {
                    "customer_id": cid,
                    "name": row["customer_name"],
                    "email": row["customer_email"],
                    "company": row["customer_company"],
                    "tier": row["customer_tier"].lower(),
                    "has_churn_risk": row["churn_risk"].lower() == "true",
                }

            # Check if an invoice ID was mentioned in subject or message
            text = f"{row['subject']} {row['message']}"
            inv_matches = re.findall(r"INV-\d{4}-\d+", text)
            for inv_id in inv_matches:
                amount = float(row["disputed_amount"]) if row.get("disputed_amount") else (
                    49.0 if row["customer_tier"] == "pro" else 250.0
                )
                invoices_from_tickets.append({
                    "invoice_id": inv_id,
                    "customer_id": cid,
                    "customer_name": row["customer_name"],
                    "customer_company": row["customer_company"],
                    "amount": amount,
                    "date": row["timestamp"][:10],
                    "status": "disputed" if row.get("disputed_amount") else "paid",
                    "description": f"Subscription Renewal & Usage - {inv_id}",
                })

    return customers_map, invoices_from_tickets


def generate_full_customer_database():
    """Builds complete enterprise customer dataset and invoice history."""
    tickets_customers, referenced_invoices = extract_customer_info_from_tickets()

    all_customers = {}

    # 1. Insert seed customers
    for sc in SEED_CUSTOMERS:
        all_customers[sc["customer_id"]] = sc

    # 2. Populate and enrich all customers from tickets
    for cid, cdata in tickets_customers.items():
        if cid in all_customers:
            continue

        tier = cdata["tier"]
        country, city, phone_prefix = random.choice(COUNTRIES_CITIES)
        phone = f"{phone_prefix}{random.randint(1000, 9999)}"
        industry = random.choice(INDUSTRIES)

        # Joined date between 2021 and 2024
        days_ago = random.randint(60, 1100)
        joined_dt = datetime.now() - timedelta(days=days_ago)
        renewal_dt = joined_dt + timedelta(days=365 * 2)

        if tier == "enterprise":
            monthly = float(random.choice([499.00, 799.00, 1250.00, 2400.00, 4800.00]))
            acv = round(monthly * 12, 2)
            account_mgr = random.choice(ENTERPRISE_MANAGERS)
            sla = "Enterprise Critical (15min 24/7 SLA • 99.99% Uptime Guarantee)"
            pay_method = random.choice([
                "ACH Direct Corporate Transfer (Silicon Valley Bank)",
                "ACH Direct Corporate Transfer (JPMorgan Chase)",
                "Wire Transfer (SEPA / SWIFT Net 30)",
                "AMEX Corporate ending 1004",
            ])
            licenses = random.randint(50, 500)
            credit = float(random.choice([0.0, 250.0, 500.0, 1500.0]))
        elif tier == "pro":
            monthly = float(random.choice([49.00, 79.00, 99.00, 149.00, 250.00]))
            acv = round(monthly * 12, 2)
            account_mgr = random.choice(PRO_MANAGERS)
            sla = "Priority Business (4h Business Hours SLA)"
            pay_method = random.choice([
                "Visa ending 4242",
                "Visa ending 8819",
                "Mastercard ending 9182",
                "Mastercard ending 5012",
            ])
            licenses = random.randint(5, 30)
            credit = float(random.choice([0.0, 25.0, 50.0]))
        else:
            monthly = 0.00
            acv = 0.00
            account_mgr = random.choice(FREE_MANAGERS)
            sla = "Standard Community (48h SLA)"
            pay_method = "None (Free Community Tier)"
            licenses = 1
            credit = 0.00

        status = "churn_risk" if cdata.get("has_churn_risk") else random.choice(
            ["active", "active", "active", "renewal_pending"]
        )

        all_customers[cid] = {
            "customer_id": cid,
            "name": cdata["name"],
            "email": cdata["email"],
            "company": cdata["company"],
            "tier": tier,
            "industry": industry,
            "monthly_spend": monthly,
            "annual_contract_value": acv,
            "account_manager": account_mgr,
            "sla_level": sla,
            "joined_date": joined_dt.strftime("%Y-%m-%d"),
            "renewal_date": renewal_dt.strftime("%Y-%m-%d"),
            "account_status": status,
            "billing_country": country,
            "billing_city": city,
            "phone": phone,
            "payment_method": pay_method,
            "credit_balance": credit,
            "active_licenses": licenses,
        }

    # 3. Generate Invoices Database
    all_invoices = []
    seen_invoices = set()

    # Seed invoices
    seed_invoices = [
        {"invoice_id": "INV-2024-001", "customer_id": "CUST-001", "amount": 49.00, "date": "2024-05-01", "status": "paid", "description": "Pro Tier Monthly Subscription - May 2024"},
        {"invoice_id": "INV-2024-002", "customer_id": "CUST-001", "amount": 49.00, "date": "2024-06-01", "status": "paid", "description": "Pro Tier Monthly Subscription - June 2024"},
        {"invoice_id": "INV-2024-099", "customer_id": "CUST-004", "amount": 250.00, "date": "2024-06-05", "status": "disputed", "description": "Enterprise Add-on & Extra Compute Seats"},
        {"invoice_id": "INV-2024-501", "customer_id": "CUST-002", "amount": 499.00, "date": "2024-06-01", "status": "paid", "description": "Enterprise Tier Monthly Dedicated Node"},
    ]
    for sinv in seed_invoices:
        cinfo = all_customers.get(sinv["customer_id"], {})
        sinv["customer_name"] = cinfo.get("name", "Customer")
        sinv["customer_company"] = cinfo.get("company", "Company")
        sinv["currency"] = "USD"
        sinv["due_date"] = (datetime.strptime(sinv["date"], "%Y-%m-%d") + timedelta(days=30)).strftime("%Y-%m-%d")
        sinv["payment_method"] = cinfo.get("payment_method", "Visa ending 4242")
        all_invoices.append(sinv)
        seen_invoices.add(sinv["invoice_id"])

    # Add referenced invoices from tickets
    for rinv in referenced_invoices:
        if rinv["invoice_id"] in seen_invoices:
            continue
        cinfo = all_customers.get(rinv["customer_id"], {})
        rinv["currency"] = "USD"
        try:
            dt = datetime.strptime(rinv["date"], "%Y-%m-%d")
        except Exception:
            dt = datetime(2024, 6, 1)
        rinv["due_date"] = (dt + timedelta(days=30)).strftime("%Y-%m-%d")
        rinv["payment_method"] = cinfo.get("payment_method", "ACH Corporate Transfer")
        all_invoices.append(rinv)
        seen_invoices.add(rinv["invoice_id"])

    # Generate historical billing records for Pro and Enterprise customers
    for cid, cinfo in all_customers.items():
        tier = cinfo["tier"]
        if tier == "free":
            continue

        # Add 3 to 6 historical monthly invoices per paying customer
        num_invoices = random.randint(3, 6)
        monthly_val = cinfo["monthly_spend"]
        base_date = datetime(2024, 6, 1)

        for i in range(num_invoices):
            inv_date = base_date - timedelta(days=30 * i)
            inv_id = f"INV-2024-{random.randint(1000, 9999)}"
            while inv_id in seen_invoices:
                inv_id = f"INV-2024-{random.randint(1000, 9999)}"
            seen_invoices.add(inv_id)

            status = "paid"
            if i == 0 and cinfo["account_status"] == "renewal_pending":
                status = "open"

            all_invoices.append({
                "invoice_id": inv_id,
                "customer_id": cid,
                "customer_name": cinfo["name"],
                "customer_company": cinfo["company"],
                "amount": monthly_val,
                "currency": "USD",
                "date": inv_date.strftime("%Y-%m-%d"),
                "due_date": (inv_date + timedelta(days=30)).strftime("%Y-%m-%d"),
                "status": status,
                "description": f"{tier.upper()} Tier Subscription Service - {inv_date.strftime('%B %Y')}",
                "payment_method": cinfo["payment_method"],
            })

    # Sort customers and invoices
    sorted_customers = sorted(all_customers.values(), key=lambda x: x["customer_id"])
    sorted_invoices = sorted(all_invoices, key=lambda x: (x["customer_id"], x["date"]), reverse=True)

    print(f"Generated {len(sorted_customers)} enterprise customer profiles.")
    print(f"Generated {len(sorted_invoices)} customer invoice records.")

    # 4. Write CSV files
    cust_csv_path = os.path.join(DATA_DIR, "customers.csv")
    with open(cust_csv_path, "w", encoding="utf-8", newline="") as f:
        fieldnames = list(sorted_customers[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted_customers)
    print(f"Saved: {cust_csv_path}")

    inv_csv_path = os.path.join(DATA_DIR, "invoices.csv")
    with open(inv_csv_path, "w", encoding="utf-8", newline="") as f:
        fieldnames = list(sorted_invoices[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted_invoices)
    print(f"Saved: {inv_csv_path}")

    # 5. Write JSON for web app
    cust_json_path = os.path.join(WEB_DATA_DIR, "customers.json")
    with open(cust_json_path, "w", encoding="utf-8") as f:
        json.dump(sorted_customers, f, indent=2)
    print(f"Saved: {cust_json_path}")

    inv_json_path = os.path.join(WEB_DATA_DIR, "invoices.json")
    with open(inv_json_path, "w", encoding="utf-8") as f:
        json.dump(sorted_invoices, f, indent=2)
    print(f"Saved: {inv_json_path}")


if __name__ == "__main__":
    generate_full_customer_database()
