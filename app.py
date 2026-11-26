"""
Dashboard Institucional – Observatorio de Contratación por Prestación de Servicios (OPS 2018–2026)
Agencia Nacional de Contratación Pública – Colombia Compra Eficiente (ANCP - CCE)
Página Principal (Portada Ejecutiva):
  1. Panel Ejecutivo fiel al bosquejo oficial:
     - Número total y Valor total de contratos de prestación de servicios
     - Desglose por carácter territorial: NACIONAL | DEPARTAMENTAL | MUNICIPAL
     - Total Entidades y desglose por Entidades Nacionales, Departamentales y Municipales
  2. Análisis Visual General (Carácter Territorial, Evolución Anual, Proveedor Binario, SECOP I vs II)
  3. Mapa de Calor Geográfico Rápido (Departamentos y Municipios DIVIPOLA)
  4. Tablas Oficiales de Balance por Carácter Territorial y por Vigencia
"""

import sys
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Colombia Compra Eficiente – Prestación de Servicios (OPS 2018–2026)",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Observatorio de Contratación por Prestación de Servicios (OPS 2018–2026) | Colombia Compra Eficiente"
    },
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.styles import inject_css
from utils.data_loader import (
    load_entidades_data,
    load_meta,
    load_geojson_departamentos,
    load_geojson_municipios,
    render_sidebar_filters,
    fmt_int_co,
    fmt_dec_co,
    fmt_billones,
    fmt_cop_exacto,
    ORDEN_ORDER,
    ORDEN_LABELS,
)
from utils.charts import (
    aggregate_departamentos,
    chart_dona_territorial,
    chart_evolucion_anual_orden,
    chart_proveedor_binario,
    chart_genero_donut,
    chart_transicion_secop,
    chart_distribucion_departamentos_por_orden,
    chart_mapa_calor_departamentos,
    chart_mapa_calor_municipios,
)

inject_css()

# ── Carga de datos y Sidebar institucional ──────────────────────────────────
df_raw = load_entidades_data()
if df_raw.empty:
    st.error(
        "No se encontraron los archivos Parquet en `dashboard_ops/data/`. "
        "Ejecute primero `python dashboard_ops/build_dashboard_data.py`."
    )
    st.stop()

df = render_sidebar_filters(df_raw)
meta = load_meta()

if df.empty:
    st.warning("No hay registros que coincidan con la combinación de filtros seleccionada en el panel lateral.")
    st.stop()

# ── Cálculo de KPIs exactos sobre la selección activa ───────────────────────
total_contratos = int(df["N_CONTRATOS"].sum())
valor_total = float(df["VALOR_TOTAL"].sum())
total_entidades = int(df["CODIGO_ENTIDAD"].nunique())
total_entidades_unif = int(df["NOMBRE_ENTIDAD"].nunique())
total_nits = int(df.loc[df["NIT_ENTIDAD"] != "Sin NIT", "NIT_ENTIDAD"].nunique())
valor_promedio = valor_total / max(total_contratos, 1)

contratos_pn = int(df.loc[df["TIPO_PROVEEDOR_FINAL"] == "PERSONA NATURAL", "N_CONTRATOS"].sum())
pct_pn = contratos_pn / max(total_contratos, 1) * 100.0
pct_pj = 100.0 - pct_pn

# Desglose por carácter territorial (NACIONAL / DEPARTAMENTAL / MUNICIPAL)
ord_grp = df.groupby("ORDEN_CPS", observed=True).agg(
    contratos=("N_CONTRATOS", "sum"),
    valor=("VALOR_TOTAL", "sum"),
    entidades=("CODIGO_ENTIDAD", "nunique"),
    nits=("NIT_ENTIDAD", lambda s: s[s != "Sin NIT"].nunique()),
)

def get_ord_stats(orden_key: str):
    if orden_key in ord_grp.index:
        r = ord_grp.loc[orden_key]
        return int(r["contratos"]), float(r["valor"]), int(r["entidades"]), int(r["nits"])
    return 0, 0.0, 0, 0

nac_c, nac_v, nac_e, nac_nit = get_ord_stats("NACIONAL")
dep_c, dep_v, dep_e, dep_nit = get_ord_stats("DEPARTAMENTAL")
mun_c, mun_v, mun_e, mun_nit = get_ord_stats("MUNICIPAL")

