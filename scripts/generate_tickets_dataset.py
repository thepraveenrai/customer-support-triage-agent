"""Enterprise Customer Support Ticket Dataset Generator.

Generates 1,000+ realistic, non-dummy customer support tickets across Billing,
Technical, and Escalation categories, mirroring real-world SaaS enterprise operations.
Zero placeholder text (no 'Lorem Ipsum' or 'Ticket #123').
"""

import csv
import os
import random
from datetime import datetime, timedelta

random.seed(42)

# ==============================================================================
# Realistic Entity Pools
# ==============================================================================

FIRST_NAMES = [
    "Alexander", "Elena", "Marcus", "Priya", "Chen", "Liam", "Sofia", "Takashi",
    "Aisha", "David", "Emma", "Lucas", "Fatima", "Dmitri", "Hannah", "Mateo",
    "Ananya", "Carlos", "Chloe", "Arjun", "Zara", "Benjamin", "Yuki", "Amira",
    "Gabriel", "Olga", "Nathan", "Leila", "Siddharth", "Camila", "Viktor", "Mei",
    "Daniel", "Nadia", "Kavita", "Julian", "Fatou", "Tariq", "Sergei", "Isabella",
    "Kwame", "Min-jun", "Chiara", "Rohan", "Beatriz", "Henrik", "Sora", "Astrid",
    "Devon", "Rachel", "Omar", "Ingrid", "Sven", "Zubair", "Thalia", "Kiran"
]

LAST_NAMES = [
    "Vance", "Rostova", "Sharma", "Wei", "O'Connor", "Rodriguez", "Tanaka",
    "Al-Mansoor", "Jenkins", "Kowalski", "Dubois", "Patel", "Lindqvist", "Nakamura",
    "Gomez", "Muller", "Novak", "Kaufman", "Mercer", "Sinclair", "Sterling",
    "Blackwood", "Fontaine", "Svensson", "Castillo", "Moretti", "Morales", "Bauer",
    "Schneider", "Ivanov", "Chowdhury", "Popov", "Larsson", "Bhatia", "Vargas",
    "Hassan", "Ferrari", "Park", "Kim", "Gupta", "Nielsen", "Decker", "Hawthorne"
]

COMPANIES = [
    ("NovaFin Technologies", "novafin.io"),
    ("Apex Logistics Global", "apexlogistics.com"),
    ("MedPulse Health Systems", "medpulse.health"),
    ("CloudScale Infrastructure", "cloudscale.de"),
    ("DataStream Analytics", "datastream.ai"),
    ("QuantumPay Solutions", "quantumpay.com"),
    ("Vertex AI Labs", "vertexlabs.io"),
    ("BioGenetics Global", "biogenetics.org"),
    ("Aurora Media Group", "auroramedia.co.uk"),
    ("Horizon Retail Network", "horizonretail.com"),
    ("CyberShield Security", "cybershield.net"),
    ("Starlight E-Commerce", "starlightshop.com"),
    ("OmniCorp Supply Chain", "omnicorp.io"),
    ("Krypton Capital Partners", "kryptoncap.com"),
    ("Zion Cloud Services", "zioncloud.tech"),
    ("Nordic Freight Solutions", "nordicfreight.se"),
    ("Pacific Rim Trading", "pacificrim.jp"),
    ("Atlas Autonomous Systems", "atlasauto.ai"),
    ("Vanguard Aerospace", "vanguardaero.com"),
    ("Helios Clean Energy", "heliosenergy.com"),
    ("Synergy Workspace", "synergywork.io"),
    ("Echo Payments Inc", "echopay.co"),
    ("Nexus Healthcare Platform", "nexushealth.io"),
    ("Strata Geotechnical", "stratageo.com"),
    ("Beacon Real Estate Tech", "beaconprop.io"),
]

# ==============================================================================
# Ticket Scenarios & Templates
# ==============================================================================

