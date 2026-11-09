# EnerSense – Smart Energy Intelligence Platform

An end-to-end AI-powered Smart Energy Management Platform that bridges **Electrical Physics** ($P = V \times I, E = P \times t$) with **Machine Learning** (Random Forest & Linear Regression) to predict consumption, estimate electricity bills, simulate savings, and deliver real-time personalized recommendations.

---

## ⚡ 15 Core Platform Features

1. **Responsive Real-Time Dashboard**: Key metrics (latest daily kWh, predicted monthly kWh, estimated bill, carbon footprint), monthly budget tracker, efficiency score ring, and interactive Trend & Distribution charts.
2. **AI Energy Prediction**: ML regression predicting daily kilowatt-hours (kWh) using 6 physical and environmental features with dual range sliders and real-time physics calculation preview.
3. **Appliance Energy Calculator**: Per-device power consumption breakdown (AC, ceiling fans, refrigerators, LED lights, washing machines, geysers, induction cooktops) with interactive doughnut chart and monthly cost estimates.
4. **Electricity Bill Estimator**: Configurable tariff calculator supporting Flat Rate, Residential Slab (tiered pricing), and Commercial Slab structures with full tier-by-tier cost breakdown.
5. **What-If Energy Saving Simulator**: Interactive simulator allowing users to adjust daily appliance operating hours and immediately calculate projected monthly energy savings (kWh), monetary savings (₹), and CO₂ reductions.
6. **Monthly Electricity Budget Planner**: Set a monthly spending ceiling; the platform automatically monitors usage percentage and triggers proactive visual alerts if bills risk exceeding budget.
7. **Consumption History & Graphs**: Comprehensive historical log with filtering by time period (24h, 7 days, 30 days) and consumption tier (LOW, NORMAL, HIGH), interactive trend chart, and pagination.
8. **One-Click CSV Export**: Download complete prediction and billing records in standard CSV format for external spreadsheet auditing.
9. **Monthly Comparison Engine**: Automatic calculation of current month vs. previous month consumption and percentage variance.
10. **Estimated Carbon Footprint**: Real-time greenhouse gas calculation based on regional grid emission factors (default: $0.82 \text{ kg CO}_2/\text{kWh}$ for Indian electricity grid).
11. **Personalized Energy-Saving Recommendations**: Data-driven suggestions tailored to active load current, ambient temperature, appliance count, and usage spikes.
12. **Energy Efficiency Score (0–100)**: Transparent 4-factor scoring model measuring consumption level (40 pts), runtime efficiency (25 pts), appliance count (20 pts), and temperature comfort (15 pts).
13. **AI Energy Advisor**: Interactive assistant that explains energy usage, provides conservation advice, breaks down appliances, and answers questions using grounded rules and telemetry (with optional Gemini API support).
14. **User Preferences & Tariff Settings**: Customizable profile saving regional tariff rates, currency (₹, $, €, £), household type, family size, budget limits, and secure password updates.
15. **Dark Mode & Light Mode**: Fluid theme toggle persisted in `localStorage` across page reloads.

---

## 🔬 Machine Learning Pipeline

- **Algorithm**: Random Forest Regressor ($100$ estimators, max depth $12$) with StandardScaler preprocessing.
- **Accuracy**: $R^2 = 0.9841$, $\text{MAE} = 1.1582 \text{ kWh}$, $\text{RMSE} = 1.5945 \text{ kWh}$.
- **Dataset**: 2,000 physically grounded records ($P = V \times I$ baseline + thermal load non-linearities + appliance standby loads).
- **Features**:
  1. `voltage` (V): AC supply voltage ($150\text{V} - 300\text{V}$)
  2. `current` (A): Total current drawn ($0.1\text{A} - 50\text{A}$)
  3. `usage_hours`: Active runtime ($0.1 - 24 \text{ hours/day}$)
  4. `number_of_appliances`: Active equipment count ($1 - 50$)
  5. `temperature`: Ambient temperature ($-10^\circ\text{C} - 60^\circ\text{C}$)
  6. `previous_consumption`: Historical consumption baseline ($\text{kWh}$)

