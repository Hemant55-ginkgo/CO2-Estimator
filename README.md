# 🚛 European Freight CO₂ Estimator

> Compare carbon emissions across Road FTL, Road LTL, and Air Freight using real road distances and published GLEC emission factors — built for logistics professionals navigating CSRD reporting obligations.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![GLEC](https://img.shields.io/badge/Methodology-GLEC%20v3.0-10b981?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-64748b?style=flat-square)

---

## What This Tool Does

The European Freight CO₂ Estimator is an interactive web application that calculates and compares the carbon footprint of a freight shipment across three transport modes:

- **Road FTL** (Full Truckload) — dedicated truck, lowest emissions per tonne-km
- **Road LTL** (Groupage / Less-than-Truckload) — shared truck space, higher due to partial loads
- **Air Freight** — fastest, but 9–10× more carbon-intensive than road

A user enters an origin city, destination city, and shipment weight. The app calls the **OpenRouteService API** to retrieve the real HGV road distance, applies **GLEC Framework v3.0** emission factors, and instantly renders a comparison chart, formula breakdown, key insight, and a downloadable PDF report.

---

## The Logistics Problem It Solves

Freight modal choice is one of the highest-leverage decisions in supply chain sustainability. A shipper moving 5 tonnes from Hamburg to Warsaw by air produces roughly **9.7× more CO₂e** than the equivalent FTL road shipment — yet many transport decisions are still made purely on lead time and cost.

This tool makes the carbon cost of modal choice **visible and quantified** in under 10 seconds, without requiring access to a TMS, a sustainability consultant, or a spreadsheet model.

It is particularly relevant for:
- **Logistics managers** evaluating modal shift opportunities
- **Sustainability teams** building Scope 3 emissions inventories
- **Freight forwarders** advising clients on greener routing options
- **Supply chain analysts** preparing CSRD disclosures

---

## Live Demo

🔗 **[Launch the app →](https://your-app-name.streamlit.app)**
*(Replace this link after deploying to Streamlit Community Cloud)*

**Example output — Hamburg to Warsaw, 5,000 kg:**

| Transport Mode | CO₂e (kg) | vs FTL |
|---|---|---|
| Road FTL | 328.5 | baseline |
| Road LTL | 540.1 | 1.6× |
| Air Freight | 3,178.6 | 9.7× |

---

## Methodology

### Emission Factors

Sourced from the **Global Logistics Emissions Council (GLEC) Framework v3.0**, published by the Smart Freight Centre. This is the leading international standard for calculating and reporting logistics emissions, aligned with the GHG Protocol and referenced in ISO 14083.

| Mode | Factor | Source |
|---|---|---|
| Road FTL | 0.0623 kg CO₂e / tonne-km | GLEC Framework v3.0, Table 4 |
| Road LTL | 0.1025 kg CO₂e / tonne-km | GLEC Framework v3.0, Table 4 |
| Air Freight | 0.602 kg CO₂e / tonne-km | GLEC Framework v3.0, Table 6 |

### Formula

```
CO₂e (kg) = Distance (km) × Weight (tonnes) × Emission Factor (kg CO₂e / tonne-km)
```

### Distance Calculation

Road distances are calculated using the **OpenRouteService API** with the `driving-hgv` (Heavy Goods Vehicle) routing profile, which accounts for truck-specific road restrictions and produces more accurate freight distances than standard car routing.

### Scope

Results represent **tank-to-wheel (TTW)** emissions — direct combustion emissions from fuel use. Well-to-wheel (WTW) figures would be approximately 20% higher for diesel road transport. Results are indicative estimates intended for **modal comparison purposes**.

---

## CSRD Relevance

The EU **Corporate Sustainability Reporting Directive (CSRD)**, which entered into force in 2023, requires large companies to disclose Scope 3 greenhouse gas emissions under **ESRS E1** standards. Freight transport typically represents a material portion of a company's Scope 3 Category 4 (upstream transportation) and Category 9 (downstream transportation) emissions.

This tool supports the preliminary quantification step — understanding the emissions profile of different transport choices — before feeding results into a full GHG inventory.

---

## Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| Web framework | Streamlit | Interactive UI, no HTML required |
| Routing API | OpenRouteService | Real HGV road distances |
| Data | pandas | CSV emission factor lookup |
| Charts | Plotly | Interactive bar chart |
| PDF export | fpdf2 | Downloadable report generation |
| Environment | python-dotenv | Secure API key management |

---

## Project Structure

```
co2-estimator/
├── app.py                  # Main Streamlit application
├── utils/
│   ├── calculator.py       # GLEC formula logic
│   ├── routing.py          # OpenRouteService API integration
│   └── pdf_export.py       # PDF report generation
├── data/
│   └── glec_factors.csv    # GLEC emission factors lookup table
├── requirements.txt
└── README.md
```

---

## Run Locally

### Prerequisites
- Python 3.11 or higher
- A free OpenRouteService API key ([get one here](https://openrouteservice.org/dev/#/signup) — no credit card required)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-username/co2-estimator.git
cd co2-estimator

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your API key
cp .env.example .env
# Open .env and replace "your_api_key_here" with your ORS key

# 5. Launch the app
streamlit run app.py
```

The app will open automatically at `http://localhost:8501`

### Test the Formula (no API key needed)

```bash
python utils/calculator.py
```

### Test the API Connection

```bash
python utils/routing.py
```

---

## Key Design Decisions

**Why GLEC Framework?**
GLEC v3.0 is the methodology referenced by the Smart Freight Centre, aligned with ISO 14083, and increasingly cited in CSRD-related logistics reporting. Using published, citable factors makes the tool credible and auditable.

**Why OpenRouteService instead of Google Maps?**
ORS is free, open-source, and offers a dedicated HGV routing profile — more appropriate for freight than car-optimised APIs. No credit card required for the free tier.

**Why Streamlit?**
For a data tool aimed at logistics professionals, Streamlit delivers a functional, shareable web interface with minimal front-end overhead — keeping the codebase focused on the domain logic.

---

## Limitations

- Emission factors are European averages — actual emissions vary by vehicle age, load factor, and fuel type
- Air freight factor includes belly cargo averages — dedicated freighter flights have different profiles
- Does not account for empty return legs, transshipment, or last-mile delivery
- Road distances assume direct HGV routing — actual routes may differ due to restrictions or congestion

---

## References

- Smart Freight Centre. (2023). *GLEC Framework for Logistics Emissions Accounting and Reporting, Version 3.0*. smartfreightcentre.org
- European Commission. (2022). *Corporate Sustainability Reporting Directive (CSRD)*, Directive 2022/2464/EU
- OpenRouteService. (2024). *HGV Routing API Documentation*. openrouteservice.org
- GHG Protocol. (2011). *Corporate Value Chain (Scope 3) Accounting and Reporting Standard*

---

## Author

Built by [Your Name] as a portfolio project demonstrating applied Python development in the logistics and supply chain domain.

🔗 [LinkedIn](https://linkedin.com/in/your-profile) · [GitHub](https://github.com/your-username)

---

*Results are indicative estimates for modal comparison purposes only and should not be used as the sole basis for regulatory reporting without further verification.*