BILLING_SCENARIOS = [
    # Routine / Small (<= $50) -> Auto-resolved
    {
        "subject": "Question regarding charge {inv_id} for ${amount:.2f}",
        "message": "Hi team, I noticed invoice {inv_id} for ${amount:.2f} on our company credit card this morning. Could you clarify whether this covers our Pro subscription renewal or additional user seats? Thanks!",
        "amount_range": (15.0, 49.0),
        "sentiment": "NEUTRAL",
        "priority": "LOW",
        "churn_risk": False,
        "requires_human": False,
    },
    {
        "subject": "Accidental duplicate subscription payment ({inv_id})",
        "message": "Hello, it appears our billing system was charged twice for the monthly plan yesterday (${amount:.2f} each, reference {inv_id}). Could you please verify and refund the duplicate payment? Thank you!",
        "amount_range": (29.0, 49.0),
        "sentiment": "NEUTRAL",
        "priority": "MEDIUM",
        "churn_risk": False,
        "requires_human": False,
    },
    {
        "subject": "Forgot to cancel trial before renewal - refund request",
        "message": "Hi support, I was testing your platform last week but forgot to cancel the trial before it converted today. I was charged ${amount:.2f}. We haven't used any API credits since renewal. Would it be possible to get a refund? Appreciate your understanding.",
        "amount_range": (20.0, 49.0),
        "sentiment": "NEUTRAL",
        "priority": "LOW",
        "churn_risk": False,
        "requires_human": False,
    },
    {
        "subject": "VAT / Tax invoice request for {inv_id}",
        "message": "Hello accounts department, our finance team needs an updated VAT/Tax breakdown invoice for {inv_id} showing our European VAT ID (EU88492019). Could you please regenerate the receipt? Thanks.",
        "amount_range": (30.0, 50.0),
        "sentiment": "NEUTRAL",
        "priority": "LOW",
        "churn_risk": False,
        "requires_human": False,
    },
    # Large / Disputed (> $50) -> HITL Triggered
    {
        "subject": "UNAUTHORIZED CHARGE of ${amount:.2f} - Immediate Refund Required!",
        "message": "THIS IS UNACCEPTABLE! You billed our corporate card ${amount:.2f} for invoice {inv_id} without any notification or approval! I demand an immediate refund of ${amount:.2f} or I will dispute this charge with American Express as fraudulent and cancel our company account today.",
        "amount_range": (150.0, 950.0),
        "sentiment": "ANGRY",
        "priority": "HIGH",
        "churn_risk": True,
        "requires_human": True,
    },
    {
        "subject": "Charged for 20 extra seats we never provisioned ({inv_id})",
        "message": "We were billed ${amount:.2f} on invoice {inv_id} for additional team licenses. Our admin audit logs show our team size has not changed since March. We request a full reversal of ${amount:.2f}. Please have a billing manager review this ASAP.",
        "amount_range": (200.0, 1200.0),
        "sentiment": "FRUSTRATED",
        "priority": "HIGH",
        "churn_risk": True,
        "requires_human": True,
    },
    {
        "subject": "Annual Enterprise renewal dispute - ${amount:.2f}",
        "message": "Our contract explicitly stated a 60-day opt-out window before auto-renewal. Your team billed our account ${amount:.2f} for invoice {inv_id} despite our written notice sent on May 10th. We require immediate cancellation and credit memo issued.",
        "amount_range": (1200.0, 4800.0),
        "sentiment": "ANGRY",
        "priority": "CRITICAL",
        "churn_risk": True,
        "requires_human": True,
    },
    {
        "subject": "Dispute regarding overage compute fees (${amount:.2f})",
        "message": "Hello, our latest invoice {inv_id} includes ${amount:.2f} in compute overage charges. We believe this was caused by an infinite loop in your webhook retry handler rather than our queries. We request a courtesy credit or fee waiver.",
        "amount_range": (75.0, 350.0),
        "sentiment": "FRUSTRATED",
        "priority": "MEDIUM",
        "churn_risk": False,
        "requires_human": True,
    },
]

