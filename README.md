# 🍲 Local Food Wastage Management System

## 📌 Project Overview
This project addresses the issue of surplus food wastage by connecting food providers (restaurants, grocery stores, etc.) with receivers (NGOs, individuals) through a Streamlit-powered dashboard.  
It uses **Python, SQL, and Streamlit** to manage and analyze food donation data, perform CRUD operations, and generate insights.

---

## 🎯 Features
- Load data from CSVs into an SQLite database
- Perform **15 SQL queries** answering key food wastage and distribution questions
- **CRUD operations** for Providers, Receivers, Food Listings, and Claims
- Charts for provider types, claim status distribution, and food types
- **Expiry alerts** for food nearing expiration
- Search filters for quick data access

---

## 🗂 Dataset
- `providers_data.csv` → Food providers info
- `receivers_data.csv` → Food receivers info
- `food_listings_data.csv` → Available food listings
- `claims_data.csv` → Food claim records

## Folder Structure/
- │
- ├── app.py                        # Streamlit dashboard (final enhanced version)
- ├── requirements.txt              # Dependencies
- ├── README.md                     # Project documentation
- │
- ├── db/                            # Database folder
- │   └── food_wastage.db           # Generated after running the app/loader
- │
- ├── data/                          # CSV files (raw data)
- │   ├── providers_data.csv
- │   ├── receivers_data.csv
- │   ├── food_listings_data.csv
- │   └── claims_data.csv
- │
- ├── Food Provider.pdf
- |
- └── scripts/                       # Helper scripts
-     ├── create_tables.py
-     ├── load_data.py
-     └── queries.py


## 🚀 How to Run
1. Clone this repository:
   ```bash
   git clone https://github.com/SuziSharma2/local-food-wastage-management.git
   cd local-food-wastage-management
