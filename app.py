import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from itertools import combinations

st.set_page_config(page_title="Iconic Buildings Evaluation tool", page_icon="◆", layout="wide")

LEVEL_COLORS = {
    "Q1": "#87945C",  # olive
    "Q2": "#4F9690",  # teal
    "Q3": "#D6A45D",  # amber
    "Q4": "#C77F80",  # rose
    "Q5": "#A7839C",  # mauve
    "Not Qualified": "#777777",
}

OUTCOMES = {
    "NS": "New Symbolism",
    "NCI": "New City Image",
    "GA": "Global Attachment",
    "EG": "Economic Growth",
}
CORE = {
    "IV": "Iconic Vision",
    "N": "Novelty",
    "A": "Applicability",
}

def classify(values):
    """Apply the user's binary evaluation rules without numerical scoring."""
    if not all(bool(values[k]) for k in CORE):
        return "Not Qualified", 0, []
    achieved = [code for code in OUTCOMES if bool(values[code])]
    count = len(achieved)
    level = {4: "Q1", 3: "Q2", 2: "Q3", 1: "Q4", 0: "Q5"}[count]
    return level, count, achieved

def combination_text(level, achieved):
    if level == "Not Qualified":
        return "Core requirements not fully achieved"
    if level == "Q5":
        return "Core requirements only"
    return " + ".join(achieved)

def make_matrix_figure(level, achieved):
    # Five stacked diamond-shaped layers; selected outcome-combination
    # is highlighted on its corresponding level.
    fig = go.Figure()
    layer_specs = [
        ("Q5", 0, [tuple()]),
        ("Q4", 1, list(combinations(["NS", "NCI", "GA", "EG"], 1))),
        ("Q3", 2, list(combinations(["NS", "NCI", "GA", "EG"], 2))),
        ("Q2", 3, list(combinations(["NS", "NCI", "GA", "EG"], 3))),
        ("Q1", 4, [tuple(["NS", "NCI", "GA", "EG"])]),
    ]
    # Use a diamond lattice layout; each layer is a translucent horizontal
    # diamond plane. The selected layer is emphasized.
    for q, z, combos in layer_specs:
        xs, ys, zs, labels, colors, sizes = [], [], [], [], [], []
        for i, combo in enumerate(combos):
            # Deterministic positions distributed around the layer's diamond.
            if len(combos) == 1:
                x, y = 0, 0
            elif len(combos) == 4:
                positions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
                x, y = positions[i]
            elif len(combos) == 6:
                positions = [(-1, 0), (-0.5, 0.8), (0.5, 0.8),
                             (1, 0), (0.5, -0.8), (-0.5, -0.8)]
                x, y = positions[i]
            else:
                positions = [(-0.6, 0.5), (0.6, 0.5), (0, -0.7), (0, 0)]
                x, y = positions[i]
            selected = (q == level and set(combo) == set(achieved))
            xs.append(x); ys.append(y); zs.append(z)
            labels.append(q if not combo else " + ".join(combo))
            colors.append(LEVEL_COLORS[q] if selected else "#D8D2C8")
            sizes.append(23 if selected else 13)
        fig.add_trace(go.Scatter3d(
            x=xs, y=ys, z=zs, mode="markers+text",
            text=labels, textposition="top center",
            marker=dict(size=sizes, color=colors, opacity=0.95,
                        line=dict(color="#514B46", width=1)),
            name=q, hovertemplate="%{text}<extra>" + q + "</extra>"
        ))
    fig.update_layout(
        height=560, margin=dict(l=0, r=0, t=10, b=0),
        scene=dict(
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            zaxis=dict(visible=False, range=[-0.5, 4.7]),
            camera=dict(eye=dict(x=1.7, y=1.7, z=1.3)),
            aspectmode="manual", aspectratio=dict(x=1.2, y=1.2, z=1.5),
            bgcolor="rgba(0,0,0,0)"
        ),
        paper_bgcolor="rgba(0,0,0,0)", showlegend=False
    )
    return fig

if "evaluations" not in st.session_state:
    st.session_state.evaluations = []

st.title("3D Iconic Buildings Evaluation Tool")
st.caption("Binary evaluation tool based on the 5-level, 16-combination model.")

with st.sidebar:
    st.header("Evaluation rules")
    st.markdown("**Core requirements (all three are mandatory):**")
    st.markdown("- IV — Iconic Vision\n- N — Novelty\n- A — Applicability")
    st.markdown("**Complementary outcomes:**")
    for code, label in OUTCOMES.items():
        st.markdown(f"- {code} — {label}")
    st.info("If any core requirement is not achieved, the building is Not Qualified, regardless of complementary outcomes.")

tab_eval, tab_compare, tab_method = st.tabs(["Evaluate a building", "Compare buildings", "Model rules"])

