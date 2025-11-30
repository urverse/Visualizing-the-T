import streamlit as st
import pandas as pd
import altair as alt
from src.dashboard_utils import load_all_data

st.set_page_config(page_title="Hypothesis Testing", page_icon="🧪", layout="wide")

st.title("🧪 Hypothesis Testing & Statistical Analysis")

data = load_all_data()

if data is None:
    st.error("Failed to load data.")
    st.stop()

bootstrap = data.get('confidence_intervals')
learned_weights = data.get('learned_weights')
model_results = data.get('regression_results')

if bootstrap is None or learned_weights is None or model_results is None:
    st.error("Statistical data files not found in the loaded dataset.")
    st.stop()

st.markdown("### Confidence Intervals for RSS")
st.write("Bootstrap analysis (95% CI) to test if differences between lines are statistically significant.")

# Chart for CI
base = alt.Chart(bootstrap).encode(
    x=alt.X('Mean_RSS', scale=alt.Scale(domain=[70, 100]), title='Mean RSS Score'),
    y=alt.Y('Route', title='Route')
)

points = base.mark_point(filled=True, size=100, color='black')
error_bars = base.mark_errorbar().encode(
    x='CI_Lower',
    x2='CI_Upper'
)

chart = (error_bars + points).properties(
    title='95% Confidence Intervals for Route Satisfaction Scores',
    height=200
)

st.altair_chart(chart, use_container_width=True)

st.write("**Interpretation:**")
st.dataframe(bootstrap.style.format({
    'Mean_RSS': '{:.2f}',
    'CI_Lower': '{:.2f}',
    'CI_Upper': '{:.2f}'
}))

st.divider()

st.markdown("### Feature Importance (Learned Weights)")
st.write("Weights derived from regression analysis to understand drivers of satisfaction.")

weights_chart = alt.Chart(learned_weights).mark_bar().encode(
    x=alt.X('Weight', title='Coefficient Value'),
    y=alt.Y('Feature', sort='-x', title='Feature'),
    color=alt.condition(
        alt.datum.Weight > 0,
        alt.value('steelblue'),  # The positive color
        alt.value('orange')      # The negative color
    )
).properties(
    title='Impact of Metrics on RSS'
)

st.altair_chart(weights_chart, use_container_width=True)

st.divider()

st.markdown("### Model Performance")
st.dataframe(model_results)