TECHNICAL_SCENARIOS = [
    {
        "subject": "HTTP 503 Service Unavailable on /v2/sync pipeline",
        "message": "Our automated data sync worker has been failing with HTTP 503 since 14:20 UTC. Log snippet:\n`HTTP 503: upstream worker pool exhausted on partition sync`\nIs there an active service outage on the US-East-1 data sync cluster? We are blocked on client ETL.",
        "sentiment": "FRUSTRATED",
        "priority": "HIGH",
        "churn_risk": False,
        "requires_human": False,
    },
    {
        "subject": "API Rate Limit 429 Too Many Requests on batch endpoint",
        "message": "Hello, our production scraper is receiving HTTP 429 errors on `POST /v1/batch/process` even though our dashboard shows we have only consumed 45% of our monthly tier quota. What is the per-minute burst rate limit on this endpoint?",
        "sentiment": "NEUTRAL",
        "priority": "MEDIUM",
        "churn_risk": False,
        "requires_human": False,
    },
    {
        "subject": "SAML SSO Okta authentication failure for new team members",
        "message": "Hi, three of our new engineers are unable to log in through Okta SAML. They receive error `Invalid SAML assertion: signature verification failed (code 4001)`. Our Okta certificate is valid until 2027. Can you check your Identity Provider metadata sync?",
        "sentiment": "FRUSTRATED",
        "priority": "HIGH",
        "churn_risk": False,
        "requires_human": False,
    },
    {
        "subject": "Python SDK ImportError on version 2.4.1 upgrade",
        "message": "After upgrading to `langgraph-agent-sdk==2.4.1`, our pipeline fails on startup with `ImportError: cannot import name 'AsyncCheckpointer' from 'langgraph_sdk'`. Is this a breaking change or missing dependency in the wheel?",
        "sentiment": "NEUTRAL",
        "priority": "LOW",
        "churn_risk": False,
        "requires_human": False,
    },
    {
        "subject": "Webhook delivery failure: HMAC signature mismatch",
        "message": "Our receiving endpoint is rejecting your event webhooks with `401 Unauthorized`. We verified our webhook secret matches the dashboard. Did you update the hashing algorithm from SHA-256 to SHA-512 in the latest release?",
        "sentiment": "NEUTRAL",
        "priority": "MEDIUM",
        "churn_risk": False,
        "requires_human": False,
    },
    {
        "subject": "CORS preflight error on browser client integration",
        "message": "We are attempting to query the status API directly from our React dashboard, but Chrome blocks the request: `Access-Control-Allow-Origin header missing in preflight OPTIONS request`. How do we whitelist our domain `app.novafin.io`?",
        "sentiment": "NEUTRAL",
        "priority": "LOW",
        "churn_risk": False,
        "requires_human": False,
    },
    {
        "subject": "Postgres connector latency spike (>8000ms)",
        "message": "Our telemetry monitors are alerting on database query latency on your managed Postgres connector. Latency jumped from 45ms to 8,200ms at 18:00 UTC. Could you check if connection pooling or read-replica failover occurred?",
        "sentiment": "FRUSTRATED",
        "priority": "HIGH",
        "churn_risk": False,
        "requires_human": False,
    },
    {
        "subject": "How to generate and rotate secondary API keys?",
        "message": "Hi team, we are conducting a security audit and need to rotate all production API keys without causing downtime for our active workers. Does your API support dual-key verification during key rotation?",
        "sentiment": "NEUTRAL",
        "priority": "LOW",
        "churn_risk": False,
        "requires_human": False,
    },
]

ESCALATION_SCENARIOS = [
    {
        "subject": "URGENT: Enterprise 99.99% SLA Breach - Emergency Call Demanded",
        "message": "This is {name}, VP of Engineering at {company}. Your platform has been down for 95 minutes during our peak trading window, directly violating Section 4.2 of our Enterprise SLA (99.99% uptime). I need an emergency bridge with your VP of Engineering and our account manager within 30 minutes, or we will initiate contract termination.",
        "sentiment": "ANGRY",
        "priority": "CRITICAL",
        "churn_risk": True,
        "requires_human": True,
    },
    {
        "subject": "LEGAL NOTICE: Contract Breach & Notice of Litigation",
        "message": "Notice to Customer Support & Legal Department: Due to unmitigated data loss during your database migration yesterday, {company} has suffered severe commercial damages. Our legal counsel has instructed us to demand preservation of all server logs, audit trails, and internal communications. Litigation will commence unless resolved within 48 hours.",
        "sentiment": "ANGRY",
        "priority": "CRITICAL",
        "churn_risk": True,
        "requires_human": True,
    },
    {
        "subject": "Formal GDPR Article 17 Data Erasure Request (Right to be Forgotten)",
        "message": "Official GDPR Compliance Request: Pursuant to Article 17 of the EU General Data Protection Regulation, {company} formally requests the permanent deletion of all telemetry and user data associated with customer ID {cust_id}. Please provide confirmation of deletion and an audit certificate signed by your DPO within 30 days.",
        "sentiment": "NEUTRAL",
        "priority": "HIGH",
        "churn_risk": False,
        "requires_human": True,
    },
    {
        "subject": "Executive Escalation: Unresponsive Support on Sev-1 Production Outage",
        "message": "I am the CTO of {company}. We opened a Sev-1 ticket 3 hours ago regarding our broken payment checkout and have received only automated bot replies. We pay $1,500/month for 15-minute priority SLA. Escalate this to senior leadership immediately or we are migrating our infrastructure to your competitor.",
        "sentiment": "ANGRY",
        "priority": "CRITICAL",
        "churn_risk": True,
        "requires_human": True,
    },
    {
        "subject": "SOC 2 Type II Report & Security Questionnaire for Enterprise Audit",
        "message": "Hello, our annual cybersecurity compliance review is underway. We require your latest SOC 2 Type II audit report, ISO 27001 certificate, and our completed vendor risk questionnaire before our renewal on July 1st. Please route to your compliance officer.",
        "sentiment": "NEUTRAL",
        "priority": "HIGH",
        "churn_risk": False,
        "requires_human": True,
    },
]