anios_sel = sorted(df["ANIO"].unique().tolist())
rango_anios = f"{anios_sel[0]}–{anios_sel[-1]}" if len(anios_sel) > 1 else str(anios_sel[0])

solo_pn = (pct_pj < 0.05)
tot_pn_unicas = int(meta.get("total_personas_naturales_unicas", 0))
val_defl_meta = float(meta.get("valor_deflactado_cop", 0.0))
c_muj_sel = int(df["CONTRATOS_MUJER"].sum())
c_hom_sel = int(df["CONTRATOS_HOMBRE"].sum())
pct_muj_sel = c_muj_sel / max(c_muj_sel + c_hom_sel, 1) * 100.0
pct_hom_sel = 100.0 - pct_muj_sel

tag_prov = (
    f"👤 100% Personas Naturales • {fmt_int_co(tot_pn_unicas)} contratistas únicos"
    if solo_pn
    else f"👤 {fmt_dec_co(pct_pn, 1)}% Persona Natural • {fmt_dec_co(pct_pj, 1)}% Persona Jurídica"
)
sub_hero_l = (
    f"👤 100% Personas Naturales (Datos Abiertos CCE) • ♀️ {fmt_dec_co(pct_muj_sel, 1)}% Mujeres • ♂️ {fmt_dec_co(pct_hom_sel, 1)}% Hombres"
    if solo_pn
    else f"👤 {fmt_int_co(contratos_pn)} Persona Natural ({fmt_dec_co(pct_pn, 1)}%) • 🏢 {fmt_int_co(total_contratos - contratos_pn)} Persona Jurídica ({fmt_dec_co(pct_pj, 1)}%)"
)

