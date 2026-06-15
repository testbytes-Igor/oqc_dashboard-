import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="OQC Dashboard",
    layout="wide",
    page_icon="📊"
)

# =========================
# CSS - Tema Escuro Midea
# =========================

st.markdown("""
<style>

.stApp {
    background-color: #000000;
    color: white;
}

div[data-testid="stMetric"] {
    background-color: #1a1a1a;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #333;
}

.block-container {
    padding-top: 1rem;
}

h1, h2, h3 {
    color: white;
}

</style>
""", unsafe_allow_html=True)

st.title("📊 OQC Dashboard")
st.caption("Visão Geral da Qualidade - OQC")

# =========================
# Upload
# =========================
arquivo = st.sidebar.file_uploader(
    "Upload OQC",
    type=["csv", "xlsx"]
)

if arquivo:

    if arquivo.name.endswith(".xlsx"):
        df = pd.read_excel(arquivo)

    elif arquivo.name.endswith(".csv"):
        # CSV brasileiro geralmente usa ;
        df = pd.read_csv(arquivo, sep=";")

    else:
        st.error("Formato não suportado.")
        st.stop()

else:
    st.info("Faça upload de um arquivo CSV ou Excel.")
    st.stop()
# Limpa espaços extras nos nomes das colunas
# Cria colunas faltantes automaticamente
if "Linha" not in df.columns:
    df["Linha"] = "N/A"

if "Inspetor" not in df.columns:
    df["Inspetor"] = "N/A"

# Mostra as colunas encontradas
#st.write("Colunas encontradas:", list(df.columns))

# Verifica se existe a coluna Data
if "Data" not in df.columns:
    st.error(
        f"Coluna 'Data' não encontrada. "
        f"Colunas encontradas: {list(df.columns)}"
    )
    st.stop()

# Converte para data
df["Data"] = pd.to_datetime(
    df["Data"],
    dayfirst=True,
    errors="coerce"
)

# =========================
# Filtros
# =========================

st.sidebar.header("Filtros")

# Remove valores vazios/NaN
modelos = sorted(df["Modelo"].dropna().astype(str).unique())
turnos = sorted(df["Turno"].dropna().astype(str).unique())

modelo = st.sidebar.multiselect(
    "Modelo",
    modelos,
    default=modelos
)

turno = st.sidebar.multiselect(
    "Turno",
    turnos,
    default=turnos
)

df["Modelo"] = df["Modelo"].astype(str)
df["Turno"] = df["Turno"].astype(str)

df = df[
    (df["Modelo"].isin(modelo)) &
    (df["Turno"].isin(turno))
]

# =========================
# KPIs
# =========================

total_inspecionado = df["Qtd_Inspecionada"].sum()
total_defeitos = df["Qtd_Defeitos"].sum()

fpy = (
    (total_inspecionado - total_defeitos)
    / total_inspecionado
) * 100

ppm = (
    total_defeitos
    / total_inspecionado
) * 1000000

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "FPY TOTAL",
    f"{fpy:.1f}%"
)

col2.metric(
    "INSPECIONADO",
    f"{total_inspecionado:,}"
)

col3.metric(
    "DEFEITOS",
    f"{total_defeitos:,}"
)

col4.metric(
    "PPM",
    f"{ppm:,.0f}"
)

st.divider()

# =========================
# Top Defeitos
# =========================

c1, c2 = st.columns(2)

with c1:

    top_def = (
        df.groupby("Defeito")["Qtd_Defeitos"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    fig = px.bar(
        top_def,
        x="Qtd_Defeitos",
        y="Defeito",
        orientation="h",
        title="TOP 10 DEFEITOS",
        template="plotly_dark"
    )

    fig.update_layout(
        paper_bgcolor='black',
        plot_bgcolor='black',
        font_color='white'
    )

    st.plotly_chart(fig, use_container_width=True)

with c2:

    linha = (
        df.groupby("Modelo")["Qtd_Defeitos"]
        .sum()
        .reset_index()
    )

    fig2 = px.bar(
        linha,
        x="Modelo",
        y="Qtd_Defeitos",
        title="DEFEITOS POR MODELO",
        template="plotly_dark"
    )

    fig2.update_layout(
        paper_bgcolor='black',
        plot_bgcolor='black',
        font_color='white'
    )

    st.plotly_chart(fig2, use_container_width=True)

# =========================
# FPY Diário
# =========================

df_dia = (
    df.groupby("Data")
    .agg({
        "Qtd_Inspecionada":"sum",
        "Qtd_Defeitos":"sum"
    })
    .reset_index()
)

df_dia["FPY"] = (
    (
        df_dia["Qtd_Inspecionada"]
        - df_dia["Qtd_Defeitos"]
    )
    /
    df_dia["Qtd_Inspecionada"]
) * 100

fig3 = go.Figure()

fig3.add_trace(
    go.Scatter(
        x=df_dia["Data"],
        y=df_dia["FPY"],
        mode="lines+markers",
        name="FPY"
    )
)

fig3.update_layout(
    title="FPY POR DATA",
    template="plotly_dark",
    paper_bgcolor='black',
    plot_bgcolor='black',
    font_color='white',
    yaxis_title="FPY (%)"
)

st.plotly_chart(fig3, use_container_width=True)

# =========================
# Turno
# =========================

c3, c4 = st.columns(2)

with c3:

    turno_df = (
        df.groupby("Turno")
        .agg({
            "Qtd_Inspecionada":"sum",
            "Qtd_Defeitos":"sum"
        })
        .reset_index()
    )

    fig4 = px.bar(
        turno_df,
        x="Turno",
        y="Qtd_Defeitos",
        title="DEFEITOS POR TURNO",
        template="plotly_dark"
    )

    fig4.update_layout(
        paper_bgcolor='black',
        plot_bgcolor='black',
        font_color='white'
    )

    st.plotly_chart(fig4, use_container_width=True)

with c4:

    fig5 = px.pie(
        top_def.head(5),
        names="Defeito",
        values="Qtd_Defeitos",
        title="PARETO DOS DEFEITOS",
        template="plotly_dark"
    )

    fig5.update_layout(
        paper_bgcolor='black',
        plot_bgcolor='black',
        font_color='white'
    )

    st.plotly_chart(fig5, use_container_width=True)

st.divider()

st.dataframe(df, use_container_width=True)