"""
Página 5: Bases Consolidadas, Ficha Metodológica y Centro de Descargas
Colombia Compra Eficiente – Observatorio de Prestación de Servicios (OPS 2018–2026)
"""

import sys
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Bases y Descargas | OPS CCE", page_icon="📥", layout="wide")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.styles import inject_css
from utils.data_loader import (
    load_entidades_data,
    load_mensual_data,
    load_recurrencia_data,
    load_outliers_data,
    load_meta,
    render_sidebar_filters,
    get_project_file,
    fmt_int_co,
    fmt_dec_co,
    fmt_billones,
    fmt_cop_exacto,
    ORDEN_LABELS,
)
from utils.charts import aggregate_departamentos, aggregate_municipios

inject_css()


@st.cache_data(show_spinner="⏳ Preparando archivo CSV...")
def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


df_raw = load_entidades_data()
df_mes_raw = load_mensual_data()
df_rec = load_recurrencia_data()
meta = load_meta()

if df_raw.empty:
    st.error("Ejecute primero `python dashboard_ops/build_dashboard_data.py`.")
    st.stop()

df = render_sidebar_filters(df_raw)

st.markdown("# 📥 Bases Consolidadas, Metodología y Centro de Descargas")
st.markdown(
    f"Consulte la ficha técnica de depuración de los **{fmt_int_co(meta.get('total_contratos', 0))} contratos OPS de Personas Naturales (2018–2026)** "
    "extraídos directamente de **Datos Abiertos (`datos.gov.co`)** y descargue las tablas agregadas oficiales en formato **CSV (UTF-8 con BOM)**."
)

# ── BANNER FICHA METODOLÓGICA ────────────────────────────────────────────────
st.markdown(f"""
<div class="banner-download">
    <h2>📑 Base Oficial Datos Abiertos – Prestación de Servicios Personas Naturales (2018–2026)</h2>
    <p>
        Fuente: <b>datos.gov.co</b> — SECOP I (<code>f789-7hwg</code>) + SECOP II (<code>jbjy-vk9h</code>) • Corte de firma: <b>{meta.get('fecha_firma_min', '2018-01-01')}</b> a <b>{meta.get('fecha_firma_max', '2026-11-26')}</b>.<br>
        Registros brutos descargados: <b>{fmt_int_co(meta.get('total_filas_leidas', 0))}</b> |
        Fuera de rango $1M–$500M: <b>{fmt_int_co(meta.get('total_descartados_valor_cero', 0))}</b> |
        Duplicados eliminados: <b>{fmt_int_co(meta.get('total_duplicados_eliminados', 0))}</b> |
        Universo final depurado: <b>{fmt_int_co(meta.get('total_contratos', 0))}</b> contratos por <b>{fmt_billones(meta.get('valor_total_cop', 0))}</b> (Deflactado PIB 2015: <b>{fmt_billones(meta.get('valor_deflactado_cop', 0))}</b>).
    </p>
</div>
""", unsafe_allow_html=True)

# ── DESCARGA DE PRODUCTOS MAESTROS DEL PROYECTO ─────────────────────────────
st.markdown('<div class="section-header">📦 Productos Maestros Disponibles en la Carpeta del Proyecto</div>', unsafe_allow_html=True)

