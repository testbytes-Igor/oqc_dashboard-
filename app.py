import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================

st.set_page_config(
    page_title="OQC Dashboard",
    layout="wide",
    page_icon="📊"
)

# =====================================================
# CSS - Tema Escuro Industrial
# =====================================================

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

# =====================================================
# UPLOAD
# =====================================================

arquivo = st.sidebar.file_uploader(
    "Upload OQC",
    type=["csv", "xlsx"]
)

if arquivo:

    try:

        if arquivo.name.endswith(".xlsx"):
            df = pd.read_excel(arquivo)

        elif arquivo.name.endswith(".csv"):

            try:
                df = pd.read_csv(
                arquivo,
                sep=";",
                encoding="utf-8-sig"
    )

            except:
                arquivo.seek(0)
                df = pd.read_csv(
                arquivo,
                sep=";",
                encoding="cp1252"
    )

        else:
            st.error("Formato não suportado.")
            st.stop()

    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")
        st.stop()

else:
    st.info("Faça upload de um arquivo CSV ou Excel.")
    st.stop()

# =====================================================
# LIMPEZA DOS DADOS
# =====================================================

df.columns = df.columns.str.strip()
df.columns = (
    df.columns
    .str.strip()
    .str.replace("\ufeff", "", regex=False)
    .str.replace("ï»¿", "", regex=False)
)
df = df.dropna(how="all")

# Cria colunas faltantes automaticamente
colunas_padrao = {
    "Linha": "N/A",
    "Inspetor": "N/A",
    "Categoria": "N/A",
    "Severidade": "N/A",
    "Status": "N/A",
    "Qtd_Defeitos": 0,
    "Qtd_Inspecionada": 0
}

for col, valor in colunas_padrao.items():
    if col not in df.columns:
        df[col] = valor

# Validação
if "Data" not in df.columns:
    st.error(f"Coluna 'Data' não encontrada. Colunas: {list(df.columns)}")
    st.stop()

if "Modelo" not in df.columns:
    st.error("Coluna 'Modelo' não encontrada.")
    st.stop()

if "Turno" not in df.columns:
    st.error("Coluna 'Turno' não encontrada.")
    st.stop()

if "Defeito" not in df.columns:
    st.error("Coluna 'Defeito' não encontrada.")
    st.stop()

# Data
df["Data"] = pd.to_datetime(
    df["Data"],
    dayfirst=True,
    errors="coerce"
)

# Numéricos
df["Qtd_Inspecionada"] = pd.to_numeric(
    df["Qtd_Inspecionada"],
    errors="coerce"
).fillna(0)

df["Qtd_Defeitos"] = pd.to_numeric(
    df["Qtd_Defeitos"],
    errors="coerce"
).fillna(0)

# Strings
for col in [
    "Modelo",
    "Turno",
    "Defeito",
    "Categoria",
    "Severidade",
    "Status",
    "Linha"
]:
    df[col] = df[col].astype(str)

# =====================================================
# FILTROS
# =====================================================

st.sidebar.header("Filtros")

modelos = sorted(df["Modelo"].dropna().unique())
turnos = sorted(df["Turno"].dropna().unique())
categorias = sorted(df["Categoria"].dropna().unique())

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

categoria = st.sidebar.multiselect(
    "Categoria",
    categorias,
    default=categorias
)

df = df[
    (df["Modelo"].isin(modelo)) &
    (df["Turno"].isin(turno)) &
    (df["Categoria"].isin(categoria))
]

# =====================================================
# KPIs
# =====================================================

total_inspecionado = df["Qtd_Inspecionada"].sum()
total_defeitos = df["Qtd_Defeitos"].sum()

if total_inspecionado > 0:

    fpy = (
        (total_inspecionado - total_defeitos)
        / total_inspecionado
    ) * 100

    ppm = (
        total_defeitos
        / total_inspecionado
    ) * 1000000

    taxa_defeito = (
        total_defeitos
        / total_inspecionado
    ) * 100

    dpu = (
        total_defeitos
        / total_inspecionado
    )

else:
    fpy = 0
    ppm = 0
    taxa_defeito = 0
    dpu = 0

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("🛡 FPY", f"{fpy:.2f}%")
col2.metric("📦 INSPECIONADO", f"{total_inspecionado:,.0f}")
col3.metric("⚠ DEFEITOS", f"{total_defeitos:,.0f}")
col4.metric("📈 PPM", f"{ppm:,.0f}")
col5.metric("📉 TAXA DEF.", f"{taxa_defeito:.2f}%")
col6.metric("🔧 DPU", f"{dpu:.4f}")

# =====================================================
# SEMÁFORO FPY
# =====================================================

if fpy >= 98:
    st.success(f"🟢 FPY Excelente: {fpy:.2f}%")
elif fpy >= 95:
    st.warning(f"🟡 FPY Atenção: {fpy:.2f}%")
else:
    st.error(f"🔴 FPY Crítico: {fpy:.2f}%")

st.divider()

# =====================================================
# TOP DEFEITOS E MODELO
# =====================================================

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

    st.plotly_chart(
    fig,
    use_container_width=True,
    config={
        "toImageButtonOptions": {
            "format": "png",
            "scale": 4
        }
    }
)

with c2:

    modelo_df = (
        df.groupby("Modelo")["Qtd_Defeitos"]
        .sum()
        .reset_index()
        .sort_values("Qtd_Defeitos", ascending=False)
    )

    fig2 = px.bar(
        modelo_df,
        x="Modelo",
        y="Qtd_Defeitos",
        title="DEFEITOS POR MODELO",
        template="plotly_dark"
    )

    fig2.update_layout(
        paper_bgcolor="black",
        plot_bgcolor="black",
        font_color="white"
    )

    st.plotly_chart(fig2, use_container_width=True)

