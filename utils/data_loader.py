"""
Cargador de datos, filtros institucionales compartidos y formateadores
para el Dashboard de Prestación de Servicios (OPS 2018–2026) – Colombia Compra Eficiente.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent   # dashboard_ops/
ROOT_DIR = BASE_DIR.parent                          # Derecho de Peticion ESPECTADOR/
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"

PARQUET_ENTIDADES = DATA_DIR / "ops_base_entidades.parquet"
PARQUET_MENSUAL = DATA_DIR / "ops_mensual.parquet"
PARQUET_RECURRENCIA = DATA_DIR / "ops_recurrencia_anual.parquet"
PARQUET_CONSECUTIVOS = DATA_DIR / "ops_consecutivos.parquet"
PARQUET_TOP_CONTRATISTAS = DATA_DIR / "ops_top_contratistas.parquet"
PARQUET_OUTLIERS = DATA_DIR / "ops_outliers_digitacion.parquet"
META_JSON = DATA_DIR / "ops_meta.json"

GEOJSON_DEPTO_PATH = ASSETS_DIR / "colombia_departamentos.geojson"
GEOJSON_MPIO_PATH = ASSETS_DIR / "colombia_municipios.geojson"
DIVIPOLA_COORDS_PATH = ASSETS_DIR / "divipola_coords.json"

# Etiquetas y colores oficiales por carácter territorial (ORDEN_CPS)
ORDEN_ORDER = ["NACIONAL", "DEPARTAMENTAL", "MUNICIPAL"]

ORDEN_LABELS = {
    "NACIONAL": "Nacional",
    "DEPARTAMENTAL": "Departamental",
    "MUNICIPAL": "Municipal",
}

ORDEN_COLORS = {
    "NACIONAL": "#174073",       # Azul institucional CCE
    "DEPARTAMENTAL": "#533965",  # Morado institucional CCE
    "MUNICIPAL": "#1E8449",      # Verde esmeralda territorial
}

GOBIERNO_ORDER = [
    "Santos II (cierre 2018)",
    "Duque (2018–2022)",
    "Petro (2022–2026)",
]

GOBIERNO_COLORS = {
    "Santos II (cierre 2018)": "#5A666A",
    "Duque (2018–2022)": "#174073",
    "Petro (2022–2026)": "#D61C38",
}

PROVEEDOR_COLORS = {
    "PERSONA NATURAL": "#174073",
    "PERSONA JURIDICA": "#D98A3C",
}

FUENTE_COLORS = {
    "SECOP II": "#1E8449",
    "SECOP I": "#D98A3C",
}


# ── Formateadores colombianos ───────────────────────────────────────────────

def fmt_int_co(value) -> str:
    """Formatea entero con separador de miles estilo colombiano (puntos): 6.700.430."""
    if value is None or pd.isna(value):
        return "0"
    return f"{int(round(float(value))):,}".replace(",", ".")


def fmt_dec_co(value, decimals: int = 2) -> str:
    """Formatea decimal con coma decimal y punto de miles: 331,45."""
    if value is None or pd.isna(value):
        return "0,00"
    s = f"{float(value):,.{decimals}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def fmt_billones(value: float, short: bool = False) -> str:
    """Formatea valor en Billones o Miles de Millones de COP (escala larga colombiana)."""
    if value is None or pd.isna(value):
        return "$ 0"
    val = float(value)
    b = val / 1e12
    if abs(b) >= 1.0:
        return f"$ {fmt_dec_co(b, 2)} B" if short else f"$ {fmt_dec_co(b, 2)} Billones"
    mm = val / 1e9
    if abs(mm) >= 1.0:
        return f"$ {fmt_dec_co(mm, 1)} MM" if short else f"$ {fmt_dec_co(mm, 1)} Mil Millones"
    m = val / 1e6
    return f"$ {fmt_dec_co(m, 1)} M" if short else f"$ {fmt_dec_co(m, 1)} Millones"


def fmt_cop_exacto(value: float) -> str:
    """Formatea pesos colombianos exactos con separador de miles en punto."""
    if value is None or pd.isna(value):
        return "$ 0"
    return f"$ {fmt_int_co(value)}"


# ── Cargas cacheadas ────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="⏳ Cargando base consolidada de Prestación de Servicios (2018–2026)...", ttl=3600)
def load_entidades_data() -> pd.DataFrame:
    if not PARQUET_ENTIDADES.exists():
        return pd.DataFrame()
    df = pd.read_parquet(PARQUET_ENTIDADES, engine="pyarrow")
    df["ANIO"] = df["ANIO"].astype(int)
    df["ANIO_STR"] = df["ANIO"].astype(str)
    return df


@st.cache_resource(show_spinner="⏳ Cargando serie mensual y estacionalidad...", ttl=3600)
def load_mensual_data() -> pd.DataFrame:
    if not PARQUET_MENSUAL.exists():
        return pd.DataFrame()
    df = pd.read_parquet(PARQUET_MENSUAL, engine="pyarrow")
    df["ANIO"] = df["ANIO"].astype(int)
    df["MES"] = df["MES"].astype(int)
    return df


@st.cache_resource(show_spinner=False, ttl=3600)
def load_recurrencia_data() -> pd.DataFrame:
    if not PARQUET_RECURRENCIA.exists():
        return pd.DataFrame()
    return pd.read_parquet(PARQUET_RECURRENCIA, engine="pyarrow")


@st.cache_resource(show_spinner=False, ttl=3600)
def load_consecutivos_data() -> pd.DataFrame:
    if not PARQUET_CONSECUTIVOS.exists():
        return pd.DataFrame()
    return pd.read_parquet(PARQUET_CONSECUTIVOS, engine="pyarrow")


@st.cache_resource(show_spinner=False, ttl=3600)
def load_top_contratistas() -> pd.DataFrame:
    if not PARQUET_TOP_CONTRATISTAS.exists():
        return pd.DataFrame()
    return pd.read_parquet(PARQUET_TOP_CONTRATISTAS, engine="pyarrow")


@st.cache_resource(show_spinner=False, ttl=3600)
def load_outliers_data() -> pd.DataFrame:
    if not PARQUET_OUTLIERS.exists():
        return pd.DataFrame()
    return pd.read_parquet(PARQUET_OUTLIERS, engine="pyarrow")


@st.cache_resource(show_spinner=False)
def load_meta() -> dict:
    if META_JSON.exists():
        return json.loads(META_JSON.read_text(encoding="utf-8"))
    return {}


@st.cache_resource(show_spinner=False)
def load_geojson_departamentos() -> dict:
    if GEOJSON_DEPTO_PATH.exists():
        return json.loads(GEOJSON_DEPTO_PATH.read_text(encoding="utf-8"))
    return {"type": "FeatureCollection", "features": []}


@st.cache_resource(show_spinner=False)
def load_geojson_municipios() -> dict:
    if GEOJSON_MPIO_PATH.exists():
        return json.loads(GEOJSON_MPIO_PATH.read_text(encoding="utf-8"))
    return {"type": "FeatureCollection", "features": []}


@st.cache_resource(show_spinner=False)
def load_divipola_coords() -> dict:
    if DIVIPOLA_COORDS_PATH.exists():
        return json.loads(DIVIPOLA_COORDS_PATH.read_text(encoding="utf-8"))
    return {"municipios": {}, "departamentos_code": {}, "departamentos_center": {}}


# ── Filtros globales del sidebar ────────────────────────────────────────────

def apply_filters(
    df: pd.DataFrame,
    anios=None,
    gobiernos=None,
    ordenes=None,
    departamentos=None,
    fuentes=None,
    tipos_proveedor=None,
    sectores=None,
) -> pd.DataFrame:
    if df.empty:
        return df
    mask = pd.Series(True, index=df.index)

    if anios and "Todas" not in anios:
        mask &= df["ANIO"].isin([int(a) for a in anios])

    if gobiernos and "GOBIERNO" in df.columns:
        mask &= df["GOBIERNO"].isin(gobiernos)

    if ordenes and "ORDEN_CPS" in df.columns:
        mask &= df["ORDEN_CPS"].isin(ordenes)

    if departamentos and "DEPARTAMENTO" in df.columns:
        mask &= df["DEPARTAMENTO"].isin(departamentos)

    if fuentes and "Todas" not in fuentes and "FUENTE" in df.columns:
        mask &= df["FUENTE"].isin(fuentes)

    if tipos_proveedor and "Todos" not in tipos_proveedor and "TIPO_PROVEEDOR_FINAL" in df.columns:
        mask &= df["TIPO_PROVEEDOR_FINAL"].isin(tipos_proveedor)

    if sectores and "SECTOR" in df.columns:
        mask &= df["SECTOR"].isin(sectores)

    return df[mask]


def render_sidebar_filters(df_raw: pd.DataFrame, return_state: bool = False):
    """
    Renderiza el panel lateral institucional de Colombia Compra Eficiente
    y retorna el DataFrame filtrado (y opcionalmente el diccionario de filtros activos).
    """
    meta = load_meta()
    with st.sidebar:
        logo_path = ASSETS_DIR / "escudo.png"
        if logo_path.exists():
            st.image(str(logo_path), width="stretch")

        st.markdown("## 🏛️ Observatorio OPS (2018–2026)")
        st.markdown("**Colombia Compra Eficiente**")
        st.caption("Prestación de Servicios • SECOP I y SECOP II")
        st.markdown("---")

        anios_disp = sorted(df_raw["ANIO"].dropna().unique().tolist())
        sel_anios = st.multiselect(
            "Vigencia (Año Firma)",
            options=["Todas"] + [str(a) for a in anios_disp],
            default=["Todas"],
        )

        gob_disp = [g for g in GOBIERNO_ORDER if g in df_raw["GOBIERNO"].unique()]
        sel_gobiernos = st.multiselect(
            "Periodo Presidencial",
            options=gob_disp,
            default=[],
        )

        ord_disp = [o for o in ORDEN_ORDER if o in df_raw["ORDEN_CPS"].unique()]
        sel_ordenes = st.multiselect(
            "Carácter Territorial",
            options=ord_disp,
            format_func=lambda x: ORDEN_LABELS.get(x, x),
            default=[],
        )

        deptos_disp = sorted([d for d in df_raw["DEPARTAMENTO"].dropna().unique().tolist() if d != "No Determinado"])
        if "No Determinado" in df_raw["DEPARTAMENTO"].unique():
            deptos_disp.append("No Determinado")
        sel_deptos = st.multiselect(
            "Departamento",
            options=deptos_disp,
            default=[],
        )

        sel_tipo_prov = st.radio(
            "Tipo de Proveedor Final",
            options=["Todos", "PERSONA NATURAL", "PERSONA JURIDICA"],
            format_func=lambda x: {
                "Todos": "Todos (Natural + Jurídica)",
                "PERSONA NATURAL": "Persona Natural",
                "PERSONA JURIDICA": "Persona Jurídica",
            }[x],
            horizontal=False,
        )

        with st.expander("⚙️ Filtros Avanzados (Plataforma / Sector)", expanded=False):
            fuentes_disp = sorted(df_raw["FUENTE"].dropna().unique().tolist())
            sel_fuentes = st.multiselect(
                "Plataforma SECOP",
                options=["Todas"] + fuentes_disp,
                default=["Todas"],
            )

            sectores_disp = sorted(df_raw["SECTOR"].dropna().unique().tolist()) if "SECTOR" in df_raw.columns else []
            sel_sectores = st.multiselect(
                "Sector Institucional",
                options=sectores_disp,
                default=[],
            )

        st.markdown("---")
        tot_c = meta.get("total_contratos", int(df_raw["N_CONTRATOS"].sum()))
        tot_e = meta.get("total_entidades_cod", int(df_raw["CODIGO_ENTIDAD"].nunique()))
        f_max = meta.get("fecha_firma_max", "2026")
        st.caption(f"📊 Base depurada: **{fmt_int_co(tot_c)}** contratos | **{fmt_int_co(tot_e)}** entidades")
        st.caption(f"🗓️ Corte de firmas hasta: **{f_max}**")
        st.caption("Sin duplicados • Cuantía > $0 • Proveedor binario")

    tipos_list = None if sel_tipo_prov == "Todos" else [sel_tipo_prov]
    filtros = {
        "anios": sel_anios,
        "gobiernos": sel_gobiernos,
        "ordenes": sel_ordenes,
        "departamentos": sel_deptos,
        "fuentes": sel_fuentes,
        "tipos_proveedor": tipos_list,
        "sectores": sel_sectores,
    }
    df_filt = apply_filters(df_raw, **filtros)
    if return_state:
        return df_filt, filtros
    return df_filt


def get_project_file(filename: str) -> Path:
    """Ubica archivos maestros generados en docs/ (para Streamlit Cloud) o en la carpeta raíz local."""
    for candidate in (BASE_DIR / "docs" / filename, ROOT_DIR / filename, BASE_DIR / filename):
        if candidate.exists():
            return candidate
    return BASE_DIR / "docs" / filename
