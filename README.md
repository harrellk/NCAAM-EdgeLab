# 🏀 NCAAM EdgeLab  
### Advanced College Basketball Modeling & Betting Analytics  
**Author:** Harl (Kevin Harrell)  
**Status:** v1.0.0 — Stable Modular Pipeline  
**Branches:** `master` (stable) • `dev` (active development)

---

## 📌 Overview

NCAAM EdgeLab is a fully modular college basketball analytics engine built to:

- Ingest **DraftKings sportsbook odds**
- Ingest and merge **KenPom efficiency data**
- Generate **model-calibrated spreads, totals, and win probabilities**
- Compute **true betting edges** using a corrected home/away spread convention
- Produce daily **playable model output** for handicapping

The system is built for:
- Accuracy  
- Reproducibility  
- Transparency  
- Long-term maintainability  

It runs through a clean daily pipeline:

fetch_odds → load_kenpom → apply_mappings → compute_model → generate_edges → run_daily

yaml
Copy code

---

## 📁 Project Structure

NCAAM-EdgeLab/
│
├── data/
│ ├── raw/ # Daily odds, KenPom source files
│ ├── processed/ # Cleaned + merged KP tables and daily model input
│ └── mappings/ # Team alias mapping files
│
├── output/
│ ├── model/ # Final model outputs
│ ├── logs/ # Mapping and diagnostics logs
│ └── reports/ # Accuracy tracking & performance history
│
├── src/
│ ├── fetch_odds.py # Extract & normalize sportsbook odds
│ ├── load_kenpom.py # Load + merge KenPom efficiency metrics
│ ├── apply_mappings.py # Team alias cleanup
│ ├── compute_model.py # Model calibration & projections
│ ├── generate_edges.py # Edge computation logic
│ ├── run_daily.py # Main pipeline runner (modular)
│ └── utils.py # Helper functions / normalization
│
├── venv/ # Python virtual environment
│
├── README.md # Project documentation
└── CHANGELOG.md # Version history

yaml
Copy code

---

## 🚀 Getting Started

### **1. Clone the repository**
git clone https://github.com/harrellk/NCAAM-EdgeLab.git
cd NCAAM-EdgeLab

shell
Copy code

### **2. Create your virtual environment**
(You already have this, but for documentation)

python -m venv venv

markdown
Copy code

### **3. Activate the environment**

**PowerShell:**
.\venv\Scripts\Activate.ps1

makefile
Copy code

**CMD:**
venv\Scripts\activate

markdown
Copy code

### **4. Install dependencies**
pip install -r requirements.txt # (optional once you add this file)

yaml
Copy code

---

## 🔧 Running the Daily Pipeline

Run the full end-to-end process:

python src/run_daily.py

markdown
Copy code

This performs:

1. Load DraftKings odds  
2. Load + merge KenPom  
3. Team alias normalization  
4. Spread/total model computation  
5. Calibration + home-court adjustments  
6. Value-side selection  
7. Save output to:

output/model/Model_Batch_Output_Calibrated.csv

markdown
Copy code

---

## 📊 Model Features

### **✔ Calibrated spreads (home & away)**  
- Uses corrected home-only convention  
- Applies home-court advantage  
- Blowout compression logic (>18pt spreads)

### **✔ Calibrated totals**  
- Tempo-adjusted  
- KenPom-based AdjOE + AdjDE  
- Model scaling factor

### **✔ Win probability**  
Using logistic transformation of model spread.

### **✔ True betting edges**  
Automatically computes:

- HomeSpreadEdge  
- AwaySpreadEdge  
- TotalEdge  
- EdgeSide  
- EdgeTeam  
- EdgePoints  

---

## 🧩 Development Workflow

### **Branches**
- `master` — stable, tagged versions only  
- `dev` — everyday coding happens here  

### **Typical workflow**
git checkout dev
git pull

make changes
git add .
git commit -m "Clear description of change"
git push

markdown
Copy code

### **Promote to stable**
git checkout master
git merge dev
git tag v1.0.X
git push
git push --tags

yaml
Copy code

---

## 🧹 Code Style

- **Black** for auto-formatting
- **Ruff** for linting & import organization
- **Pylance** for static analysis
- Editor settings stored via VS Code profile

---

## 🧪 Accuracy Tracking

Daily output is stored in:

output/reports/model_results_tracking.xlsx

yaml
Copy code

Tracks:

- Spread bias  
- Total bias  
- Model MAE  
- Edge hit/miss rate  

Future enhancements will include automated trend detection.

---

## 🧭 Roadmap

### Upcoming:
- Model bias self-correction  
- Automated tuning (spread/total scaling)  
- Advanced matchup-based adjustments  
- Player-level impact (Fouls / usage / injuries)  
- Web dashboard for output visualization

---

## 🤝 Contributions

This is a closed personal project, but structure is ready for:
- branching  
- pull requests  
- issue tracking  
- documentation  

---

## 📜 License
All rights reserved — personal analytics project.
