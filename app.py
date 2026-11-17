import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from itertools import combinations

st.set_page_config(page_title="Iconic Buildings Evaluation Model", page_icon="◆", layout="wide")

BURGUNDY = "#7B1834"
ACHIEVED = "#8B2945"
NOT_ACHIEVED = "#F1D6D8"
LEVEL_COLORS = {"Q1": "#B98A9A", "Q2": "#DFA8A0", "Q3": "#EBCB9E",
                "Q4": "#C7D0AE", "Q5": "#AFC7D0", "Not Qualified": "#888888"}

CORE = {"IV": "Iconic Vision", "N": "Novelty", "A": "Applicability"}
OUTCOMES = {"NS": "New Symbolism", "NCI": "New City Image",
            "GA": "Global Attachment", "EG": "Economic Growth"}

# Exact 16 combinations from the supplied matrix, grouped by level.
COMBINATIONS = [
    ("C1", "Q1", ("NS", "NCI", "GA", "EG")),
    ("C2", "Q2", ("NS", "NCI", "GA")),
    ("C3", "Q2", ("NS", "NCI", "EG")),
    ("C4", "Q2", ("NS", "GA", "EG")),
    ("C5", "Q2", ("NCI", "GA", "EG")),
    ("C6", "Q3", ("NS", "NCI")),
    ("C7", "Q3", ("NS", "GA")),
    ("C8", "Q3", ("NS", "EG")),
    ("C9", "Q3", ("NCI", "GA")),
    ("C10", "Q3", ("NCI", "EG")),
    ("C11", "Q3", ("GA", "EG")),
    ("C12", "Q4", ("NS",)),
    ("C13", "Q4", ("NCI",)),
    ("C14", "Q4", ("GA",)),
    ("C15", "Q4", ("EG",)),
    ("C16", "Q5", ()),
]

def classify(values):
    if not all(bool(values[k]) for k in CORE):
        return "Not Qualified", 0, [], None
    achieved = [k for k in OUTCOMES if bool(values[k])]
    count = len(achieved)
    level = {4: "Q1", 3: "Q2", 2: "Q3", 1: "Q4", 0: "Q5"}[count]
    combo_id = next(cid for cid, q, members in COMBINATIONS
                    if q == level and set(members) == set(achieved))
    return level, count, achieved, combo_id

def make_heatmap(selected_id=None, core_pass=True):
    columns = ["IV", "N", "A", "NS", "NCI", "GA", "EG"]
    z, text, ylabels = [], [], []
    for cid, level, members in COMBINATIONS:
        row = [1, 1, 1] + [1 if k in members else 0 for k in ["NS", "NCI", "GA", "EG"]]
        z.append(row)
        text.append(["✓" if v else "–" for v in row])
        ylabels.append(f"{level} · {cid}")
    # Core requirements are shown as mandatory in every combination.
    # If the current building fails a core criterion, its outcome is Not Qualified;
    # the matrix still shows the canonical 16 eligible combinations.
    fig = go.Figure(go.Heatmap(
        z=z, x=columns, y=ylabels,
        zmin=0, zmax=1,
        colorscale=[[0, NOT_ACHIEVED], [0.49, NOT_ACHIEVED],
                    [0.5, ACHIEVED], [1, ACHIEVED]],
        showscale=False,
        text=text, texttemplate="%{text}",
        xgap=5, ygap=5,
        hovertemplate="Combination: %{y}<br>Criterion: %{x}<br>%{text}<extra></extra>",
    ))
    if selected_id:
        index = [c[0] for c in COMBINATIONS].index(selected_id)
        fig.add_shape(type="rect", xref="paper", yref="y",
                      x0=0, x1=1, y0=index-0.48, y1=index+0.48,
                      line=dict(color=BURGUNDY, width=3), fillcolor="rgba(0,0,0,0)")
    fig.update_layout(
        height=610, margin=dict(l=10, r=10, t=20, b=10),
        xaxis=dict(side="top", tickfont=dict(size=13), fixedrange=True),
        yaxis=dict(autorange="reversed", tickfont=dict(size=12), fixedrange=True),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#35151D"),
    )
    return fig

if "evaluations" not in st.session_state:
    st.session_state.evaluations = []

st.title("Iconic Buildings Evaluation Model")
st.caption("Binary evaluation · 5 Iconicity Levels · 16 Combinations")

tab_eval, tab_compare, tab_saved, tab_rules = st.tabs(
    ["Evaluate a Building", "Compare Buildings", "Saved Evaluations", "Model Rules"]
)

