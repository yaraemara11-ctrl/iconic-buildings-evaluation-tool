import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math

st.set_page_config(
    page_title="Iconic Buildings Evaluation Model",
    page_icon="◆",
    layout="wide"
)

# Official palette approved for both visualizations
LEVEL_COLORS = {
    "Q1": "#A6A875",  # muted olive / sage
    "Q2": "#6FA8A1",  # muted teal
    "Q3": "#E2B66B",  # warm ochre
    "Q4": "#C98282",  # dusty rose
    "Q5": "#A78FA7",  # muted mauve
}
ACHIEVED = "#7A1831"
NOT_INCLUDED = "#F1D0D0"
SELECTED = "#74152E"
INK = "#20333D"
WHITE = "#FFFFFF"

CORE = {
    "IV": "Iconic Vision",
    "N": "Novelty",
    "A": "Applicability",
}
OUTCOMES = {
    "NS": "New Symbolism",
    "NCI": "New City Image",
    "GA": "Global Attachment",
    "EG": "Economic Growth",
}

# Exactly 16 combinations: 1 + 4 + 6 + 4 + 1
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

LEVEL_RULES = {
    "Q1": "Core + all four complementary outcomes",
    "Q2": "Core + any three complementary outcomes",
    "Q3": "Core + any two complementary outcomes",
    "Q4": "Core + any one complementary outcome",
    "Q5": "Core requirements only",
}

def classify(values):
    if not all(values[k] for k in CORE):
        return "Not Qualified", [], None
    achieved = [k for k in OUTCOMES if values[k]]
    n = len(achieved)
    level = {4: "Q1", 3: "Q2", 2: "Q3", 1: "Q4", 0: "Q5"}[n]
    combo_id = next(
        cid for cid, q, members in COMBINATIONS
        if q == level and set(members) == set(achieved)
    )
    return level, achieved, combo_id

def add_cube(fig, cx, cy, z0, width, height, color, selected=False, label="", level_selected=False):
    """Draw one raised isometric diamond tile with visible side faces."""
    half = width / 2
    # A square rotated 45 degrees reads as a diamond from the camera angle.
    base = [(-half, 0), (0, half), (half, 0), (0, -half)]
    verts = [(cx + x, cy + y, z0) for x, y in base]
    verts += [(cx + x, cy + y, z0 + height) for x, y in base]
    xs, ys, zs = zip(*verts)

    # Top face plus four side faces.
    faces = [
        (4, 5, 6), (4, 6, 7),
        (0, 1, 5), (0, 5, 4),
        (1, 2, 6), (1, 6, 5),
        (2, 3, 7), (2, 7, 6),
        (3, 0, 4), (3, 4, 7),
    ]
    ii, jj, kk = zip(*faces)
    fig.add_trace(go.Mesh3d(
        x=xs, y=ys, z=zs, i=ii, j=jj, k=kk,
        color=color, opacity=1,
        flatshading=True, showscale=False,
        hovertext=label, hoverinfo="text",
        lighting=dict(ambient=0.78, diffuse=0.72, specular=0.12, roughness=0.9),
        lightposition=dict(x=100, y=100, z=150),
    ))

    # Fine cream seams keep the stacked-diamond construction legible.
    outline = verts[4:] + [verts[4]]
    fig.add_trace(go.Scatter3d(
        x=[v[0] for v in outline],
        y=[v[1] for v in outline],
        z=[v[2] + 0.008 for v in outline],
        mode="lines",
        line=dict(color="#F8F0E8", width=3),
        hoverinfo="skip", showlegend=False
    ))
    if level_selected:
        # Bright outline around every tile in the evaluated level.
        fig.add_trace(go.Scatter3d(
            x=[v[0] for v in outline],
            y=[v[1] for v in outline],
            z=[v[2] + 0.020 for v in outline],
            mode="lines",
            line=dict(color="#FFF8E8", width=10),
            hoverinfo="skip", showlegend=False
        ))
    if selected:
        # Amber outline pinpoints the exact combination within the highlighted level.
        fig.add_trace(go.Scatter3d(
            x=[v[0] for v in outline],
            y=[v[1] for v in outline],
            z=[v[2] + 0.032 for v in outline],
            mode="lines",
            line=dict(color="#7A1831", width=13),
            hoverinfo="skip", showlegend=False
        ))

    # Abbreviations are shown on the top face; full combination is in hover.
    short_label = label.split(": ", 1)[-1].replace(" + ", "<br>")
    if short_label == "Core requirements":
        short_label = "Q5<br>Core"
    label_color = "#3B2630" if color in (LEVEL_COLORS["Q3"], LEVEL_COLORS["Q4"]) else "#FFFFFF"
    fig.add_trace(go.Scatter3d(
        x=[cx], y=[cy], z=[z0 + height + 0.035],
        mode="text", text=[short_label],
        textfont=dict(size=9 if width < 1.1 else 11, color=label_color),
        hoverinfo="skip", showlegend=False
    ))