with tab_eval:
    st.subheader("1. Building information")
    name = st.text_input("Building name", placeholder="e.g. Sydney Opera House")
    location = st.text_input("Location", placeholder="City, Country")
    year = st.text_input("Completion year (optional)", placeholder="e.g. 1973")

    st.subheader("2. Binary assessment")
    st.write("Select **Achieved** or **Not achieved** for each criterion.")
    left, right = st.columns(2)
    values = {}
    with left:
        st.markdown("#### Core requirements")
        for code, label in CORE.items():
            values[code] = st.radio(label, ["Achieved", "Not achieved"],
                                    horizontal=True, key=f"core_{code}") == "Achieved"
    with right:
        st.markdown("#### Complementary iconic outcomes")
        for code, label in OUTCOMES.items():
            values[code] = st.radio(label, ["Achieved", "Not achieved"],
                                    horizontal=True, key=f"out_{code}") == "Achieved"

    level, count, achieved = classify(values)
    st.divider()
    st.subheader("3. Automatic classification")
    c1, c2, c3 = st.columns(3)
    c1.metric("Iconicity level", level)
    c2.metric("Complementary outcomes achieved", f"{count}/4" if level != "Not Qualified" else f"{count}/4")
    c3.metric("Combination", combination_text(level, achieved))
    if level == "Not Qualified":
        st.error("Not Qualified — at least one Core Requirement is not achieved. The building is excluded from Q1–Q5 classification.")
    else:
        st.success(f"{level} Iconicity — {combination_text(level, achieved)}")
    st.plotly_chart(make_matrix_figure(level, achieved), use_container_width=True)
    st.caption("The highlighted marker identifies the evaluated combination. The diagram is a schematic interactive representation of the supplied stacked-diamond matrix.")

    if st.button("Save this building evaluation", type="primary", disabled=not name.strip()):
        record = {
            "Building": name.strip(),
            "Location": location.strip(),
            "Year": year.strip(),
            **{CORE[k]: "Achieved" if values[k] else "Not achieved" for k in CORE},
            **{OUTCOMES[k]: "Achieved" if values[k] else "Not achieved" for k in OUTCOMES},
            "Iconicity Level": level,
            "Achieved Outcomes": ", ".join(achieved) if achieved else ("None" if level != "Not Qualified" else "Not classified"),
            "Combination": combination_text(level, achieved),
        }
        st.session_state.evaluations = [
            r for r in st.session_state.evaluations if r["Building"].casefold() != name.strip().casefold()
        ]
        st.session_state.evaluations.append(record)
        st.success(f"Saved evaluation for {name.strip()}.")

with tab_compare:
    st.subheader("Saved building evaluations")
    if not st.session_state.evaluations:
        st.info("No saved evaluations yet. Evaluate and save a building in the first tab.")
    else:
        df = pd.DataFrame(st.session_state.evaluations)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Download results as CSV", df.to_csv(index=False).encode("utf-8-sig"),
                           file_name="iconicity_evaluations.csv", mime="text/csv")
        qualified = df[df["Iconicity Level"] != "Not Qualified"]
        if not qualified.empty:
            order = ["Q1", "Q2", "Q3", "Q4", "Q5", "Not Qualified"]
            chart_df = df.copy()
            chart_df["Iconicity Level"] = pd.Categorical(chart_df["Iconicity Level"], categories=order, ordered=True)
            chart_df = chart_df.sort_values("Iconicity Level")
            fig = go.Figure(go.Bar(
                x=chart_df["Building"], y=chart_df["Iconicity Level"].astype(str),
                marker_color=[LEVEL_COLORS[x] for x in chart_df["Iconicity Level"].astype(str)],
                text=chart_df["Iconicity Level"].astype(str), textposition="outside"
            ))
            fig.update_layout(title="Iconicity classification comparison", xaxis_title="Building",
                              yaxis_title="Classification", yaxis=dict(categoryorder="array",
                              categoryarray=order[::-1]), height=400)
            st.plotly_chart(fig, use_container_width=True)
        if st.button("Clear all saved evaluations"):
            st.session_state.evaluations = []
            st.rerun()

with tab_method:
    st.subheader("Classification logic")
    st.markdown("""
**Core gate:** Q5 is eligible only when all three core requirements are achieved:
`IV AND N AND A`.

If any one of them is not achieved, the result is **Not Qualified**, even if all four complementary outcomes are achieved.

| Level | Rule | Number of combinations |
|---|---|---:|
| Q1 | Core + NS + NCI + GA + EG | 1 |
| Q2 | Core + any three complementary outcomes | 4 |
| Q3 | Core + any two complementary outcomes | 6 |
| Q4 | Core + any one complementary outcome | 4 |
| Q5 | Core requirements only | 1 |
| **Total** | | **16** |

The tool uses binary inputs and does not calculate averages, percentages, or weighted scores.
""")
    st.warning("Before academic use, verify that the written definitions and operational indicators for each criterion are finalized in the thesis. This app implements the logical rules shown in the supplied matrix.")
