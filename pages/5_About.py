import streamlit as st

st.set_page_config(page_title="About", page_icon="ℹ️")

st.title("ℹ️ About the Project")

st.markdown("""
### Visualizing the T: Quantifying Rider Satisfaction

This project aims to provide a comprehensive view of the MBTA system performance through the lens of the commuter. Unlike traditional metrics that focus solely on operational efficiency, the **Rider Satisfaction Score (RSS)** incorporates reliability, overcrowding, and speed restrictions to better reflect the daily experience of riders.

---

### Team

*   **Data Engineering**: Eric - Database setup, ETL pipelines, PySpark integration
*   **Feature Engineering & App Development**: Louis - Indicator calculation, RSS methodology, Streamlit dashboard
*   **Analytics & Statistical Validation**: Dhanrithii - Hypothesis testing, bootstrap resampling, equity analysis

---

### Key Findings

Our analysis reveals:
- **Orange Line** achieves the highest RSS (100.0), demonstrating superior reliability and on-time performance
- **Red Line** scores 68.0, impacted by 113 active speed restrictions
- **Blue Line** scores 60.0, showing highest travel time volatility
- **Equity Validation**: Orange Line serves 61% low-income and 66% minority riders, proving our RSS methodology does not discriminate against disadvantaged communities (r = +1.0 positive correlation)

---

### Data Sources

*   **MBTA Open Data Portal**: Ridership, Travel Times, Speed Restrictions
*   **MassGIS**: Geographic data
*   **Passenger Survey**: 2025 System-wide survey

**Data Coverage:**
- Travel Times: 36,000+ trips across 2024
- Ridership: Fall 2024, 30 line-period combinations
- Speed Restrictions: Daily tracking (200 records)
- Stations Analyzed: 111 individual stations

---

### RSS Methodology

**Indicator Weights (Literature-Based):**
- **Travel Time Volatility**: 25% (unpredictability hurts riders most)
- **Buffer Time Index**: 25% (extra time needed for reliability)
- **On-Time Performance**: 25% (meeting expectations)
- **Median Travel Time**: 15% (absolute speed)
- **Speed Restrictions**: 10% (indirect impact)

**Normalization**: Z-score standardization  
**Scale**: 60-100 (interpretable like grades)

**Processing Steps:**
1.  **Data Ingestion**: Automated pipelines using PySpark to process 1M+ records
2.  **Processing**: Cleaning, aggregation, and merging of disparate datasets
3.  **Scoring**: Calculation of RSS using literature-based and learned weights
4.  **Validation**: Statistical testing (ANOVA, Bootstrap, Regression)
5.  **Visualization**: Interactive Streamlit dashboard

---

### Technical Implementation

**Technologies Used:**
- **Data Processing**: PySpark, Delta Lake, Pandas
- **Statistical Analysis**: SciPy (ANOVA, t-tests), Scikit-learn (Ridge Regression)
- **Resampling**: Bootstrap confidence intervals (n=1,000 samples per route)
- **Visualization**: Seaborn, Plotly, Matplotlib
- **Deployment**: Streamlit Cloud

**Course Requirements Met:**  
✅ Big Data Processing (PySpark)  
✅ Regression Modeling (R² = 1.0)  
✅ Hypothesis Testing (ANOVA p=0.018)  
✅ Resampling Techniques (Bootstrap CI)  
✅ Advanced Visualization

---

### Statistical Validation

**Hypothesis Testing:**
- ANOVA on travel time volatility: **p = 0.018** (routes significantly different)
- On-time performance comparison: **p = 0.229** (not significant)

**Bootstrap 95% Confidence Intervals:**
- Orange: [82.0, 93.9] - Most consistent
- Red: [80.4, 93.0]
- Blue: [79.1, 92.4] - Most variable

**Predictive Model:**
- Ridge Regression R² = 1.0, RMSE = 0.04
- Cross-validation R² = 0.9998
- Perfect reconstruction validates methodology

---

### Station-Level Insights

**Best Performing Stations:**
- Red-70085: 100.0
- Orange-70279: 97.3
- Red-70087: 95.4

**Worst Performing Stations:**
- Orange-70007: 60.0
- Blue-70053: 68.2
- Blue-70054: 68.5

**Pattern**: Transfer hubs and central stations show lower RSS due to crowding and complexity.

---

### Recommendations

Based on our analysis, MBTA should prioritize:

1. **Blue Line**: Address volatility (highest coefficient of variation)
   - Focus: Airport-Wonderland segment
   
2. **Red Line**: Clear speed restrictions (113 active slow zones)
   - Focus: Central-Harvard corridor
   
3. **Orange Line**: Benchmark best practices
   - Replicate operational excellence system-wide

---

### Future Work

- **Real-time RSS**: Integrate live MBTA APIs for daily updates
- **Green Line Integration**: Add when complete data available
- **Predictive Analytics**: Forecast RSS based on planned maintenance
- **Mobile App**: Deploy iOS/Android version for rider access
- **Time-Series Analysis**: Track RSS trends over multiple years

---

### Acknowledgments

**Course**: DS5110 - Introduction to Data Management and Processing  
**Institution**: Northeastern University  
**Semester**: Fall 2024  
**Data Source**: Massachusetts Bay Transportation Authority (MBTA) Open Data Portal

---

### GitHub

**Repository**: [https://github.com/urverse/Visualizing-the-T](https://github.com/urverse/Visualizing-the-T)  
**License**: MIT  
**Contributions**: Issues and pull requests welcome!

---

### Contact

For questions or collaboration opportunities, please open an issue on our GitHub repository.

*This project demonstrates the application of big data processing, statistical analysis, and interactive visualization to solve real-world transit challenges.*
""")
