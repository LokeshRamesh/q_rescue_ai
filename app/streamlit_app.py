import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.graph_objects as go

from q_rescue.services.response_service import compare_allocators
from q_rescue.simulation.generator import generate_scenario

# New imports added for scenario selection
from q_rescue.domain.models import DisasterCategory
from q_rescue.simulation.scenarios import generate_scenario_by_category

st.set_page_config(page_title="Q-Rescue AI", layout="wide")
st.title("Q-Rescue AI")
st.caption("Classical and quantum-inspired emergency resource allocation")

seed = st.sidebar.number_input("Scenario seed", min_value=0, value=42)
ambulance_count = st.sidebar.slider("Ambulances", 1, 10, 3)
incident_count = st.sidebar.slider("Incidents", 1, 20, 5)

# Scenario type dropdown
scenario_type = st.sidebar.selectbox(
    "Scenario Type",
    [
        "GENERIC",
        "FLOOD",
        "INDUSTRIAL_ACCIDENT",
        "CITY_WIDE_EMERGENCY",
    ],
)

# old scenario generation removed
scenario = generate_scenario_by_category(
    DisasterCategory[scenario_type],
    config={
        "simulation": {
            "ambulances": ambulance_count,
            "incidents": incident_count
        }
    },
    seed=int(seed),
)

actual_variables = (
    len(scenario.ambulances)
    * len(scenario.incidents)
)

if actual_variables > 24:
    st.warning(
        f"This scenario generates {actual_variables} binary variables. "
        "The starter exact QUBO solver supports at most 24 variables. "
        "Reduce the scenario size."
    )
    st.stop()

# Hospital Visualization
st.subheader("Hospital Capacity")

hospital_df = pd.DataFrame([
    {
        "id": h.id,
        "name": h.name,
        "lat": h.location.x,
        "lon": h.location.y,
        "available_beds": h.available_beds
    }
    for h in scenario.hospitals
])

st.dataframe(hospital_df)

# Model for Map Selection
model_view = st.sidebar.radio(
    "Show Model",
    ["Classical", "Quantum"]
)

comparison = compare_allocators(scenario)

# Performance Comparison Chart
st.subheader("Classical vs Quantum Performance")

classical_metrics = comparison["classical"]["metrics"]
quantum_metrics = comparison["quantum"]["metrics"]

metric_names = list(classical_metrics.keys())

fig = go.Figure()

fig.add_trace(go.Bar(
    name="Classical",
    x=metric_names,
    y=[classical_metrics[m] for m in metric_names]
))

fig.add_trace(go.Bar(
    name="Quantum",
    x=metric_names,
    y=[quantum_metrics[m] for m in metric_names]
))

fig.update_layout(
    barmode="group",
    title="Solver Performance Comparison",
    yaxis_title="Value"
)

st.plotly_chart(fig, use_container_width=True)

# Map Visualization
# Ambulance (Blue)
ambulance_df = pd.DataFrame([
    {
        "lat": a.location.x,
        "lon": a.location.y,
        "type": "Ambulance",
        "id": a.id
    }
    for a in scenario.ambulances
])

# Incidents (Red)
incident_df = pd.DataFrame([
    {
        "lat": i.location.x,
        "lon": i.location.y,
        "type": "Incident",
        "id": i.id
    }
    for i in scenario.incidents
])

# Assignment Lines
assignment_lines = []

for name, result in comparison.items():
    # Filter Models
    if model_view == "Classical" and name != "classical":
        continue
    if model_view == "Quantum" and name != "quantum":
        continue

    for assignment in result["result"].assignments:
        amb = next(a for a in scenario.ambulances if a.id == assignment.ambulance_id)
        inc = next(i for i in scenario.incidents if i.id == assignment.incident_id)

        assignment_lines.append({
            "from_lat": amb.location.x,
            "from_lon": amb.location.y,
            "to_lat": inc.location.x,
            "to_lon": inc.location.y,
        })

assignment_df = pd.DataFrame(assignment_lines)

# Map Layers
# Ambulance Layer Blue
ambulance_layer = pdk.Layer(
    "ScatterplotLayer",
    data=ambulance_df,
    get_position=["lon", "lat"],
    get_color=[0, 0, 255],
    get_radius=80,
)

# Incident Layer Red
incident_layer = pdk.Layer(
    "ScatterplotLayer",
    data=incident_df,
    get_position=["lon", "lat"],
    get_color=[255, 0, 0],  
    get_radius=80,
)

# Assignment Lines Green
line_layer = pdk.Layer(
    "LineLayer",
    data=assignment_df,
    get_source_position=["from_lon", "from_lat"],
    get_target_position=["to_lon", "to_lat"],
    get_color=[0, 255, 0],  
    get_width=3,
)

# Hospital Layer
hospital_layer = pdk.Layer(
    "ScatterplotLayer",
    data=hospital_df,
    get_position=["lon", "lat"],
    get_color=[128, 0, 128],  # purple
    get_radius=120,
)

# Map View
st.subheader("Scenario Map (With Assignments)")

view_state = pdk.ViewState(
    latitude=float(scenario.ambulances[0].location.x),
    longitude=float(scenario.ambulances[0].location.y),
    zoom=11,
)

st.pydeck_chart(pdk.Deck(
    layers=[ambulance_layer, incident_layer, hospital_layer, line_layer],
    initial_view_state=view_state
))

# Solver Metadata
st.subheader("Solver Metadata")

binary_vars = len(scenario.ambulances) * len(scenario.incidents)

classical_name = comparison["classical"]["result"].solver_name
quantum_name = comparison["quantum"]["result"].solver_name

# Friendly explanations
solver_explanations = {
    "classical-greedy": "Classical: fast greedy assignment method",
    "exact-enumeration": "Quantum: exact solution for small problems",
    "qaoa": "Quantum: approximate solution using QAOA",
}

st.markdown(f"""
### System Overview
- **Possible assignments:** `{binary_vars}` ambulance–incident combinations  
- **Classical solver:** {solver_explanations.get(classical_name, classical_name)}  
- **Quantum solver:** {solver_explanations.get(quantum_name, quantum_name)}  
""")

for column, (name, payload) in zip(st.columns(2), comparison.items(), strict=True):
    with column:
        result = payload["result"]
        st.subheader(name.title())
        st.metric("Objective", f"{result.objective_value:.2f}")
        st.write("Feasibility:", "Feasible" if result.feasible else "Infeasible")
        st.dataframe([assignment.__dict__ for assignment in result.assignments])
