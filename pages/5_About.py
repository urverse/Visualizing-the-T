import streamlit as st

st.set_page_config(page_title="About", page_icon="ℹ️")

st.title("ℹ️ About the Project")

st.markdown("""
### Visualizing the T: Quantifying Rider Satisfaction

This project aims to provide a comprehensive view of the MBTA system performance through the lens of the commuter. Unlike traditional metrics that focus solely on operational efficiency, the **Rider Satisfaction Score (RSS)** incorporates reliability, overcrowding, and speed restrictions to better reflect the daily experience of riders.

### Team
*   **Data Science**: [Name]
*   **Visualization**: [Name]
*   **Engineering**: [Name]

### Data Sources
*   **MBTA Open Data Portal**: Ridership, Travel Times, Speed Restrictions.
*   **MassGIS**: Geographic data.
*   **Passenger Survey**: 2025 System-wide survey.

### Methodology
1.  **Data Ingestion**: Automated pipelines fetch daily data.
2.  **Processing**: Cleaning, aggregation, and merging of disparate datasets.
3.  **Scoring**: Calculation of RSS using literature-based and learned weights.
4.  **Visualization**: Interactive Streamlit dashboard.

### GitHub
[Link to https://github.com/urverse/Visualizing-the-T]
""")