def make_3d_diamond(selected_id, selected_level):
    """Layered 3D diamond with evaluated level illuminated."""
    fig = go.Figure()
    combo_map = {cid: members for cid, level, members in COMBINATIONS}

    # Core foundation: a broad mauve diamond platform.
    add_cube(
        fig, 0, 0, 0.0, 4.0, 0.38, LEVEL_COLORS["Q5"],
        selected=selected_id == "C16",
        label="C16: Core requirements",
        level_selected=(selected_level == "Q5")
    )

    # Q4: four single-outcome tiles around the foundation.
    q4_positions = [(-1.05, 0), (0, 1.05), (1.05, 0), (0, -1.05)]
    for (x, y), cid in zip(q4_positions, ["C12", "C13", "C14", "C15"]):
        add_cube(
            fig, x, y, 0.48, 1.22, 0.38, LEVEL_COLORS["Q4"],
            selected=selected_id == cid,
            label=f"{cid}: {' + '.join(combo_map[cid])}",
            level_selected=(selected_level == "Q4")
        )

    # Q3: six two-outcome tiles.
    q3_positions = [
        (-1.55, 0.0), (-0.78, 1.35), (0.78, 1.35),
        (1.55, 0.0), (0.78, -1.35), (-0.78, -1.35)
    ]
    for (x, y), cid in zip(q3_positions, ["C6", "C7", "C8", "C9", "C10", "C11"]):
        add_cube(
            fig, x, y, 0.96, 1.05, 0.38, LEVEL_COLORS["Q3"],
            selected=selected_id == cid,
            label=f"{cid}: {' + '.join(combo_map[cid])}",
            level_selected=(selected_level == "Q3")
        )

    # Q2: four three-outcome tiles.
    q2_positions = [(-0.68, 0.68), (0.68, 0.68), (-0.68, -0.68), (0.68, -0.68)]
    for (x, y), cid in zip(q2_positions, ["C2", "C3", "C4", "C5"]):
        add_cube(
            fig, x, y, 1.44, 1.18, 0.38, LEVEL_COLORS["Q2"],
            selected=selected_id == cid,
            label=f"{cid}: {' + '.join(combo_map[cid])}",
            level_selected=(selected_level == "Q2")
        )

    # Q1: single top tile with all four complementary outcomes.
    add_cube(
        fig, 0, 0, 1.92, 1.35, 0.48, LEVEL_COLORS["Q1"],
        selected=selected_id == "C1",
        label="C1: NS + NCI + GA + EG",
        level_selected=(selected_level == "Q1")
    )

    fig.update_layout(
        height=820,
        margin=dict(l=0, r=0, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        scene=dict(
            xaxis=dict(visible=False, range=[-2.45, 2.45]),
            yaxis=dict(visible=False, range=[-2.45, 2.45]),
            zaxis=dict(visible=False, range=[0, 2.65]),
            aspectmode="manual",
            aspectratio=dict(x=1.28, y=1.28, z=0.92),
            camera=dict(eye=dict(x=1.35, y=1.50, z=1.18)),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=False,
    )
    return fig


def make_heatmap(selected_id):
    xlabels = ["IV", "N", "A", "NS", "NCI", "GA", "EG"]
    ylabels, z, text = [], [], []
    for cid, level, members in COMBINATIONS:
        ylabels.append(f"{level} · {cid}")
        row = [1, 1, 1] + [1 if key in members else 0 for key in ["NS", "NCI", "GA", "EG"]]
        z.append(row)
        text.append(["✓" if v else "–" for v in row])

    fig = go.Figure(go.Heatmap(
        z=z, x=xlabels, y=ylabels, zmin=0, zmax=1,
        colorscale=[[0, NOT_INCLUDED], [0.499, NOT_INCLUDED],
                    [0.5, ACHIEVED], [1, ACHIEVED]],
        showscale=False, text=text, texttemplate="%{text}",
        xgap=5, ygap=5,
        hovertemplate="Combination: %{y}<br>Criterion: %{x}<br>Status: %{text}<extra></extra>"
    ))
    if selected_id:
        row_index = [c[0] for c in COMBINATIONS].index(selected_id)
        fig.add_shape(
            type="rect", xref="paper", yref="y",
            x0=0, x1=1, y0=row_index - 0.48, y1=row_index + 0.48,
            line=dict(color="#C58B32", width=4),
            fillcolor="rgba(0,0,0,0)"
        )
    fig.update_layout(
        height=620,
        margin=dict(l=10, r=10, t=35, b=10),
        xaxis=dict(side="top", tickfont=dict(size=13), fixedrange=True),
        yaxis=dict(autorange="reversed", tickfont=dict(size=12), fixedrange=True),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=INK),
    )
    return fig

if "evaluations" not in st.session_state:
    st.session_state.evaluations = []

st.title("Iconic Buildings Evaluation Model")
st.caption("Interactive Evaluation Dashboard · 3D Stacked Diamond + 16-Combination Heatmap")

evaluate_tab, compare_tab, saved_tab, rules_tab = st.tabs(
    ["Evaluate a Building", "Compare Buildings", "Saved Evaluations", "Model Rules"]
)

with evaluate_tab:
    left, right = st.columns([0.85, 1.6], gap="large")
    with left:
        st.subheader("1. Building Information")
        building = st.text_input("Building name", placeholder="e.g. Sydney Opera House")
        location = st.text_input("Location", placeholder="City, Country")
        year = st.text_input("Completion year (optional)", placeholder="e.g. 1973")

        st.subheader("2. Evaluation Criteria")
        st.markdown("**Core Requirements — all three are mandatory**")
        values = {}
        for key, label in CORE.items():
            values[key] = st.checkbox(f"{key} — {label}", key=f"core_{key}")
        st.divider()
        st.markdown("**Complementary Outcomes**")
        for key, label in OUTCOMES.items():
            values[key] = st.checkbox(f"{key} — {label}", key=f"out_{key}")
        save_clicked = st.button("Evaluate & Save Building", type="primary", use_container_width=True)

    level, achieved, combo_id = classify(values)
    with right:
        st.subheader("3. Linked Visual Evaluation")
        m1, m2, m3 = st.columns(3)
        m1.metric("Iconicity Level", level)
        m2.metric("Combination", combo_id or "—")
        m3.metric("Outcomes Achieved", f"{len(achieved)}/4")

        if level == "Not Qualified":
            st.warning("Not Qualified: all three Core Requirements must be achieved. This result is outside Q1–Q5.")
        else:
            st.success(f"{level} Iconicity · {combo_id} — {LEVEL_RULES[level]}")

        st.markdown("#### 3D Stacked Diamond Model")
        st.caption("The full evaluated level is illuminated with a bright outline; the exact combination is emphasized in amber. Rotate or zoom to inspect the model.")
        st.plotly_chart(make_3d_diamond(combo_id, level if level != "Not Qualified" else None), use_container_width=True,
                        config={"displayModeBar": True, "scrollZoom": True})
        st.markdown("**Model highlight:** bright cream outline = evaluated level · amber outline = exact combination")

        st.markdown("#### Interactive Combination Heatmap")
        st.caption("The amber outline marks the same combination highlighted in the 3D model.")
        st.plotly_chart(make_heatmap(combo_id), use_container_width=True,
                        config={"displayModeBar": False})
        st.markdown(
            f"<span style='color:{ACHIEVED};font-weight:700'>■ Achieved / included</span>"
            f"&nbsp;&nbsp;&nbsp; <span style='color:#D7A6A9;font-weight:700'>■ Not included</span>"
            f"&nbsp;&nbsp;&nbsp; <span style='color:{SELECTED};font-weight:700'>▱ Selected combination</span>",
            unsafe_allow_html=True
        )

        if save_clicked:
            if not building.strip():
                st.error("Please enter a building name before saving.")
            else:
                record = {
                    "Building": building.strip(),
                    "Location": location.strip(),
                    "Year": year.strip(),
                    **{CORE[k]: "Achieved" if values[k] else "Not achieved" for k in CORE},
                    **{OUTCOMES[k]: "Achieved" if values[k] else "Not achieved" for k in OUTCOMES},
                    "Iconicity Level": level,
                    "Combination": combo_id or "Not Qualified",
                    "Achieved Outcomes": ", ".join(achieved) if achieved else "None",
                }
                st.session_state.evaluations = [
                    r for r in st.session_state.evaluations
                    if r["Building"].casefold() != building.strip().casefold()
                ]
                st.session_state.evaluations.append(record)
                st.success(f"Saved evaluation for {building.strip()} in this session.")

with compare_tab:
    st.subheader("Building Comparison")
    if not st.session_state.evaluations:
        st.info("Evaluate and save buildings to compare their results.")
    else:
        df = pd.DataFrame(st.session_state.evaluations)
        st.dataframe(df[["Building", "Location", "Iconicity Level", "Combination", "Achieved Outcomes"]],
                     use_container_width=True, hide_index=True)
        level_order = ["Q1", "Q2", "Q3", "Q4", "Q5", "Not Qualified"]
        counts = df["Iconicity Level"].value_counts().reindex(level_order, fill_value=0)
        bar_colors = [LEVEL_COLORS.get(x, "#8A8A8A") for x in level_order]
        fig = go.Figure(go.Bar(x=level_order, y=counts.values, marker_color=bar_colors,
                               text=counts.values, textposition="outside"))
        fig.update_layout(title="Buildings by Iconicity Level", height=380,
                          xaxis_title="Iconicity Level", yaxis_title="Number of Buildings")
        st.plotly_chart(fig, use_container_width=True)

with saved_tab:
    st.subheader("Saved Evaluations")
    if not st.session_state.evaluations:
        st.info("No saved evaluations in this session yet.")
    else:
        df = pd.DataFrame(st.session_state.evaluations)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Download results as CSV",
                           df.to_csv(index=False).encode("utf-8-sig"),
                           file_name="iconicity_evaluations.csv",
                           mime="text/csv")
        if st.button("Clear session evaluations"):
            st.session_state.evaluations = []
            st.rerun()

with rules_tab:
    st.subheader("Evaluation Model Rules")
    st.markdown("""
**Core Requirements:** Iconic Vision (IV), Novelty (N), and Applicability (A).
All three are mandatory. If any one is not achieved, the building is **Not Qualified**
and remains outside the Q1–Q5 classification.

| Level | Rule | Combinations |
|---|---|---:|
| Q1 | Core + NS + NCI + GA + EG | 1 |
| Q2 | Core + any three outcomes | 4 |
| Q3 | Core + any two outcomes | 6 |
| Q4 | Core + any one outcome | 4 |
| Q5 | Core only | 1 |
| **Total** | | **16** |

**Complementary Outcomes:** NS — New Symbolism; NCI — New City Image;
GA — Global Attachment; EG — Economic Growth.

The 3D Stacked Diamond and the Heatmap use the same 16-combination model.
The amber outline identifies the evaluated combination in both visualizations.
""")
