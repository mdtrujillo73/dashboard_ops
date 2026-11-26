"""
Página 2: Análisis Territorial, Distribución por Departamento y Mapas de Calor
(33 Departamentos y 1.099+ Municipios DANE DIVIPOLA)
Colombia Compra Eficiente – Observatorio de Prestación de Servicios (OPS 2018–2026)
"""

import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Territorial & Distribución Departamental | OPS CCE", page_icon="🗺️", layout="wide")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.styles import inject_css
from utils.data_loader import (
    load_entidades_data,
    load_geojson_departamentos,
    load_geojson_municipios,
    render_sidebar_filters,
    fmt_int_co,
    fmt_dec_co,
    fmt_billones,
    fmt_cop_exacto,
    ORDEN_ORDER,
    ORDEN_LABELS,
    ORDEN_COLORS,
)
from utils.charts import (
    aggregate_departamentos,
    aggregate_municipios,
    chart_mapa_calor_departamentos,
    chart_mapa_calor_municipios,
    chart_mapa_depto_orden_individual,
    chart_distribucion_departamentos_por_orden,
    chart_matriz_calor_territorial,
    chart_top_departamentos,
    CCE_AZUL,
    CCE_ROJO,
    CCE_MORADO,
    CCE_VERDE,
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

n_deptos = df[df["DEPARTAMENTO"] != "No Determinado"]["DEPARTAMENTO"].nunique()
n_mpios = df[~df["CODIGO_DIVIPOLA"].astype(str).str.endswith("000")]["CODIGO_DIVIPOLA"].nunique()
tot_c = int(df["N_CONTRATOS"].sum())
tot_v = float(df["VALOR_TOTAL"].sum())
tot_e = int(df["CODIGO_ENTIDAD"].nunique())

st.markdown("# 🗺️ Análisis Territorial, Distribución por Departamento y Mapas de Calor")
st.markdown(
    f"**{n_deptos}** departamentos | **{fmt_int_co(n_mpios)}** municipios (DANE DIVIPOLA) | "
    f"**{fmt_int_co(tot_e)}** entidades | **{fmt_int_co(tot_c)}** contratos OPS ({fmt_billones(tot_v)})"
)

tab_mapa, tab_dpto, tab_matriz, tab_rank = st.tabs([
    "🔥 Mapa de Calor Geográfico (Deptos y Municipios)",
    "🏛️ Distribución por Departamento (Ficha y Desglose)",
    "🧩 Matriz de Calor 2D (Cruces)",
    "📊 Rankings Departamentos y Municipios",
])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1: MAPA DE CALOR GEOGRÁFICO + TRÍPTICO POR CARÁCTER TERRITORIAL
# ═══════════════════════════════════════════════════════════════════════════
with tab_mapa:
    st.markdown('<div class="section-header">🔥 Mapa de Calor Interactivo: Departamentos y Municipios</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="info-box">📌 <b>Georreferenciación DANE DIVIPOLA (Datos Abiertos SECOP I y II):</b> Explora la concentración geográfica de contratos OPS con Personas Naturales, cuantías y entidades. Selecciona un departamento para activar el <b>zoom automático</b> sobre todos sus municipios.</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns([1.3, 1.2, 1.2, 1.1])
    with c1:
        vista_mapa = st.selectbox(
            "Disposición de mapas:",
            options=["dual", "depto", "mpio"],
            format_func=lambda x: {
                "dual": "🔀 Vista Dual (Departamentos + Municipios)",
                "depto": "🗺️ Solo Departamental (33 Deptos)",
                "mpio": "📍 Solo Municipal (1.099+ Municipios)",
            }[x],
            key="vista_mapa_ops",
        )
    with c2:
        metrica_calor = st.selectbox(
            "Indicador del Mapa:",
            options=["contratos", "valor", "entidades", "promedio", "pct_mujer"],
            format_func=lambda x: {
                "contratos": "📄 Número de Contratos OPS",
                "valor": "💰 Valor Contratado (COP)",
                "entidades": "🏛️ Entidades Únicas",
                "promedio": "💵 Valor Promedio por Contrato",
                "pct_mujer": "👩 % Mujeres (Género def.)",
            }[x],
            key="met_calor_ops",
        )
    with c3:
        deptos_lista = sorted([d for d in df["DEPARTAMENTO"].dropna().unique().tolist() if d != "No Determinado"])
        depto_zoom = st.selectbox(
            "🔍 Enfocar Departamento (Zoom):",
            options=["🇨🇴 Toda Colombia (Vista Nacional)"] + deptos_lista,
            key="depto_zoom_ops",
        )
    with c4:
        escala_calor = st.selectbox(
            "Paleta de Calor:",
            options=[
                "Institucional CCE (Azul-Naranja-Rojo)",
                "Calor Intenso (Amarillo-Naranja-Rojo)",
                "Azul Institucional",
                "Viridis (Alto Contraste)",
                "Plasma",
            ],
            key="escala_calor_ops",
        )

    modo_mpio = st.radio(
        "Modo de capa para el Mapa Municipal:",
        options=["densidad", "coropletico", "burbujas"],
        format_func=lambda x: {
            "densidad": "🔥 Mapa de Calor de Densidad + Puntos Municipales (Recomendado)",
            "coropletico": "🗺️ Polígonos Municipales Coropléticos (Límites DANE)",
            "burbujas": "🔵 Burbujas Georreferenciadas por Municipio",
        }[x],
        horizontal=True,
        key="modo_mpio_ops",
    )

    df_view = df if depto_zoom == "🇨🇴 Toda Colombia (Vista Nacional)" else df[df["DEPARTAMENTO"] == depto_zoom]
    geo_d = load_geojson_departamentos()
    geo_m = load_geojson_municipios()

    if vista_mapa == "dual":
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown("#### 🗺️ Mapa de Calor por Departamento")
            st.plotly_chart(
                chart_mapa_calor_departamentos(df_view, geo_d, metrica=metrica_calor, escala_nombre=escala_calor),
                width="stretch",
                key="ops_dual_d",
            )
        with col_m2:
            tit_m = "📍 Mapa de Calor por Municipio" if depto_zoom == "🇨🇴 Toda Colombia (Vista Nacional)" else f"📍 Municipios de {depto_zoom}"
            st.markdown(f"#### {tit_m}")
            st.plotly_chart(
                chart_mapa_calor_municipios(df_view, geo_m, metrica=metrica_calor, modo=modo_mpio, escala_nombre=escala_calor),
                width="stretch",
                key="ops_dual_m",
            )
    elif vista_mapa == "depto":
        st.plotly_chart(
            chart_mapa_calor_departamentos(df_view, geo_d, metrica=metrica_calor, escala_nombre=escala_calor),
            width="stretch",
            key="ops_single_d",
        )
    else:
        st.plotly_chart(
            chart_mapa_calor_municipios(df_view, geo_m, metrica=metrica_calor, modo=modo_mpio, escala_nombre=escala_calor),
            width="stretch",
            key="ops_single_m",
        )

    # ── TRÍPTICO COMPARATIVO POR CARÁCTER TERRITORIAL (IGUAL AL REFERENTE EMAE) ──
    st.markdown('<div class="section-header">🔥 Comparativa Departamental en 3 Mapas: Nacional vs. Departamental vs. Municipal</div>', unsafe_allow_html=True)
    met_trip = st.radio(
        "Indicador del tríptico departamental:",
        options=["contratos", "valor", "entidades"],
        format_func=lambda x: {"contratos": "📄 Contratos", "valor": "💰 Valor Real ($ B)", "entidades": "🏛️ Entidades"}[x],
        horizontal=True,
        key="met_trip_ops",
    )
    triptico_cfg = [
        ("NACIONAL", "🔵 Carácter NACIONAL", CCE_AZUL, "#EBF3FA", [[0.0, "#EBF3FA"], [0.4, "#6CA0DC"], [0.8, "#174073"], [1.0, "#0B2240"]]),
        ("DEPARTAMENTAL", "🟣 Carácter DEPARTAMENTAL", CCE_MORADO, "#F4ECF7", [[0.0, "#F4ECF7"], [0.4, "#A569BD"], [0.8, "#533965"], [1.0, "#2E1A3D"]]),
        ("MUNICIPAL", "🟢 Carácter MUNICIPAL", CCE_VERDE, "#EAFAF1", [[0.0, "#EAFAF1"], [0.4, "#52BE80"], [0.8, "#1E8449"], [1.0, "#0B5345"]]),
    ]
    tm1, tm2, tm3 = st.columns(3)
    for col_t, (ord_k, lbl_t, col_hex, bg_hex, cscale) in zip([tm1, tm2, tm3], triptico_cfg):
        sub_ord = df[df["ORDEN_CPS"] == ord_k]
        nc_o = int(sub_ord["N_CONTRATOS"].sum())
        nv_o = float(sub_ord["VALOR_TOTAL"].sum())
        ne_o = int(sub_ord["CODIGO_ENTIDAD"].nunique())
        nd_o = sub_ord[sub_ord["DEPARTAMENTO"] != "No Determinado"]["DEPARTAMENTO"].nunique()
        with col_t:
            st.markdown(
                f"<div style='background:{bg_hex};border-top:4px solid {col_hex};padding:0.65rem 0.9rem;border-radius:10px;margin-bottom:0.4rem;'>"
                f"<b style='color:{col_hex};font-size:0.95rem;'>{lbl_t}</b><br>"
                f"<span style='font-size:0.79rem;color:#34495E;'><b>{fmt_int_co(nc_o)}</b> contratos • <b>{fmt_billones(nv_o, short=True)}</b> • <b>{fmt_int_co(ne_o)}</b> ent. ({nd_o} deptos)</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                chart_mapa_depto_orden_individual(sub_ord, geo_d, metrica=met_trip, colorscale=cscale),
                width="stretch",
                key=f"trip_map_{ord_k}",
            )

    with st.expander(f"📋 Ver detalle municipal georreferenciado ({depto_zoom})", expanded=False):
        agg_m = aggregate_municipios(df_view)
        if not agg_m.empty:
            agg_m = agg_m.sort_values("contratos", ascending=False)
            show_m = agg_m[[
                "CODIGO_DIVIPOLA", "DEPARTAMENTO", "MUNICIPIO", "contratos", "valor_mm", "entidades", "valor_promedio_m", "pct_mujer"
            ]].rename(columns={
                "CODIGO_DIVIPOLA": "DIVIPOLA",
                "DEPARTAMENTO": "Departamento",
                "MUNICIPIO": "Municipio",
                "contratos": "Contratos OPS",
                "valor_mm": "Valor ($ Miles de Millones)",
                "entidades": "Entidades",
                "valor_promedio_m": "Valor Prom. ($ Millones)",
                "pct_mujer": "% Mujeres (gén. def.)",
            })
            show_m["Valor ($ Miles de Millones)"] = show_m["Valor ($ Miles de Millones)"].round(2)
            show_m["Valor Prom. ($ Millones)"] = show_m["Valor Prom. ($ Millones)"].round(2)
            show_m["% Mujeres (gén. def.)"] = show_m["% Mujeres (gén. def.)"].round(1)
            st.dataframe(show_m, width="stretch", hide_index=True, height=380)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2: DISTRIBUCIÓN DEPARTAMENTAL + FICHA EJECUTIVA POR DEPARTAMENTO
# ═══════════════════════════════════════════════════════════════════════════
with tab_dpto:
    st.markdown('<div class="section-header">🏛️ Distribución por Departamento Desglosada por Carácter Territorial</div>', unsafe_allow_html=True)

    dd1, dd2, dd3 = st.columns([1.4, 1.0, 0.9])
    with dd1:
        met_dist = st.radio(
            "Métrica a distribuir:",
            options=["contratos", "valor", "entidades"],
            format_func=lambda x: {"contratos": "📄 Contratos OPS", "valor": "💰 Valor Real ($ Billones)", "entidades": "🏛️ Entidades Únicas"}[x],
            horizontal=True,
            key="met_dist_t2",
        )
    with dd2:
        top_dist = st.slider("Número de departamentos:", 10, 33, 33, key="top_dist_t2")
    with dd3:
        st.write("")
        modo_pct = st.checkbox("Mostrar en 100% proporcional", value=False, key="pct_dist_t2")

    st.plotly_chart(
        chart_distribucion_departamentos_por_orden(df, metrica=met_dist, top_n=top_dist, porcentaje=modo_pct),
        width="stretch",
        key="bar_dist_dpto_t2",
    )

    # ── FICHA EJECUTIVA INDIVIDUAL POR DEPARTAMENTO (MISMO BOSQUEJO POR DPTO) ──
    st.markdown('<div class="section-header">🔍 Ficha Ejecutiva por Departamento (Estilo Bosquejo Principal)</div>', unsafe_allow_html=True)

    deptos_ficha = sorted([d for d in df["DEPARTAMENTO"].dropna().unique().tolist() if d != "No Determinado"])
    if deptos_ficha:
        dpto_sel = st.selectbox(
            "Seleccione un departamento para ver su radiografía completa:",
            options=deptos_ficha,
            index=deptos_ficha.index("Antioquia") if "Antioquia" in deptos_ficha else 0,
            key="ficha_dpto_sel",
        )
        sub_d = df[df["DEPARTAMENTO"] == dpto_sel]
        dc = int(sub_d["N_CONTRATOS"].sum())
        dv = float(sub_d["VALOR_TOTAL"].sum())
        de = int(sub_d["CODIGO_ENTIDAD"].nunique())
        dm = int(sub_d[~sub_d["CODIGO_DIVIPOLA"].astype(str).str.endswith("000")]["CODIGO_DIVIPOLA"].nunique())

        ord_d = sub_d.groupby("ORDEN_CPS", observed=True).agg(
            c=("N_CONTRATOS", "sum"), v=("VALOR_TOTAL", "sum"), e=("CODIGO_ENTIDAD", "nunique")
        )
        def _gs(k):
            if k in ord_d.index:
                r = ord_d.loc[k]
                return int(r["c"]), float(r["v"]), int(r["e"])
            return 0, 0.0, 0

        dn_c, dn_v, dn_e = _gs("NACIONAL")
        dd_c, dd_v, dd_e = _gs("DEPARTAMENTAL")
        dm_c, dm_v, dm_e = _gs("MUNICIPAL")

        fk1, fk2, fk3, fk4 = st.columns(4)
        with fk1:
            st.markdown(f"""<div class="kpi-card"><div class="kpi-label">Contratos en {dpto_sel}</div><div class="kpi-value">{fmt_int_co(dc)}</div><div class="kpi-sub">{fmt_dec_co(dc/max(tot_c,1)*100, 1)}% del total seleccionado</div></div>""", unsafe_allow_html=True)
        with fk2:
            st.markdown(f"""<div class="kpi-card verde"><div class="kpi-label">Valor Real Contratado</div><div class="kpi-value">{fmt_billones(dv, short=True)}</div><div class="kpi-sub">{fmt_cop_exacto(dv / max(dc, 1))} promedio</div></div>""", unsafe_allow_html=True)
        with fk3:
            st.markdown(f"""<div class="kpi-card morado"><div class="kpi-label">Entidades Activas</div><div class="kpi-value">{fmt_int_co(de)}</div><div class="kpi-sub">Nac: {fmt_int_co(dn_e)} • Dep: {fmt_int_co(dd_e)} • Mun: {fmt_int_co(dm_e)}</div></div>""", unsafe_allow_html=True)
        with fk4:
            st.markdown(f"""<div class="kpi-card naranja"><div class="kpi-label">Municipios con OPS</div><div class="kpi-value">{fmt_int_co(dm)}</div><div class="kpi-sub">Nac: {fmt_int_co(dn_c)} • Dep: {fmt_int_co(dd_c)} • Mun: {fmt_int_co(dm_c)}</div></div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        fc1, fc2 = st.columns(2)
        with fc1:
            st.markdown(f"**Top 10 Municipios de {dpto_sel} por Contratos**")
            m_d = aggregate_municipios(sub_d)
            if not m_d.empty:
                m_top = m_d.nlargest(10, "contratos").sort_values("contratos", ascending=True)
                fig_md = go.Figure(go.Bar(
                    x=m_top["contratos"], y=m_top["MUNICIPIO"], orientation="h",
                    marker_color=CCE_AZUL,
                    text=m_top["contratos"].apply(fmt_int_co), textposition="outside",
                ))
                fig_md.update_layout(**LAYOUT_DEFAULTS, xaxis_title="Contratos OPS", height=360)
                st.plotly_chart(fig_md, width="stretch", key="ficha_dpto_mpios")
        with fc2:
            st.markdown(f"**Top 10 Entidades de {dpto_sel} por Contratos**")
            e_d = (
                sub_d.groupby(["NOMBRE_ENTIDAD", "ORDEN_CPS"], observed=True)["N_CONTRATOS"]
                .sum()
                .reset_index(name="Contratos")
                .nlargest(10, "Contratos")
                .sort_values("Contratos", ascending=True)
            )
            e_d["corta"] = e_d["NOMBRE_ENTIDAD"].astype(str).str[:46]
            fig_ed = go.Figure(go.Bar(
                x=e_d["Contratos"], y=e_d["corta"], orientation="h",
                marker_color=e_d["ORDEN_CPS"].map(ORDEN_COLORS).fillna(CCE_AZUL).tolist(),
                text=e_d["Contratos"].apply(fmt_int_co), textposition="outside",
            ))
            fig_ed.update_layout(**LAYOUT_DEFAULTS, xaxis_title="Contratos OPS", height=360)
            st.plotly_chart(fig_ed, width="stretch", key="ficha_dpto_ents")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3: MATRIZ DE CALOR 2D
# ═══════════════════════════════════════════════════════════════════════════
with tab_matriz:
    st.markdown('<div class="section-header">🧩 Matriz de Calor 2D: Departamentos vs. Dimensión Analítica</div>', unsafe_allow_html=True)
    hm1, hm2, hm3 = st.columns(3)
    with hm1:
        dim_mat = st.selectbox(
            "Cruzar Departamentos contra:",
            options=["ANIO", "ORDEN_CPS", "GOBIERNO", "FUENTE"],
            format_func=lambda x: {
                "ANIO": "📅 Vigencia (2018–2026)",
                "ORDEN_CPS": "🏛️ Carácter Territorial",
                "GOBIERNO": "⚖️ Periodo Presidencial",
                "FUENTE": "💻 Plataforma SECOP I / II",
            }[x],
            key="dim_mat_ops",
        )
    with hm2:
        met_mat = st.radio(
            "Métrica en celdas:",
            options=["contratos", "valor", "entidades"],
            format_func=lambda x: {"contratos": "Contratos", "valor": "Valor ($ Miles MM)", "entidades": "Entidades"}[x],
            horizontal=True,
            key="met_mat_ops",
        )
    with hm3:
        top_n_mat = st.slider("Top N Departamentos:", 10, 33, 20, key="top_mat_ops")

    st.plotly_chart(
        chart_matriz_calor_territorial(df, dim_col=dim_mat, metrica=met_mat, top_n=top_n_mat),
        width="stretch",
        key="heatmap_2d_ops",
    )

# ═══════════════════════════════════════════════════════════════════════════
# TAB 4: RANKINGS DEPARTAMENTALES Y MUNICIPALES
# ═══════════════════════════════════════════════════════════════════════════
with tab_rank:
    st.markdown('<div class="section-header">🏘️ Ranking por Departamento</div>', unsafe_allow_html=True)
    met_d = st.radio(
        "Ordenar departamentos por:",
        ["contratos", "valor", "entidades"],
        format_func=lambda x: {"contratos": "📄 Contratos", "valor": "💰 Valor Real ($ Billones)", "entidades": "🏛️ Entidades"}[x],
        horizontal=True,
        key="met_d_ops",
    )
    n_d = st.slider("Top N departamentos:", 5, 33, 18, key="n_d_ops")

    d1, d2 = st.columns([1.35, 1.15])
    with d1:
        st.plotly_chart(chart_top_departamentos(df, n_d, met_d), width="stretch", key="top_d_ops")
    with d2:
        depto_agg = aggregate_departamentos(df)
        if not depto_agg.empty:
            sort_c = {"contratos": "contratos", "valor": "valor_billones", "entidades": "entidades"}[met_d]
            depto_agg = depto_agg.sort_values(sort_c, ascending=False)
            depto_show = depto_agg[[
                "DEPARTAMENTO", "contratos", "valor_billones", "entidades", "municipios", "pct_mujer"
            ]].rename(columns={
                "DEPARTAMENTO": "Departamento",
                "contratos": "Contratos",
                "valor_billones": "Valor ($ B)",
                "entidades": "Entidades",
                "municipios": "Municipios",
                "pct_mujer": "% Mujeres",
            })
            depto_show["Valor ($ B)"] = depto_show["Valor ($ B)"].apply(lambda v: f"$ {fmt_dec_co(v, 2)} B")
            depto_show["% Mujeres"] = depto_show["% Mujeres"].apply(lambda v: f"{fmt_dec_co(v, 1)}%")
            st.dataframe(depto_show, width="stretch", hide_index=True, height=460)

    st.markdown('<div class="section-header">📍 Top Municipios con Mayor Contratación OPS</div>', unsafe_allow_html=True)
    met_m = st.radio(
        "Ordenar municipios por:",
        ["contratos", "valor", "entidades"],
        format_func=lambda x: {"contratos": "📄 Contratos", "valor": "💰 Valor Real ($ Miles MM)", "entidades": "🏛️ Entidades"}[x],
        horizontal=True,
        key="met_m_ops",
    )
    n_m = st.slider("Top N municipios:", 10, 50, 20, key="n_m_ops")

    mpio_agg = aggregate_municipios(df)
    if not mpio_agg.empty:
        col_s = {"contratos": "contratos", "valor": "valor_mm", "entidades": "entidades"}[met_m]
        tit_x = {"contratos": "Contratos OPS", "valor": "Valor Real ($ Miles de Millones COP)", "entidades": "Entidades Únicas"}[met_m]
        top_m = mpio_agg.nlargest(n_m, col_s).sort_values(col_s, ascending=True)
        top_m["label"] = top_m["MUNICIPIO"].astype(str) + " – " + top_m["DEPARTAMENTO"].astype(str) + " (" + top_m["CODIGO_DIVIPOLA"] + ")"

        fig_m = go.Figure(go.Bar(
            x=top_m[col_s],
            y=top_m["label"],
            orientation="h",
            marker=dict(color=top_m[col_s], colorscale=[[0, "#DCE7F3"], [0.6, CCE_AZUL], [1, CCE_ROJO]], showscale=False),
            text=top_m[col_s].apply(lambda v: f"${v:,.1f} MM" if met_m == "valor" else f"{int(v):,}"),
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>" + tit_x + ": %{x:,}<extra></extra>",
        ))
        fig_m.update_layout(**LAYOUT_DEFAULTS, xaxis_title=tit_x, yaxis_title="", height=max(430, n_m * 26))
        st.plotly_chart(fig_m, width="stretch", key="top_mpio_ops")