---

## 📂 Project Structure

```text
smart-energy-prediction/
│
├── app.py                     # Flask web server, authentication, routing & REST APIs
├── requirements.txt           # Python dependencies
├── run_app.bat                # Windows double-click startup script
├── test_app.py                # Unit test suite for authentication and core routes
├── test_enersense_features.py # Unit test suite for new features (Advisor, CSV, etc.)
├── README.md                  # Comprehensive documentation
│
├── dataset/
│   └── energy_data.csv        # 2,000-record dataset
│
├── model/
│   ├── energy_model.pkl       # Trained Random Forest Regressor
│   ├── scaler.pkl             # Trained StandardScaler
│   └── metrics.json           # Model evaluation metrics and thresholds
│
├── training/
│   └── train_model.py         # Dataset generation, model training & plotting script
│
├── database/
│   ├── db_setup.py            # SQLite schema initialization and data helper functions
│   └── energy.db              # SQLite relational database
│
├── utils/
│   └── energy_utils.py        # Physics formulas, scoring, recommendations & Advisor engine
│
├── static/
│   ├── css/
│   │   └── style.css          # EnerSense theme styles (light/dark mode, components)
│   ├── js/
│   │   └── script.js          # Chart.js renderers, advisor AJAX, live preview, counters
│   └── images/                # Generated evaluation plots (actual vs predicted, etc.)
│
└── templates/                 # Jinja2 HTML templates
    ├── base.html              # Layout skeleton (sidebar, topbar, footer)
    ├── index.html             # High-converting landing page
    ├── dashboard.html         # Main energy dashboard with telemetry
    ├── predict.html           # Prediction form with range sliders and live preview
    ├── result.html            # Prediction result with physics comparison & score
    ├── advisor.html           # AI Energy Advisor interactive chat
    ├── appliance_calculator.html # Per-appliance energy calculator
    ├── simulator.html         # What-If energy saving simulator
    ├── bill_estimator.html    # Slab-based electricity bill estimator
    ├── history.html           # History with CSV export & trend chart
    ├── insights.html          # Rule-based AI insights & monthly comparison
    ├── model_performance.html # Model metrics and feature importances
    ├── settings.html          # Profile settings and password management
    ├── about.html             # Physics & AI scientific explanation
    ├── login.html             # Sign in with quick demo access buttons
    ├── register.html          # Account registration with password confirmation
    ├── 404.html               # Page not found error
    └── 500.html               # Internal server error page
```

---

## 🚀 How to Run the Project in VS Code

### Step 1: Open the Project in VS Code
1. Launch **Visual Studio Code**.
2. Go to **File → Open Folder...** and select the folder:
   ```
   c:\Users\vinay\OneDrive\Desktop\smart-energy-prediction
   ```

### Step 2: Open the Built-in Terminal
- Press ``Ctrl + ` `` (Backtick) or go to **Terminal → New Terminal**.

### Step 3: Run the Application
In the terminal, run:
```powershell
.\.venv\Scripts\python.exe app.py
```
*(If you are on a system with standard Python installed, you can simply run `python app.py`)*

### Step 4: Open in Your Browser
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔑 Demo Login Accounts

You can register a new account anytime, or use these pre-seeded accounts:

| Role | Email | Password |
|---|---|---|
| **Admin** | `admin@energy.ai` | `admin123` |
| **Student / User** | `student@energy.ai` | `energy123` |

---

## 🧪 Running the Automated Test Suite

To verify that all features, endpoints, and ML predictions are functioning properly:

```powershell
# Run the core application tests:
.\.venv\Scripts\python.exe -m unittest -v test_app.py

# Run the EnerSense platform feature tests (Advisor, CSV export, password change, etc.):
.\.venv\Scripts\python.exe -m unittest -v test_enersense_features.py
```
Both test suites will output `OK`.