# ==============================================================================
# Generator Function
# ==============================================================================

def generate_1000_tickets(output_csv: str = "data/customer_support_tickets_1000.csv"):
    """Generates 1,000 realistic customer support tickets."""
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    tickets = []
    base_date = datetime(2024, 6, 1, 8, 0, 0)

    # 1,000 total: 350 Billing, 450 Technical, 200 Escalation
    category_counts = {"billing": 350, "technical": 450, "escalation": 200}
    ticket_counter = 1001

    for category, count in category_counts.items():
        if category == "billing":
            scenarios = BILLING_SCENARIOS
        elif category == "technical":
            scenarios = TECHNICAL_SCENARIOS
        else:
            scenarios = ESCALATION_SCENARIOS

        for i in range(count):
            scenario = random.choice(scenarios)
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            customer_name = f"{first_name} {last_name}"
            company_name, domain = random.choice(COMPANIES)
            email = f"{first_name.lower()}.{last_name.lower()}@{domain}"
            cust_id = f"CUST-{random.randint(100, 999):03d}"
            inv_id = f"INV-2024-{random.randint(1000, 9999)}"

            # Tier distribution: enterprise for escalation, pro/free for others
            if category == "escalation":
                tier = "enterprise" if random.random() < 0.75 else "pro"
            else:
                tier = random.choices(["free", "pro", "enterprise"], weights=[0.35, 0.50, 0.15])[0]

            channel = random.choices(["email", "web_portal", "api_monitor", "slack_connect"], weights=[0.45, 0.35, 0.10, 0.10])[0]

            # Disputed Amount calculation
            if "amount_range" in scenario:
                min_amt, max_amt = scenario["amount_range"]
                amount = round(random.uniform(min_amt, max_amt), 2)
            else:
                amount = None

            # Format text
            subject = scenario["subject"].format(
                name=customer_name,
                company=company_name,
                inv_id=inv_id,
                amount=amount if amount else 0.0,
                cust_id=cust_id,
            )
            message = scenario["message"].format(
                name=customer_name,
                company=company_name,
                inv_id=inv_id,
                amount=amount if amount else 0.0,
                cust_id=cust_id,
            )

            # Realistic sequential timestamp
            ticket_time = base_date + timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59),
            )

            # Final Human approval check
            requires_human = scenario["requires_human"]
            if category == "billing" and amount and amount > 50.0:
                requires_human = True

            tickets.append({
                "ticket_id": f"TIK-{ticket_counter}",
                "customer_id": cust_id,
                "customer_name": customer_name,
                "customer_email": email,
                "customer_company": company_name,
                "customer_tier": tier,
                "channel": channel,
                "subject": subject,
                "message": message,
                "disputed_amount": f"{amount:.2f}" if amount else "",
                "expected_category": category,
                "expected_sentiment": scenario["sentiment"],
                "expected_priority": scenario["priority"],
                "churn_risk": scenario["churn_risk"],
                "expected_human_approval": requires_human,
                "timestamp": ticket_time.strftime("%Y-%m-%d %H:%M:%S"),
            })

            ticket_counter += 1

    # Shuffle tickets to simulate real-time interleaving
    random.shuffle(tickets)

    # Write to CSV
    fieldnames = [
        "ticket_id",
        "customer_id",
        "customer_name",
        "customer_email",
        "customer_company",
        "customer_tier",
        "channel",
        "subject",
        "message",
        "disputed_amount",
        "expected_category",
        "expected_sentiment",
        "expected_priority",
        "churn_risk",
        "expected_human_approval",
        "timestamp",
    ]

    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tickets)

    print(f"Successfully generated {len(tickets)} enterprise tickets in: {output_csv}")
    return len(tickets)


if __name__ == "__main__":
    generate_1000_tickets()
