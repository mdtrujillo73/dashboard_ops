"""
Página 1: Análisis por Entidades Compradoras, Sectores y Tipologías de Objeto
Colombia Compra Eficiente – Observatorio de Prestación de Servicios (OPS 2018–2026)
"""

import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Entidades y Sectores | OPS CCE", page_icon="🏢", layout="wide")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.styles import inject_css
from utils.data_loader import (
    load_entidades_data,
    render_sidebar_filters,
    fmt_int_co,
    fmt_dec_co,
    fmt_billones,
    fmt_cop_exacto,
    ORDEN_LABELS,
    ORDEN_COLORS,
)
from utils.charts import (
    chart_top_entidades,
    chart_top_sectores,
    chart_tipologias_objeto,
    CCE_AZUL,
    CCE_NARANJA,
    LAYOUT_DEFAULTS,
)

inject_css()

df_raw = load_entidades_data()
if df_raw.empty:
    st.error("Ejecute primero `python dashboard_ops/build_dashboard_data_datos_abiertos.py`.")
    st.stop()

df = render_sidebar_filters(df_raw)
if df.empty:
    st.warning("No hay registros para los filtros seleccionados.")
    st.stop()

total_c = int(df["N_CONTRATOS"].sum())
total_v = float(df["VALOR_TOTAL"].sum())
total_e = int(df["CODIGO_ENTIDAD"].nunique())
total_nits = int(df.loc[df["NIT_ENTIDAD"] != "Sin NIT", "NIT_ENTIDAD"].nunique())

st.markdown("# 🏢 Análisis por Entidades Compradoras y Sectores")
st.markdown(
    f"Mostrando **{fmt_int_co(total_c)}** contratos por **{fmt_billones(total_v)}** "
    f"correspondientes a **{fmt_int_co(total_e)}** cuentas de entidades (**{fmt_int_co(total_nits)}** NITs únicos)."
)

# ── BUSCADOR Y FICHA TÉCNICA DE ENTIDAD ─────────────────────────────────────
st.markdown('<div class="section-header">🔍 Ficha Técnica de Entidad Compradora</div>', unsafe_allow_html=True)

col_b1, col_b2 = st.columns([1.1, 1.9])
with col_b1:
    filtro_input = st.text_input(
        "✍️ Digite nombre de entidad, NIT, código o municipio:",
        value="",
        placeholder="Ej: SENA, Alcaldía de Medellín, 899999, Ministerio de Salud...",
        key="busq_ent_ops",
    )

entidades_todas = sorted(df["NOMBRE_ENTIDAD"].dropna().unique().tolist())
if filtro_input.strip():
    txt = filtro_input.strip().lower()
    mask_b = pd.Series(False, index=df.index)
    for col_s in ["NOMBRE_ENTIDAD", "NIT_ENTIDAD", "CODIGO_ENTIDAD", "MUNICIPIO", "DEPARTAMENTO", "SECTOR"]:
        if col_s in df.columns:
            mask_b |= df[col_s].astype(str).str.lower().str.contains(txt, na=False)
    entidades_filtradas = sorted(df.loc[mask_b, "NOMBRE_ENTIDAD"].dropna().unique().tolist())
else:
    entidades_filtradas = entidades_todas

with col_b2:
    if entidades_filtradas:
        opciones_ent = ["— Seleccione una entidad —"] + entidades_filtradas
        idx_def = 1 if (filtro_input.strip() and len(entidades_filtradas) == 1) else 0
        entidad_sel = st.selectbox(
            "🏛️ Seleccionar entidad compradora:",
            options=opciones_ent,
            index=idx_def,
            key="sel_ent_ops",
        )
        st.caption(f"ℹ️ {fmt_int_co(len(entidades_filtradas))} entidades disponibles (de {fmt_int_co(len(entidades_todas))} en la selección activa).")
    else:
        st.selectbox("🏛️ Seleccionar entidad compradora:", ["— Sin coincidencias —"], disabled=True)
        entidad_sel = "— Sin coincidencias —"

