import numpy as np
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="StructuralBeam Pro | Análisis de Vigas",
    page_icon="🏗️",
    layout="wide",
)

# Estilo visual ejecutivo / profesional
st.markdown(
    """
    <style>
    .stApp { background-color: #0e1117; }
    .metric-box {
        background-color: #1e222d;
        border-left: 5px solid #00d4ff;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("🏗️ StructuralBeam Pro: Análisis & Dinámica de Vigas")
st.caption(
    "Plataforma de Cálculo Estructural e Interpretación Mecánica de Vigas Isostáticas"
)

# Sidebar: Entradas Estructurales
st.sidebar.header("📐 Parámetros de la Viga")
L = st.sidebar.number_input(
    "Longitud de la viga L (m):",
    min_value=1.0,
    max_value=30.0,
    value=6.0,
    step=0.5,
)
E = (
    st.sidebar.number_input(
        "Módulo de Elasticidad E (GPa):", min_value=1.0, value=210.0
    )
    * 1e9
)
I_cm4 = st.sidebar.number_input(
    "Inercia de la Sección I (cm⁴):", min_value=10.0, value=8340.0
)
I = I_cm4 * 1e-8  # Convertir a m⁴

st.sidebar.markdown("---")
st.sidebar.header("⚖️ Cargas Aplicadas")

# Carga Puntual
P = st.sidebar.number_input(
    "Carga Puntual P (kN):", min_value=0.0, value=15.0, step=1.0
)
x_P = st.sidebar.slider(
    "Posición de Carga P (m):",
    min_value=0.0,
    max_value=float(L),
    value=float(L / 2),
)

# Carga Distribuida
w = st.sidebar.number_input(
    "Carga Distribuida w (kN/m):", min_value=0.0, value=5.0, step=0.5
)

# ---------------------------------------------------------
# CÁLCULO ESTRUCTURAL (Estática de Vigas Simplemente Apoyadas)
# ---------------------------------------------------------
# Reacciones en apoyos (A en x=0, B en x=L)
# ΣMB = 0 -> Ra*L - P*(L - x_P) - w*L*(L/2) = 0
Ra = (P * (L - x_P) + w * L * (L / 2)) / L
Rb = (P * x_P + w * L * (L / 2)) / L

# Funciones discretas a lo largo de x
x = np.linspace(0, L, 400)
V = np.zeros_like(x)
M = np.zeros_like(x)
y_deflect = np.zeros_like(x)  # Deformación teórica aprox.

for i, xi in enumerate(x):
    # Cortante V(x)
    V[i] = Ra - w * xi - (P if xi >= x_P else 0.0)

    # Momento M(x)
    M[i] = Ra * xi - 0.5 * w * (xi**2) - (P * (xi - x_P) if xi >= x_P else 0.0)

    # Deformación y(x) por carga distribuida y puntual (Aproximación elástica)
    y_w = (w * 1000 * xi / (24 * E * I)) * (L**3 - 2 * L * (xi**2) + xi**3)
    if xi <= x_P:
        y_p = (
            (P * 1000 * (L - x_P) * xi)
            / (6 * E * I * L)
            * (L**2 - (L - x_P) ** 2 - xi**2)
        )
    else:
        y_p = (
            (P * 1000 * x_P * (L - xi))
            / (6 * E * I * L)
            * (L**2 - x_P**2 - (L - xi) ** 2)
        )
    y_deflect[i] = -(y_w + y_p) * 1000  # Convertir a mm

# Resultados Principales
st.subheader("📊 Resultados de Reacciones y Esfuerzos Máximos")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Reacción A (Ra)", f"{Ra:.2f} kN")
c2.metric("Reacción B (Rb)", f"{Rb:.2f} kN")
c3.metric("Cortante Máx. |Vmax|", f"{np.max(np.abs(V)):.2f} kN")
c4.metric("Momento Máx. |Mmax|", f"{np.max(np.abs(M)):.2f} kN.m")

# ---------------------------------------------------------
# ANIMACIÓN / DCL DINÁMICO EN MOVIMIENTO
# ---------------------------------------------------------
st.write("---")
st.subheader(
    "🎥 Diagrama de Cuerpo Libre y Simulación de Flexión Dinámica"
)
st.caption(
    "La animación muestra la oscilación elástica y la respuesta de deformación de la viga bajo carga."
)

amp = st.slider(
    "Escala de animación de flexión:",
    min_value=1.0,
    max_value=10.0,
    value=3.0,
)

# Generación de fotogramas para animación interactiva con Plotly
frames = []
t_steps = np.linspace(0, 2 * np.pi, 30)

for t in t_steps:
    # Simulación de deformada vibratoria sintonizada
    y_dynamic = y_deflect * (1 + 0.25 * np.sin(t)) * (amp / 5)

    frame_data = [
        # Viga Deformada dinámicamente
        go.Scatter(
            x=x,
            y=y_dynamic,
            mode="lines",
            line=dict(color="#00d4ff", width=6),
            name="Viga Deformada",
        ),
        # Apoyo A
        go.Scatter(
            x=[0],
            y=[y_dynamic[0]],
            mode="markers+text",
            marker=dict(symbol="triangle-up", size=18, color="#00ff87"),
            text=["Apoyo A (Fijo)"],
            textposition="bottom center",
            name="Apoyo A",
        ),
        # Apoyo B
        go.Scatter(
            x=[L],
            y=[y_dynamic[-1]],
            mode="markers+text",
            marker=dict(symbol="circle", size=16, color="#00ff87"),
            text=["Apoyo B (Móvil)"],
            textposition="bottom center",
            name="Apoyo B",
        ),
        # Vector Carga P
        go.Scatter(
            x=[x_P, x_P],
            y=[
                y_dynamic[int(len(x) * (x_P / L))] + (P * 0.1),
                y_dynamic[int(len(x) * (x_P / L))],
            ],
            mode="lines+markers",
            line=dict(color="#ff2a6d", width=4),
            marker=dict(symbol="arrow-bar-up", size=10),
            name=f"P = {P} kN",
        ),
    ]
    frames.append(go.Frame(data=frame_data))

# Figura Inicial
fig_anim = go.Figure(
    data=[
        go.Scatter(
            x=x,
            y=y_deflect * (amp / 5),
            mode="lines",
            line=dict(color="#00d4ff", width=6),
            name="Viga",
        ),
        go.Scatter(
            x=[0],
            y=[0],
            mode="markers+text",
            marker=dict(symbol="triangle-up", size=18, color="#00ff87"),
            text=["Apoyo A"],
            textposition="bottom center",
        ),
        go.Scatter(
            x=[L],
            y=[0],
            mode="markers+text",
            marker=dict(symbol="circle", size=16, color="#00ff87"),
            text=["Apoyo B"],
            textposition="bottom center",
        ),
        go.Scatter(
            x=[x_P, x_P],
            y=[P * 0.1, 0],
            mode="lines+markers",
            line=dict(color="#ff2a6d", width=4),
            name=f"P = {P} kN",
        ),
    ],
    layout=go.Layout(
        xaxis=dict(range=[-0.5, L + 0.5], title="Posición a lo largo del eje x (m)"),
        yaxis=dict(
            range=[np.min(y_deflect) * (amp / 2) - 5, 5],
            title="Deflexión / Oscilación (mm)",
        ),
        template="plotly_dark",
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(
                        label="▶️ Iniciar Animación",
                        method="animate",
                        args=[
                            None,
                            dict(
                                frame=dict(duration=50, redraw=True),
                                fromcurrent=True,
                            ),
                        ],
                    ),
                    dict(
                        label="⏸️ Pausar",
                        method="animate",
                        args=[
                            [None],
                            dict(
                                frame=dict(duration=0, redraw=False),
                                mode="immediate",
                            ),
                        ],
                    ),
                ],
            )
        ],
    ),
    frames=frames,
)

st.plotly_chart(fig_anim, use_container_width=True)

# ---------------------------------------------------------
# DIAGRAMAS DE ESFUERZOS INTERNOS (V y M)
# ---------------------------------------------------------
st.write("---")
st.subheader("📈 Diagramas de Esfuerzos Internos (V & M)")

col_v, col_m = st.columns(2)

with col_v:
    fig_v = go.Figure()
    fig_v.add_trace(
        go.Scatter(
            x=x,
            y=V,
            fill="tozeroy",
            line=dict(color="#00d4ff", width=2),
            name="Cortante V(x)",
        )
    )
    fig_v.update_layout(
        title="Diagrama de Fuerza Cortante (V)",
        xaxis_title="x (m)",
        yaxis_title="V (kN)",
        template="plotly_dark",
    )
    st.plotly_chart(fig_v, use_container_width=True)

with col_m:
    fig_m = go.Figure()
    fig_m.add_trace(
        go.Scatter(
            x=x,
            y=M,
            fill="tozeroy",
            line=dict(color="#ff2a6d", width=2),
            name="Momento M(x)",
        )
    )
    fig_m.update_layout(
        title="Diagrama de Momento Flector (M)",
        xaxis_title="x (m)",
        yaxis_title="M (kN.m)",
        template="plotly_dark",
    )
    st.plotly_chart(fig_m, use_container_width=True)