with tab_eval:
    left, right = st.columns([0.85, 1.5], gap="large")
    with left:
        st.subheader("1. Building Information")
        name = st.text_input("Building name", placeholder="e.g. Sydney Opera House")
        location = st.text_input("Location", placeholder="City, Country")
        year = st.text_input("Completion year (optional)", placeholder="e.g. 1973")

        st.subheader("2. Evaluation Criteria")
        st.markdown("**Core Requirements (all three are mandatory)**")
        values = {}
        for code, label in CORE.items():
            values[code] = st.checkbox(f"{code} — {label}", value=False, key=f"core_{code}")
        st.divider()
        st.markdown("**Complementary Outcomes**")
        for code, label in OUTCOMES.items():
            values[code] = st.checkbox(f"{code} — {label}", value=False, key=f"out_{code}")

        evaluate = st.button("Evaluate Building", type="primary", use_container_width=True)

    level, count, achieved, combo_id = classify(values)
    with right:
        st.subheader("3. Evaluation Result")
        m1, m2, m3 = st.columns(3)
        m1.metric("Iconicity Level", level)
        m2.metric("Combination", combo_id or "—")
        m3.metric("Achieved Outcomes", f"{count}/4")
        if level == "Not Qualified":
            st.error("Not Qualified — at least one mandatory Core Requirement is not achieved.")
        else:
            st.success(f"{level} Iconicity · {combo_id} · Core requirements achieved")
        st.subheader("Combination Heatmap — 16 Combinations")
        st.caption("Rows represent the exact 16 combinations; columns show the three Core Requirements and four Complementary Outcomes. The outlined row is the current result.")
        st.plotly_chart(make_heatmap(combo_id, level != "Not Qualified"),
                        use_container_width=True, config={"displayModeBar": False})
        st.caption("Dark cells = achieved within that combination · Light cells = not included in that combination.")

        if evaluate:
            if not name.strip():
                st.warning("Please enter a building name before saving the evaluation.")
            else:
                record = {
                    "Building": name.strip(), "Location": location.strip(), "Year": year.strip(),
                    **{CORE[k]: "Achieved" if values[k] else "Not achieved" for k in CORE},
                    **{OUTCOMES[k]: "Achieved" if values[k] else "Not achieved" for k in OUTCOMES},
                    "Iconicity Level": level, "Combination": combo_id or "Not Qualified",
                    "Achieved Outcomes": ", ".join(achieved) if achieved else "None",
                }
                st.session_state.evaluations = [
                    r for r in st.session_state.evaluations
                    if r["Building"].casefold() != name.strip().casefold()
                ]
                st.session_state.evaluations.append(record)
                st.success(f"Evaluation saved for {name.strip()} in this session.")

with tab_compare:
    st.subheader("Compare Buildings")
    if not st.session_state.evaluations:
        st.info("Save at least one evaluation to compare buildings.")
    else:
        df = pd.DataFrame(st.session_state.evaluations)
        st.dataframe(df[["Building", "Location", "Iconicity Level", "Combination",
                         "Achieved Outcomes"]], use_container_width=True, hide_index=True)
        level_order = ["Q1", "Q2", "Q3", "Q4", "Q5", "Not Qualified"]
        counts = df["Iconicity Level"].value_counts().reindex(level_order, fill_value=0)
        fig = go.Figure(go.Bar(
            x=counts.index, y=counts.values,
            marker_color=[LEVEL_COLORS[x] for x in counts.index],
            text=counts.values, textposition="outside"
        ))
        fig.update_layout(title="Distribution of Evaluated Buildings by Iconicity Level",
                          xaxis_title="Iconicity Level", yaxis_title="Number of Buildings",
                          yaxis=dict(rangemode="tozero"), height=380)
        st.plotly_chart(fig, use_container_width=True)

with tab_saved:
    st.subheader("Saved Evaluations")
    if not st.session_state.evaluations:
        st.info("No saved evaluations yet.")
    else:
        df = pd.DataFrame(st.session_state.evaluations)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Download results as CSV", df.to_csv(index=False).encode("utf-8-sig"),
                           file_name="iconicity_evaluations.csv", mime="text/csv")
        if st.button("Clear session evaluations"):
            st.session_state.evaluations = []
            st.rerun()

with tab_rules:
    st.subheader("Model Rules")
    st.markdown("""
- **Core gate:** IV (Iconic Vision), N (Novelty), and A (Applicability) must all be achieved.
- If any Core Requirement is not achieved, the building is **Not Qualified** and excluded from Q1–Q5.
- If all Core Requirements are achieved, classification depends on the number of achieved Complementary Outcomes.

| Level | Combination | Number |
|---|---|---:|
| Q1 | Core + NS + NCI + GA + EG | 1 |
| Q2 | Core + any three outcomes | 4 |
| Q3 | Core + any two outcomes | 6 |
| Q4 | Core + any one outcome | 4 |
| Q5 | Core only | 1 |
| **Total** | | **16** |

The heatmap lists all 16 combinations explicitly. It is a binary model: no averages, weights, or numerical scoring are applied.
""")