if entidad_sel not in ("— Seleccione una entidad —", "— Sin coincidencias —"):
    ent_df = df[df["NOMBRE_ENTIDAD"] == entidad_sel]
    row0 = ent_df.iloc[0]

    ord_k = row0["ORDEN_CPS"]
    ord_lbl = ORDEN_LABELS.get(ord_k, ord_k)
    ord_col = ORDEN_COLORS.get(ord_k, CCE_AZUL)
    depto = row0["DEPARTAMENTO"]
    mpio = row0["MUNICIPIO"]
    sector = row0["SECTOR"]
    nit = row0["NIT_ENTIDAD"]
    n_cods = int(ent_df["CODIGO_ENTIDAD"].nunique())
    fuentes_str = ", ".join(sorted(ent_df["FUENTE"].unique().tolist()))

    ec = int(ent_df["N_CONTRATOS"].sum())
    ev = float(ent_df["VALOR_TOTAL"].sum())
    ec_m = int(ent_df["CONTRATOS_MUJER"].sum())
    ec_h = int(ent_df["CONTRATOS_HOMBRE"].sum())
    pct_muj = ec_m / max(ec_m + ec_h, 1) * 100.0
    dur_prom = float(ent_df["DURACION_SUMA"].sum()) / max(int(ent_df["DURACION_CONTEO"].sum()), 1)

    f1, f2 = st.columns([1.65, 1.35])
    with f1:
        st.markdown(f"""
        <div class="entity-card" style="border-top-color:{ord_col};">
            <h3>🏛️ {entidad_sel}</h3>
            <span class="badge" style="background:{ord_col};">Carácter {ord_lbl}</span>
            <span class="badge" style="background:#533965;">Sector: {sector}</span>
            <span class="badge" style="background:#3E546C;">Plataforma: {fuentes_str}</span>
            <div class="entity-row">
                <div class="entity-stat">📋 NIT: {nit} ({n_cods} cuenta(s) SECOP)</div>
                <div class="entity-stat">🗺️ {depto} / {mpio}</div>
                <div class="entity-stat">📄 {fmt_int_co(ec)} contratos OPS (Personas Naturales)</div>
                <div class="entity-stat">💰 {fmt_billones(ev)} ({fmt_cop_exacto(ev)})</div>
                <div class="entity-stat">💵 Promedio: {fmt_cop_exacto(ev / max(ec, 1))}</div>
                <div class="entity-stat">👩 {fmt_dec_co(pct_muj, 1)}% Mujeres (género def.)</div>
                <div class="entity-stat">⏱️ Duración prom.: {fmt_dec_co(dur_prom, 0)} días</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with f2:
        vig_ent = (
            ent_df.groupby("ANIO", observed=True)
            .agg(Contratos=("N_CONTRATOS", "sum"), Valor_MM=("VALOR_TOTAL", lambda s: s.sum() / 1e9))
            .reset_index()
            .sort_values("ANIO")
        )
        vig_ent["ANIO_STR"] = vig_ent["ANIO"].astype(str)
        fig_ve = px.bar(
            vig_ent,
            x="ANIO_STR",
            y="Contratos",
            text="Contratos",
            color_discrete_sequence=[ord_col],
            labels={"Contratos": "Contratos OPS", "ANIO_STR": "Vigencia"},
            title="Evolución Anual de Contratos OPS de la Entidad",
        )
        fig_ve.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig_ve.update_layout(**LAYOUT_DEFAULTS, height=265)
        st.plotly_chart(fig_ve, width="stretch", key="vig_ent_ops")

# ── TOP N ENTIDADES ─────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🏆 Rankings de Entidades Compradoras</div>', unsafe_allow_html=True)

n_top = st.slider("Número de entidades a mostrar en el ranking:", 5, 30, 15, key="n_top_ent_ops")
t1, t2 = st.columns(2)
with t1:
    st.markdown("**Por número de contratos OPS**")
    st.plotly_chart(chart_top_entidades(df, n_top, "contratos"), width="stretch", key="top_ent_c")
with t2:
    st.markdown("**Por valor contratado ($ Billones COP)**")
    st.plotly_chart(chart_top_entidades(df, n_top, "valor"), width="stretch", key="top_ent_v")

# ── SECTORES Y TIPOLOGÍA DE OBJETO ──────────────────────────────────────────
st.markdown('<div class="section-header">📑 Distribución por Sector Institucional y Tipología del Objeto Contractual</div>', unsafe_allow_html=True)

s1, s2 = st.columns([1.3, 1.0])
with s1:
    met_sec = st.radio(
        "Ordenar sectores por:",
        ["contratos", "valor", "entidades"],
        format_func=lambda x: {"contratos": "Contratos", "valor": "Valor ($ B)", "entidades": "Entidades"}[x],
        horizontal=True,
        key="met_sec_ops",
    )
    st.plotly_chart(chart_top_sectores(df, n=12, por=met_sec), width="stretch", key="chart_sec_ops")
with s2:
    st.markdown("**Clasificación por tipología del objeto contractual**")
    st.caption("Clasificación automática basada en el campo `objeto_limpio` de SECOP.")
    st.plotly_chart(chart_tipologias_objeto(df), width="stretch", key="chart_tip_ops")

# ── DIRECTORIO CONSOLIDADO DESCARGABLE ──────────────────────────────────────
st.markdown('<div class="section-header">📋 Directorio Consolidado de Entidades Compradoras</div>', unsafe_allow_html=True)

directorio = (
    df.groupby(["CODIGO_ENTIDAD", "NIT_ENTIDAD", "NOMBRE_ENTIDAD", "ORDEN_CPS", "DEPARTAMENTO", "MUNICIPIO", "SECTOR"], observed=True)
    .agg(
        Contratos=("N_CONTRATOS", "sum"),
        Valor_COP=("VALOR_TOTAL", "sum"),
        Contratos_Mujer=("CONTRATOS_MUJER", "sum"),
        Contratos_Hombre=("CONTRATOS_HOMBRE", "sum"),
        Dur_Sum=("DURACION_SUMA", "sum"),
        Dur_Cnt=("DURACION_CONTEO", "sum"),
    )
    .reset_index()
    .sort_values("Contratos", ascending=False)
)
directorio["Pct_Mujer"] = (directorio["Contratos_Mujer"] / (directorio["Contratos_Mujer"] + directorio["Contratos_Hombre"]).clip(lower=1) * 100).round(1)
directorio["Duracion_Prom_Dias"] = (directorio["Dur_Sum"] / directorio["Dur_Cnt"].clip(lower=1)).round(0).astype(int)
directorio["Carácter"] = directorio["ORDEN_CPS"].map(ORDEN_LABELS)

c_s, c_dl = st.columns([3, 1])
with c_s:
    filtro_dir = st.text_input("🔎 Filtrar directorio por nombre, NIT, departamento, municipio o sector:", "", key="dir_txt_ops")
with c_dl:
    st.write("")
    csv_bytes = directorio.drop(columns=["Dur_Sum", "Dur_Cnt"]).to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Descargar CSV", csv_bytes, "directorio_entidades_ops_cce.csv", "text/csv", width="stretch")

dir_view = directorio.copy()
if filtro_dir.strip():
    q = filtro_dir.strip().lower()
    mask_d = (
        dir_view["NOMBRE_ENTIDAD"].astype(str).str.lower().str.contains(q, na=False)
        | dir_view["NIT_ENTIDAD"].astype(str).str.lower().str.contains(q, na=False)
        | dir_view["DEPARTAMENTO"].astype(str).str.lower().str.contains(q, na=False)
        | dir_view["MUNICIPIO"].astype(str).str.lower().str.contains(q, na=False)
        | dir_view["SECTOR"].astype(str).str.lower().str.contains(q, na=False)
    )
    dir_view = dir_view[mask_d]

dir_view["Valor_Fmt"] = dir_view["Valor_COP"].apply(fmt_cop_exacto)
st.dataframe(
    dir_view[[
        "NOMBRE_ENTIDAD", "NIT_ENTIDAD", "Carácter", "DEPARTAMENTO", "MUNICIPIO",
        "SECTOR", "Contratos", "Valor_Fmt", "Pct_Mujer", "Duracion_Prom_Dias"
    ]].rename(columns={
        "NOMBRE_ENTIDAD": "Entidad",
        "NIT_ENTIDAD": "NIT",
        "DEPARTAMENTO": "Departamento",
        "MUNICIPIO": "Municipio",
        "SECTOR": "Sector",
        "Valor_Fmt": "Valor Total (COP)",
        "Pct_Mujer": "% Mujeres (gén. def.)",
        "Duracion_Prom_Dias": "Duración Prom. (Días)",
    }),
    width="stretch",
    hide_index=True,
    height=440,
)