# =====================================================
# FPY DIÁRIO
# =====================================================

df_dia = (
    df.groupby("Data")
    .agg({
        "Qtd_Inspecionada": "sum",
        "Qtd_Defeitos": "sum"
    })
    .reset_index()
)

df_dia["FPY"] = (
    (df_dia["Qtd_Inspecionada"] - df_dia["Qtd_Defeitos"])
    /
    df_dia["Qtd_Inspecionada"].replace(0, 1)
) * 100

fig3 = go.Figure()

fig3.add_trace(
    go.Scatter(
    x=df_dia["Data"],
    y=df_dia["FPY"],
    mode="lines+markers+text",
    name="FPY",
    text=[f"{x:.1f}%" for x in df_dia["FPY"]],
    textposition="top center",
    textfont=dict(
        size=14,
        color="white"
    )
))

fig3.update_layout(
    title="FPY POR DATA",
    template="plotly_dark",
    paper_bgcolor="black",
    plot_bgcolor="black",
    font_color="white",
    yaxis_title="FPY (%)"
)

st.plotly_chart(fig3, use_container_width=True)

# =====================================================
# TENDÊNCIA DE DEFEITOS
# =====================================================

def_dia = (
    df.groupby("Data")["Qtd_Defeitos"]
    .sum()
    .reset_index()
)

fig6 = px.line(
    def_dia,
    x="Data",
    y="Qtd_Defeitos",
    markers=True,
    text="Qtd_Defeitos",
    template="plotly_dark"
)

fig6.update_traces(
    textposition="top center",
    textfont_size=14
)

fig6.update_layout(
    paper_bgcolor="black",
    plot_bgcolor="black",
    font_color="white"
)

st.plotly_chart(fig6, use_container_width=True)

# =====================================================
# TURNO E PARETO
# =====================================================

c3, c4 = st.columns(2)

with c3:

    turno_df = (
        df.groupby("Turno")["Qtd_Defeitos"]
        .sum()
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
        paper_bgcolor="black",
        plot_bgcolor="black",
        font_color="white"
    )

    st.plotly_chart(fig4, use_container_width=True)

with c4:

    pareto = (
        df.groupby("Defeito")["Qtd_Defeitos"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    pareto["Acumulado"] = (
        pareto["Qtd_Defeitos"].cumsum()
        / pareto["Qtd_Defeitos"].sum()
        * 100
    )

    fig5 = go.Figure()

    fig5.add_bar(
        x=pareto["Defeito"],
        y=pareto["Qtd_Defeitos"],
        name="Defeitos"
    )

    fig5.add_trace(
        go.Scatter(
            x=pareto["Defeito"],
            y=pareto["Acumulado"],
            mode="lines+markers+text",
            text=[f"{x:.0f}%" for x in pareto["Acumulado"]],
            textposition="top center",
            yaxis="y2",
            name="% Acumulado"
        )
    )

    fig5.update_layout(
        title="PARETO 80/20 DOS DEFEITOS",
        template="plotly_dark",
        paper_bgcolor="black",
        plot_bgcolor="black",
        font_color="white",
        yaxis=dict(title="Qtd Defeitos"),
        yaxis2=dict(
            title="% Acumulado",
            overlaying="y",
            side="right",
            range=[0, 100]
        )
    )

    st.plotly_chart(fig5, use_container_width=True)

# =====================================================
# HEATMAP DEFEITO X TURNO
# =====================================================

try:

    heatmap = pd.pivot_table(
        df,
        values="Qtd_Defeitos",
        index="Defeito",
        columns="Turno",
        aggfunc="sum",
        fill_value=0
    )

    fig7 = px.imshow(
        heatmap,
        text_auto=True,
        title="HEATMAP DEFEITO × TURNO",
        template="plotly_dark"
    )

    fig7.update_layout(
        paper_bgcolor="black",
        plot_bgcolor="black",
        font_color="white"
    )

    st.plotly_chart(fig7, use_container_width=True)

except:
    pass

# =====================================================
# SEVERIDADE
# =====================================================

sev = (
    df.groupby("Severidade")["Qtd_Defeitos"]
    .sum()
    .reset_index()
)

fig8 = px.pie(
    sev,
    names="Severidade",
    values="Qtd_Defeitos",
    title="SEVERIDADE DOS DEFEITOS",
    template="plotly_dark"
)

fig8.update_layout(
    paper_bgcolor="black",
    plot_bgcolor="black",
    font_color="white"
)

st.plotly_chart(fig8, use_container_width=True)

# =====================================================
# STATUS
# =====================================================

status_df = (
    df.groupby("Status")["Qtd_Defeitos"]
    .sum()
    .reset_index()
)

fig9 = px.bar(
    status_df,
    x="Status",
    y="Qtd_Defeitos",
    title="STATUS DOS PRODUTOS",
    template="plotly_dark"
)

fig9.update_layout(
    paper_bgcolor="black",
    plot_bgcolor="black",
    font_color="white"
)

st.plotly_chart(fig9, use_container_width=True)

st.divider()

# =====================================================
# TABELA FINAL
# =====================================================

st.subheader("📋 Dados Detalhados")

st.dataframe(
    df.sort_values("Data", ascending=False),
    use_container_width=True
)