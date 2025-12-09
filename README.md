# Visualizing the T: MBTA Rider Satisfaction Score

## About
An interactive analytics platform that computes a comprehensive **Rider Satisfaction Score (RSS)** for the Massachusetts Bay Transportation Authority (MBTA) by combining operational performance metrics with passenger survey data.

**Team Members:** Dhanrithii Deepa, Eric Fu, Yuchen Cai  
**Live Demo:** [MBTA RSS Streamlit App](https://visualizing-the-t-2cjkqy3zr8ug6x6l5hkire.streamlit.app)

---

## Project Goal
Develop a data-driven Rider Satisfaction Score that:
- Reflects both **perceived experience** (survey data) and **operational performance** (travel times, restrictions, crowding)
- Enables **equity analysis** across demographic groups and service areas
- Provides **actionable insights** at station/line/time-period granularity for MBTA service planning

---

## How to Run

### Prerequisites
- Python 3.9+
- pip or conda

### Installation
```bash
# Clone repository
git clone https://github.com/urverse/Visualizing-the-T.git
cd Visualizing-the-T

# Install dependencies
pip install -r requirements.txt
```

### Run Analysis Notebooks
```bash
# Start Jupyter
jupyter notebook

# Run notebooks in order:
# 1. notebooks/01_data_exploration.ipynb
# 2. notebooks/02_indicator_calculation.ipynb
# 3. notebooks/03_rss_computation.ipynb
# 4. notebooks/04_advanced_analytics.ipynb
# 5. notebooks/05_statistical_validation.ipynb
```

### Run Streamlit Dashboard
```bash
streamlit run app/streamlit_app.py
```

---

## Methodology

### Data Sources
1. **MBTA 2024 Passenger Survey** - Rider satisfaction ratings and demographics
2. **Rapid Transit Travel Times** - Operational performance metrics
3. **Fall 2024 SDP Ridership** - Exposure weights by station/line/time
4. **Speed Restrictions by Day** - Service disruptions (slow zones)

### Approach
**1. Indicator Calculation**
- Travel time reliability (P90/median ratio)
- Travel time volatility (coefficient of variation)
- Speed restriction coverage (% of line restricted)
- Crowding levels (ridership/capacity ratio)
- Actual survey satisfaction scores

**2. RSS Computation**
- Literature-based weights applied to normalized indicators
- Ridge regression validates weights against survey satisfaction
- Exposure-weighted aggregation using ridership data

**3. Statistical Validation**
- ANOVA hypothesis testing for line comparisons
- Bootstrap confidence intervals (95% CI)
- Equity analysis across income/race demographics

### Key Findings
- **Orange Line achieved highest RSS** (73.2) despite serving predominantly low-income riders
- **Methodology is equity-neutral** - no systematic bias against underserved communities
- **Reliability is strongest satisfaction driver** (β = 0.42, p < 0.001)
- Statistical validation confirms robust model performance (R² = 0.68)

---

## Results & Outputs

### Generated Artifacts
- `data/final/rss_scores.csv` - RSS by station/line/time period
- `reports/figures/` - Visualizations (heatmaps, time series, equity charts)
- `reports/presentation.pdf` - Final academic presentation

### Dashboard Features
- Interactive line/station filtering
- Time-period comparisons
- Equity analysis breakouts
- Indicator contribution charts

---

## Repository Structure
```
Visualizing-the-T/
├── data/
│   ├── raw/              # Original MBTA datasets
│   ├── processed/        # Cleaned data
│   └── final/            # RSS scores
├── notebooks/            # Analysis notebooks (01-05)
├── src/                  # Python modules
├── app/                  # Streamlit dashboard
├── reports/              # Figures and presentation
├── config/               # Weights configuration
└── requirements.txt
```

---

## Dependencies
- **Data Processing:** pandas, pyspark, numpy
- **Modeling:** scikit-learn, scipy, statsmodels
- **Visualization:** matplotlib, seaborn, plotly
- **Dashboard:** streamlit
- **Configuration:** pyyaml

See `requirements.txt` for full list with versions.

---

## Team Contributions
- **Eric Fu:** Data engineering, PySpark ETL pipelines, infrastructure setup
- **Yuchen Cai:** Feature engineering, Streamlit app development, dashboard design
- **Dhanrithii Deepa:** Statistical validation, equity analysis, hypothesis testing

---

## License
MIT License - see LICENSE file for details

---

## Acknowledgments
Data provided by [MBTA Open Data Portal](https://www.mbta.com/developers/mbta-performance)
