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
    "Consulte la ficha técnica de depuración de los **6,7 millones de contratos OPS (2018–2026)** y descargue "
    "las tablas agregadas oficiales en formato **CSV (UTF-8 con BOM)** listas para Excel o análisis estadístico."
)

# ── BANNER FICHA METODOLÓGICA ────────────────────────────────────────────────
st.markdown(f"""
<div class="banner-download">
    <h2>📑 Base Oficial Depurada – Contratación por Prestación de Servicios (2018–2026)</h2>
    <p>
        Fuente: SECOP I + SECOP II (Colombia Compra Eficiente) • Corte de firma: <b>{meta.get('fecha_firma_min', '2018-01-01')}</b> a <b>{meta.get('fecha_firma_max', '2026')}</b>.<br>
        Registros brutos auditados: <b>{fmt_int_co(meta.get('total_filas_leidas', 0))}</b> |
        Duplicados eliminados: <b>{fmt_int_co(meta.get('total_duplicados_eliminados', 0))}</b> |
        Registros valor $0 descartados: <b>{fmt_int_co(meta.get('total_descartados_valor_cero', 0))}</b> |
        Universo final depurado: <b>{fmt_int_co(meta.get('total_contratos', 0))}</b> contratos por <b>{fmt_billones(meta.get('valor_total_cop', 0))}</b>.
    </p>
</div>
""", unsafe_allow_html=True)

# ── DESCARGA DE PRODUCTOS MAESTROS DEL PROYECTO ─────────────────────────────
st.markdown('<div class="section-header">📦 Productos Maestros Disponibles en la Carpeta del Proyecto</div>', unsafe_allow_html=True)

prod_cols = st.columns(3)
productos = [
    ("Analisis_Profundo_OPS_2014_2026.xlsx", "📊 Análisis Profundo Excel (20 pestañas)", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("Informe_Investigacion_OPS_Colombia_2014_2026.docx", "📝 Informe Técnico en Word", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ("Documento_Modificaciones_y_Mejoras_Producto.docx", "🛠️ Documento de Mejoras del Producto", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
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
            "Estos registros se mantienen intactos en el conteo oficial de contratos (6.700.430), "
            "pero su cuantía atípica se aísla de la Cuantía Real para no distorsionar los indicadores macroeconómicos."
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
        st.info("No se registraron contratos atípicos de digitación.")

# ── FICHA TÉCNICA DE CALIDAD DE DATOS ───────────────────────────────────────
with st.expander("📖 Ver Reglas Técnicas de Homologación y Calidad de Datos", expanded=False):
    st.markdown("""
    1. **Desduplicación Global (`ID Contrato`):** Se consolidan los reportes de SECOP I y SECOP II eliminando duplicados globales por `ID Contrato`. Cuando un mismo contrato aparece múltiples veces, se ordena descendentemente por cuantía para conservar siempre el registro con valor real.
    2. **Eliminación de Cuantía `$0`:** Se descartan todos los registros con `Valor del Contrato <= 0` o nulo para evitar distorsiones por borradores técnicos o convenios sin cuantía.
    3. **Clasificación Binaria `Tipo_Proveedor_final`:** Se homologan estrictamente todas las categorías a **`PERSONA NATURAL`** (Cédula de Ciudadanía, Cédula de Extranjería, NIT Persona Natural, Tarjeta de Identidad, Pasaporte, PPT, NUIP) y **`PERSONA JURIDICA`** (NIT Persona Jurídica, NIT, Sociedades Extranjeras, NIT Extranjería).
    4. **Carácter Territorial (`ORDEN_CPS`):** Se clasifica cada entidad en **`NACIONAL`**, **`DEPARTAMENTAL`** o **`MUNICIPAL`** (identificando explícitamente las Alcaldías dentro del orden territorial). El conteo por código oficial de entidad garantiza aditividad exacta (`Nacionales + Departamentales + Municipales = Total Entidades`).
    5. **Imputación Geográfica en 6 Niveles (99,92% de recuperación):** Recuperación de `Municipio Entidad` y cruce contra el catálogo oficial **DANE DIVIPOLA** para mapas coropléticos y de densidad.
    """)