prod_cols = st.columns(4)
productos = [
    ("CCE-EMAE-FM-04 Ficha Metodologica Prestacion de Servicios 1.docx", "📘 Ficha Metodológica Oficial (CCE-EMAE-FM-04)", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ("Informe_Ejecutivo_Graficas_OPS_2018_2026.docx", "📝 Informe Ejecutivo con 6 Gráficas (Word)", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ("Analisis_OPS_Datos_Abiertos_2018_2026_Nacional_Dptal_Mpal.xlsx", "📊 Análisis Nacional/Deptal/Mpal (Excel)", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("Documento_Modificaciones_y_Mejoras_Producto.docx", "🛠️ Bitácora Técnica de Mejoras (Word)", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
]
for col_ui, (fname, label_p, mime_t) in zip(prod_cols, productos):
    fpath = get_project_file(fname)
    with col_ui:
        if fpath.exists():
            data_b = fpath.read_bytes()
            sz = len(data_b) / 1024
            sz_txt = f"{sz / 1024:.1f} MB" if sz > 1024 else f"{sz:.0f} KB"
            st.download_button(
                label=f"⬇️ {label_p}\n({sz_txt})",
                data=data_b,
                file_name=fname,
                mime=mime_t,
                width="stretch",
            )
        else:
            st.info(f"Archivo `{fname}` no encontrado en la carpeta raíz.")

zip_path = get_project_file("OPS 2018-2026.zip")
if zip_path.exists():
    sz_gb = zip_path.stat().st_size / (1024 ** 3)
    st.info(
        f"📁 **Base transaccional completa por partes (21 archivos Excel):** `{zip_path.name}` ({sz_gb:.2f} GB) "
        f"disponible directamente en la carpeta raíz del proyecto (`{zip_path.parent}`)."
    )

# ── PESTAÑAS DE EXPLORACIÓN Y DESCARGA CSV ──────────────────────────────────
st.markdown('<div class="section-header">📂 Explorador y Descarga de Tablas Consolidadas (Filtros Activos)</div>', unsafe_allow_html=True)

t1, t2, t3, t4, t5, t6 = st.tabs([
    "🏛️ Resumen Territorial y Vigencia",
    "🗺️ Por Departamento",
    "📍 Por Municipio (DIVIPOLA)",
    "🏢 Por Entidad Compradora",
    "📅 Serie Mensual",
    "⚠️ Auditoría Digitación SECOP",
])

with t1:
    res_tv = (
        df.groupby(["ANIO", "ORDEN_CPS", "TIPO_PROVEEDOR_FINAL", "FUENTE"], observed=True)
        .agg(
            Contratos=("N_CONTRATOS", "sum"),
            Valor_COP=("VALOR_TOTAL", "sum"),
            Entidades=("CODIGO_ENTIDAD", "nunique"),
        )
        .reset_index()
        .sort_values(["ANIO", "ORDEN_CPS"])
    )
    st.download_button(
        f"⬇️ Descargar Resumen Vigencia x Territorial x Proveedor (CSV • {len(res_tv):,} filas)",
        to_csv_bytes(res_tv),
        "ops_resumen_vigencia_territorial.csv",
        "text/csv",
    )
    st.dataframe(res_tv, width="stretch", hide_index=True, height=380)

with t2:
    agg_d = aggregate_departamentos(df).sort_values("contratos", ascending=False)
    st.download_button(
        f"⬇️ Descargar Resumen Departamental (CSV • {len(agg_d):,} filas)",
        to_csv_bytes(agg_d),
        "ops_resumen_departamental.csv",
        "text/csv",
    )
    st.dataframe(agg_d, width="stretch", hide_index=True, height=380)

with t3:
    agg_m = aggregate_municipios(df).sort_values("contratos", ascending=False)
    st.download_button(
        f"⬇️ Descargar Resumen Municipal DIVIPOLA (CSV • {len(agg_m):,} filas)",
        to_csv_bytes(agg_m),
        "ops_resumen_municipal_divipola.csv",
        "text/csv",
    )
    st.dataframe(agg_m, width="stretch", hide_index=True, height=380)

with t4:
    agg_e = (
        df.groupby(["CODIGO_ENTIDAD", "NIT_ENTIDAD", "NOMBRE_ENTIDAD", "ORDEN_CPS", "DEPARTAMENTO", "MUNICIPIO", "SECTOR"], observed=True)
        .agg(Contratos=("N_CONTRATOS", "sum"), Valor_COP=("VALOR_TOTAL", "sum"))
        .reset_index()
        .sort_values("Contratos", ascending=False)
    )
    st.download_button(
        f"⬇️ Descargar Directorio Entidades OPS (CSV • {len(agg_e):,} filas)",
        to_csv_bytes(agg_e),
        "ops_directorio_entidades.csv",
        "text/csv",
    )
    st.dataframe(agg_e.head(500), width="stretch", hide_index=True, height=380)
    st.caption("Vista previa limitada a las primeras 500 entidades; la descarga CSV incluye el 100%.")

with t5:
    if not df_mes_raw.empty:
        agg_ms = (
            df_mes_raw.groupby(["ANIO", "MES", "ANIO_MES", "GOBIERNO", "ORDEN_CPS"], observed=True)
            .agg(Contratos=("N_CONTRATOS", "sum"), Valor_COP=("VALOR_TOTAL", "sum"))
            .reset_index()
            .sort_values(["ANIO_MES", "ORDEN_CPS"])
        )
        st.download_button(
            f"⬇️ Descargar Serie Mensual 2018–2026 (CSV • {len(agg_ms):,} filas)",
            to_csv_bytes(agg_ms),
            "ops_serie_mensual_2018_2026.csv",
            "text/csv",
        )
        st.dataframe(agg_ms, width="stretch", hide_index=True, height=380)

with t6:
    df_out = load_outliers_data()
    if not df_out.empty:
        st.markdown("### ⚠️ Auditoría de Contratos con Errores Extremos de Digitación en SECOP")
        st.caption(
            f"Estos registros se mantienen intactos en el conteo oficial ({fmt_int_co(meta.get('total_contratos', 0))}), "
            "pero su cuantía atípica se aísla de la Cuantía Real."
        )
        st.download_button(
            f"⬇️ Descargar Auditoría de Atípicos SECOP (CSV • {len(df_out):,} contratos)",
            to_csv_bytes(df_out),
            "auditoria_errores_digitacion_secop_ops.csv",
            "text/csv",
        )
        df_out_v = df_out.copy()
        df_out_v["VALOR_DIGITADO_COP"] = df_out_v["VALOR_DIGITADO_COP"].apply(fmt_cop_exacto)
        st.dataframe(df_out_v, width="stretch", hide_index=True, height=400)
    else:
        st.success(
            "✅ **0 atípicos extremos de digitación presentes en la base activa:** la regla metodológica de Datos Abiertos CCE "
            "(rango de cuantía `$1.000.000` a `$500.000.000` COP) descarta automáticamente los errores extremos de digitación de ceros."
        )

# ── FICHA TÉCNICA DE CALIDAD DE DATOS ───────────────────────────────────────
with st.expander("📖 Ver Reglas Técnicas de Homologación y Calidad de Datos (Datos Abiertos CCE)", expanded=False):
    st.markdown("""
    1. **Extracción Oficial en Datos Abiertos (`datos.gov.co`):** Consultas directas sobre **SECOP I (`f789-7hwg`)** y **SECOP II (`jbjy-vk9h`)** filtrando `Prestación de Servicios` / `Prestación de servicios` con paginación exacta por clave primaria `:id` (0 pérdidas).
    2. **Filtros de la Ficha Técnica OPS CCE:** Rango de cuantía entre **`$1.000.000` y `$500.000.000` COP**, exclusión de 7 palabras clave no OPS en objeto contractual (`obra`, `convenio`, `suministr`, `consultor`, `transport`, `papel`, `medicamento`), exclusión de 59 términos de personas jurídicas en razón social y deduplicación global por `ID Contrato`.
    3. **Filtro Estricto de Personas Naturales y Estados Ejecutables:** Exclusión de `NIT`, `Nit de Persona Jurídica`, `Nit de Extranjería`, `Otro` y `No Definido`, así como procesos no celebrados en SECOP I (`Convocado`, `Adjudicado`, `Terminado Anormalmente`) y estados no ejecutables en SECOP II (`Cancelado`, `Borrador`, `En aprobación`, `Enviado Proveedor`). Con esto la base concilia al **99,87%** en contratos (`+0,13%`) y **99,99%** en valor (`+0,01%`) frente a la herramienta oficial online de CCE al corte `01/09/2026`.
    4. **Carácter Territorial (`ORDEN_CPS` – 99,87% determinístico/institucional):** Clasificación trazable en **`NACIONAL`**, **`DEPARTAMENTAL`** y **`MUNICIPAL`** integrando el `orden_entidad` oficial de SECOP I, cruce por NIT para SECOP II Territorial, reglas institucionales y catálogo validado de entidades.
    5. **Georreferenciación DANE DIVIPOLA:** Cruce de 100% de entidades con el catálogo oficial **DANE DIVIPOLA** para mapas coropléticos y de densidad departamentales y municipales.
    """)