# ── ENCABEZADO INSTITUCIONAL CCE ────────────────────────────────────────────
st.markdown(f"""
<div class="main-header">
    <div class="color-strip"></div>
    <h1>🏛️ Observatorio de Contratación – Prestación de Servicios (OPS)</h1>
    <p>Agencia Nacional de Contratación Pública – Colombia Compra Eficiente | Base Oficial de Datos Abiertos (SECOP I y SECOP II — Personas Naturales)</p>
    <span class="tag">📅 Vigencias {rango_anios}</span>
    <span class="tag">🌐 Datos Abiertos (datos.gov.co)</span>
    <span class="tag">📋 {fmt_int_co(total_contratos)} contratos depurados ($1M–$500M)</span>
    <span class="tag">🏛️ {fmt_int_co(total_entidades)} entidades compradoras</span>
    <span class="tag">{tag_prov}</span>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# SECCIÓN 1: BOSQUEJO EJECUTIVO PRINCIPAL (FIEL AL DISEÑO SOLICITADO)
# ═══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">📌 Resumen Ejecutivo Nacional y por Carácter Territorial</div>', unsafe_allow_html=True)

# Fila 1: Número total de contratos | Valor total de contratos
top_l, top_r = st.columns(2, gap="large")
with top_l:
    st.markdown(f"""
    <div class="ops-hero-wrap">
        <div class="ops-pill-header">Número total de los contratos<br>de prestación de servicios</div>
        <div class="ops-value-box">
            <div class="ops-value-main">{fmt_int_co(total_contratos)}</div>
            <div class="ops-value-sub">{sub_hero_l}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with top_r:
    st.markdown(f"""
    <div class="ops-hero-wrap">
        <div class="ops-pill-header">Valor total de los contratos de<br>prestación de servicios</div>
        <div class="ops-value-box">
            <div class="ops-value-main">{fmt_billones(valor_total)}</div>
            <div class="ops-value-sub">{fmt_cop_exacto(valor_total)} COP • Promedio: {fmt_cop_exacto(valor_promedio)} / contrato</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Fila 2: Banner horizontal carácter territorial
st.markdown("""
<div class="ops-territorial-banner">
    Contratación de prestación de servicios por su carácter territorial
</div>
""", unsafe_allow_html=True)

# Fila 3: 3 Columnas (NACIONAL | DEPARTAMENTAL | MUNICIPAL)
c_nac, c_dep, c_mun = st.columns(3, gap="medium")

territorial_blocks = [
    (c_nac, "nacional", "NACIONAL", nac_c, nac_v),
    (c_dep, "departamental", "DEPARTAMENTAL", dep_c, dep_v),
    (c_mun, "municipal", "MUNICIPAL", mun_c, mun_v),
]

for col_ui, css_cls, titulo_ord, n_c, v_c in territorial_blocks:
    pct_c = n_c / max(total_contratos, 1) * 100.0
    pct_v = v_c / max(valor_total, 1.0) * 100.0
    with col_ui:
        st.markdown(f"""
        <div class="ops-col-panel {css_cls}">
            <div class="ops-level-pill">{titulo_ord}</div>
            <div class="ops-sub-pill">NÚMERO DE CONTRATOS</div>
            <div class="ops-sub-val">
                <div class="num">{fmt_int_co(n_c)}</div>
                <div class="sub">{fmt_dec_co(pct_c, 1)}% del total de contratos</div>
            </div>
            <div class="ops-sub-pill">VALOR DE LOS CONTRATOS</div>
            <div class="ops-sub-val">
                <div class="num">{fmt_billones(v_c)}</div>
                <div class="sub">{fmt_cop_exacto(v_c)} COP ({fmt_dec_co(pct_v, 1)}%)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Fila 4: TOTAL ENTIDADES (Etiqueta azul izquierda + caja ancha blanca borde verde derecha, alineadas al píxel)
st.markdown(f"""
<div class="ops-ent-total-row">
    <div class="ops-ent-total-label">TOTAL ENTIDADES</div>
    <div class="ops-ent-total-box">
        <div class="num">{fmt_int_co(total_entidades)}</div>
        <div class="sub">Cuentas oficiales SECOP activas • {fmt_int_co(total_entidades_unif)} nombres unificados • {fmt_int_co(total_nits)} NITs únicos</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Fila 5: ENTIDADES NACIONALES | ENTIDADES DEPARTAMENTALES | ENTIDADES MUNICIPALES
e_nac, e_dep, e_mun = st.columns(3, gap="medium")
ent_blocks = [
    (e_nac, "ENTIDADES NACIONALES", nac_e, nac_nit),
    (e_dep, "ENTIDADES DEPARTAMENTALES", dep_e, dep_nit),
    (e_mun, "ENTIDADES MUNICIPALES", mun_e, mun_nit),
]

for col_ui, titulo_e, cnt_e, cnt_nit in ent_blocks:
    pct_e = cnt_e / max(total_entidades, 1) * 100.0
    with col_ui:
        st.markdown(f"""
        <div class="ops-ent-card-wrap">
            <div class="ops-ent-pill">{titulo_e}</div>
            <div class="ops-sub-val" style="width: 92%;">
                <div class="num">{fmt_int_co(cnt_e)}</div>
                <div class="sub">{fmt_dec_co(pct_e, 1)}% del total • {fmt_int_co(cnt_nit)} NITs</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

conc = meta.get("conciliacion_online_sep01", {})
conc_txt = (
    f" Validación contra herramienta online CCE al <code>01/09/2026</code>: "
    f"<strong>{fmt_int_co(conc.get('replicado_contratos', 7360772))}</strong> vs. {fmt_int_co(conc.get('online_contratos', 7351486))} contratos "
    f"(<strong>+{fmt_dec_co(conc.get('error_pct_contratos', 0.13), 2)}%</strong>) y <strong>${fmt_dec_co(conc.get('replicado_valor_b', 150.01), 2)} B</strong> vs. $150 B (<strong>+{fmt_dec_co(conc.get('error_pct_valor', 0.01), 2)}%</strong>)."
    if conc else ""
)
st.markdown(f"""
<div class="note-box">
    <strong>📌 Nota Técnica – Base Oficial de Datos Abiertos (Personas Naturales):</strong> Extraída directamente desde <code>datos.gov.co</code> — <strong>SECOP I (f789-7hwg)</strong> y <strong>SECOP II (jbjy-vk9h)</strong> (vigencias 2018–2026, corte de firmas al <strong>{meta.get('fecha_firma_max', '2026-11-26')}</strong>).
    Aplica la Ficha Técnica oficial de OPS (rango de cuantía <strong>$1M–$500M COP</strong>, exclusiones de objeto no OPS, exclusión de personas jurídicas por razón social y tipo de identificación, estados ejecutables y deduplicación global por <code>ID Contrato</code> — eliminando 100% de atípicos extremos de digitación).
    Valor deflactado global (PIB base 2015): <strong>{fmt_billones(val_defl_meta)}</strong>.{conc_txt}
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# SECCIÓN 2: ANÁLISIS VISUAL EJECUTIVO
# ═══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">📊 Análisis Visual: Carácter Territorial, Evolución Anual, Género y SECOP II</div>', unsafe_allow_html=True)

m_col1, m_col2 = st.columns([2.2, 1.0])
with m_col1:
    metrica_home = st.radio(
        "Métrica de análisis visual:",
        options=["contratos", "valor", "entidades"],
        format_func=lambda x: {
            "contratos": "📄 Número de Contratos OPS",
            "valor": "💰 Valor Contratado ($ Billones COP)",
            "entidades": "🏛️ Entidades Únicas Activas",
        }[x],
        horizontal=True,
        key="metrica_home_ops",
    )
with m_col2:
    apilado_home = st.checkbox("Barras apiladas por vigencia", value=True, key="apilado_home_ops")

g1, g2 = st.columns([1.05, 1.75])
with g1:
    st.markdown("**Participación por carácter territorial**")
    st.plotly_chart(chart_dona_territorial(df, metrica_home), width="stretch", key="dona_terr_home")

with g2:
    st.markdown(f"**Evolución anual por carácter territorial ({rango_anios})**")
    st.plotly_chart(chart_evolucion_anual_orden(df, metrica_home, apilado=apilado_home), width="stretch", key="bar_vig_home")

g3, g4 = st.columns([1.05, 1.75])
with g3:
    met_prov = "valor" if metrica_home == "valor" else "contratos"
    if solo_pn:
        st.markdown("**Enfoque de género en Personas Naturales (Mujeres vs. Hombres)**")
        st.plotly_chart(chart_genero_donut(df, met_prov), width="stretch", key="dona_prov_home")
    else:
        st.markdown("**Distribución binaria: Persona Natural vs. Persona Jurídica**")
        st.plotly_chart(chart_proveedor_binario(df, met_prov), width="stretch", key="dona_prov_home")

with g4:
    st.markdown("**Transición digital: SECOP I vs. SECOP II por vigencia**")
    st.plotly_chart(chart_transicion_secop(df, met_prov), width="stretch", key="bar_secop_home")

# ═══════════════════════════════════════════════════════════════════════════
# SECCIÓN 3: DISTRIBUCIÓN POR DEPARTAMENTO (DESGLOSADA POR CARÁCTER TERRITORIAL)
# ═══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">🏛️ Distribución por Departamento (Desglosada por Carácter Territorial)</div>', unsafe_allow_html=True)

dp_c1, dp_c2, dp_c3 = st.columns([1.4, 1.0, 0.9])
with dp_c1:
    met_dpto_home = st.radio(
        "Métrica departamental:",
        options=["contratos", "valor", "entidades"],
        format_func=lambda x: {"contratos": "📄 Contratos", "valor": "💰 Valor Real ($ B)", "entidades": "🏛️ Entidades"}[x],
        horizontal=True,
        key="met_dpto_home_ops",
    )
with dp_c2:
    top_n_dpto_home = st.slider("Departamentos a graficar:", 10, 33, 18, key="top_n_dpto_home_ops")
with dp_c3:
    st.write("")
    pct_mode_home = st.checkbox("Ver composición 100%", value=False, key="pct_dpto_home_ops")

col_dp_g, col_dp_t = st.columns([1.3, 1.15])
with col_dp_g:
    st.markdown(f"**Top {top_n_dpto_home} Departamentos por carácter territorial (Nacional / Departamental / Municipal)**")
    st.plotly_chart(
        chart_distribucion_departamentos_por_orden(
            df, metrica=met_dpto_home, top_n=top_n_dpto_home, porcentaje=pct_mode_home
        ),
        width="stretch",
        key="bar_dpto_ord_home",
    )

with col_dp_t:
    st.markdown("**Resumen completo de los 33 departamentos**")
    dpto_base = aggregate_departamentos(df)
    if not dpto_base.empty:
        piv_ord_d = (
            df[df["DEPARTAMENTO"] != "No Determinado"]
            .groupby(["DEPARTAMENTO", "ORDEN_CPS"], observed=True)["N_CONTRATOS"]
            .sum()
            .unstack(fill_value=0)
            .reset_index()
        )
        for col_o in ORDEN_ORDER:
            if col_o not in piv_ord_d.columns:
                piv_ord_d[col_o] = 0
        dpto_tbl = dpto_base.merge(piv_ord_d[["DEPARTAMENTO", "NACIONAL", "DEPARTAMENTAL", "MUNICIPAL"]], on="DEPARTAMENTO", how="left")
        sort_col = {"contratos": "contratos", "valor": "valor_billones", "entidades": "entidades"}[met_dpto_home]
        dpto_tbl = dpto_tbl.sort_values(sort_col, ascending=False)
        dpto_tbl["% País"] = (dpto_tbl["contratos"] / max(total_contratos, 1) * 100).apply(lambda v: f"{fmt_dec_co(v, 1)}%")
        dpto_tbl["Valor Real"] = dpto_tbl["valor_billones"].apply(lambda v: f"$ {fmt_dec_co(v, 2)} B")
        st.dataframe(
            dpto_tbl[[
                "DEPARTAMENTO", "contratos", "% País", "Valor Real", "entidades", "NACIONAL", "DEPARTAMENTAL", "MUNICIPAL"
            ]].rename(columns={
                "DEPARTAMENTO": "Departamento",
                "contratos": "Contratos",
                "entidades": "Entidades",
                "NACIONAL": "Nac.",
                "DEPARTAMENTAL": "Dep.",
                "MUNICIPAL": "Mun.",
            }),
            width="stretch",
            hide_index=True,
            height=max(460, top_n_dpto_home * 26),
        )

# ═══════════════════════════════════════════════════════════════════════════
# SECCIÓN 4: MAPA DE CALOR TERRITORIAL RÁPIDO EN PORTADA
# ═══════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">🔥 Mapa de Calor Territorial: Departamentos y Municipios de Colombia</div>', unsafe_allow_html=True)

mc1, mc2, mc3 = st.columns([1.2, 1.2, 1.2])
with mc1:
    nivel_mapa_home = st.radio(
        "Nivel geográfico:",
        options=["departamentos", "municipios"],
        format_func=lambda x: "🗺️ Por Departamento (33 Deptos)" if x == "departamentos" else "📍 Por Municipio (1.100+ Municipios DIVIPOLA)",
        horizontal=True,
        key="nivel_mapa_home_ops",
    )
with mc2:
    metrica_mapa_home = st.selectbox(
        "Indicador de calor:",
        options=["contratos", "valor", "entidades", "promedio", "pct_pn"],
        format_func=lambda x: {
            "contratos": "📄 Número de Contratos OPS",
            "valor": "💰 Valor Contratado (COP)",
            "entidades": "🏛️ Entidades Únicas",
            "promedio": "💵 Valor Promedio por Contrato",
            "pct_pn": "👤 % Contratos a Persona Natural",
        }[x],
        key="met_mapa_home_ops",
    )
with mc3:
    escala_home = st.selectbox(
        "Escala de color:",
        options=[
            "Institucional CCE (Azul-Naranja-Rojo)",
            "Calor Intenso (Amarillo-Naranja-Rojo)",
            "Azul Institucional",
            "Viridis (Alto Contraste)",
        ],
        key="esc_mapa_home_ops",
    )

if nivel_mapa_home == "departamentos":
    geojson_depto = load_geojson_departamentos()
    st.plotly_chart(
        chart_mapa_calor_departamentos(df, geojson_depto, metrica=metrica_mapa_home, escala_nombre=escala_home),
        width="stretch",
        key="map_home_depto_ops",
    )
else:
    geojson_mpio = load_geojson_municipios()
    modo_mpio_home = st.radio(
        "Visualización municipal:",
        options=["densidad", "coropletico", "burbujas"],
        format_func=lambda x: {
            "densidad": "🔥 Mapa de Calor Continuo (Densidad) + Puntos Municipales",
            "coropletico": "🗺️ Polígonos Municipales (Coroplético DANE)",
            "burbujas": "🔵 Burbujas Georreferenciadas por Municipio",
        }[x],
        horizontal=True,
        key="modo_mpio_home_ops",
    )
    st.plotly_chart(
        chart_mapa_calor_municipios(
            df,
            geojson_mpio=geojson_mpio,
            metrica=metrica_mapa_home,
            modo=modo_mpio_home,
            escala_nombre=escala_home,
        ),
        width="stretch",
        key="map_home_mpio_ops",
    )

st.caption("💡 **Tip:** Usa el menú lateral izquierdo para navegar a las páginas especializadas: **Entidades y Sectores**, **Territorial**, **Evolución y Gobiernos**, **Proveedores y Recurrencia** y **Bases y Descargas**.")

# ═══════════════════════════════════════════════════════════════════════════
# SECCIÓN 4: TABLAS DE BALANCE OFICIAL
# ═══════════════════════════════════════════════════════════════════════════
with st.expander("📋 Ver tablas de balance oficial por Carácter Territorial y por Vigencia", expanded=True):
    t_ord, t_vig = st.tabs(["🏛️ Balance por Carácter Territorial", "📅 Balance Anual por Vigencia (2018–2026)"])

    with t_ord:
        res_ord = (
            df.groupby("ORDEN_CPS", observed=True)
            .agg(
                Contratos=("N_CONTRATOS", "sum"),
                Valor_COP=("VALOR_TOTAL", "sum"),
                Entidades=("CODIGO_ENTIDAD", "nunique"),
                NITs=("NIT_ENTIDAD", lambda s: s[s != "Sin NIT"].nunique()),
                Dur_Sum=("DURACION_SUMA", "sum"),
                Dur_Cnt=("DURACION_CONTEO", "sum"),
            )
            .reindex([o for o in ORDEN_ORDER if o in df["ORDEN_CPS"].unique()])
            .reset_index()
        )
        res_ord["Carácter Territorial"] = res_ord["ORDEN_CPS"].map(ORDEN_LABELS)
        res_ord["% Contratos"] = (res_ord["Contratos"] / max(total_contratos, 1) * 100).apply(lambda v: f"{fmt_dec_co(v, 1)}%")
        res_ord["Valor ($ Billones)"] = res_ord["Valor_COP"].apply(fmt_billones)
        res_ord["Valor Exacto (COP)"] = res_ord["Valor_COP"].apply(fmt_cop_exacto)
        res_ord["% Valor"] = (res_ord["Valor_COP"] / max(valor_total, 1) * 100).apply(lambda v: f"{fmt_dec_co(v, 1)}%")
        res_ord["Valor Promedio"] = (res_ord["Valor_COP"] / res_ord["Contratos"].clip(lower=1)).apply(fmt_cop_exacto)
        res_ord["Duración Prom. (Días)"] = (res_ord["Dur_Sum"] / res_ord["Dur_Cnt"].clip(lower=1)).round(0).astype(int)
        st.dataframe(
            res_ord[[
                "Carácter Territorial", "Contratos", "% Contratos", "Valor ($ Billones)",
                "Valor Exacto (COP)", "% Valor", "Entidades", "NITs", "Valor Promedio", "Duración Prom. (Días)"
            ]],
            width="stretch",
            hide_index=True,
        )

    with t_vig:
        pn_vig = (
            df[df["TIPO_PROVEEDOR_FINAL"] == "PERSONA NATURAL"]
            .groupby("ANIO", observed=True)["N_CONTRATOS"]
            .sum()
            .reset_index(name="Contratos_PN")
        )
        res_vig = (
            df.groupby("ANIO", observed=True)
            .agg(
                Contratos=("N_CONTRATOS", "sum"),
                Valor_COP=("VALOR_TOTAL", "sum"),
                Entidades=("CODIGO_ENTIDAD", "nunique"),
                Dur_Sum=("DURACION_SUMA", "sum"),
                Dur_Cnt=("DURACION_CONTEO", "sum"),
            )
            .reset_index()
            .merge(pn_vig, on="ANIO", how="left")
            .sort_values("ANIO")
        )
        res_vig["Contratos_PN"] = res_vig["Contratos_PN"].fillna(0).astype(int)
        res_vig["% Persona Natural"] = (res_vig["Contratos_PN"] / res_vig["Contratos"].clip(lower=1) * 100).apply(lambda v: f"{fmt_dec_co(v, 1)}%")
        res_vig["Valor ($ Billones)"] = res_vig["Valor_COP"].apply(fmt_billones)
        res_vig["Valor Promedio"] = (res_vig["Valor_COP"] / res_vig["Contratos"].clip(lower=1)).apply(fmt_cop_exacto)
        res_vig["Duración Prom. (Días)"] = (res_vig["Dur_Sum"] / res_vig["Dur_Cnt"].clip(lower=1)).round(0).astype(int)
        st.dataframe(
            res_vig.rename(columns={"ANIO": "Vigencia"})[[
                "Vigencia", "Contratos", "Valor ($ Billones)", "Entidades",
                "% Persona Natural", "Valor Promedio", "Duración Prom. (Días)"
            ]],
            width="stretch",
            hide_index=True,
        )
