"""
Gráficos reutilizables y Mapas de Calor (Departamental y Municipal DANE DIVIPOLA)
para el Dashboard de Prestación de Servicios (OPS 2018–2026) – Colombia Compra Eficiente.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.data_loader import (
    ORDEN_ORDER,
    ORDEN_LABELS,
    ORDEN_COLORS,
    GOBIERNO_ORDER,
    GOBIERNO_COLORS,
    PROVEEDOR_COLORS,
    FUENTE_COLORS,
)

# ── Paleta institucional Colombia Compra Eficiente (ANCP - CCE) ──────────────
CCE_AMARILLO    = "#FFC000"
CCE_NARANJA     = "#D98A3C"
CCE_CAFE        = "#9C7238"
CCE_GRIS_OSCURO = "#5A666A"
CCE_GRIS_AZUL   = "#3E546C"
CCE_AZUL        = "#174073"
CCE_MORADO      = "#533965"
CCE_VINO_OSCURO = "#6A2444"
CCE_VINO_CLARO  = "#9E2044"
CCE_ROJO        = "#D61C38"
CCE_VERDE       = "#1E8449"

COLOR_SCALES = {
    "Institucional CCE (Azul-Naranja-Rojo)": [
        [0.0, "#EBF3FA"],
        [0.25, "#7FB3D5"],
        [0.5, "#174073"],
        [0.75, "#D98A3C"],
        [1.0, "#D61C38"],
    ],
    "Calor Intenso (Amarillo-Naranja-Rojo)": "YlOrRd",
    "Azul Institucional": "Blues",
    "Viridis (Alto Contraste)": "Viridis",
    "Plasma": "Plasma",
}

LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, Arial, sans-serif", color="#1A1A2E"),
    margin=dict(l=20, r=20, t=40, b=20),
)


# ── 1. Dona por Carácter Territorial (NACIONAL / DEPARTAMENTAL / MUNICIPAL) ─

def chart_dona_territorial(df: pd.DataFrame, metrica: str = "contratos") -> go.Figure:
    if df.empty:
        return go.Figure()
    grp = df.groupby("ORDEN_CPS", observed=True)
    if metrica == "valor":
        data = (grp["VALOR_TOTAL"].sum() / 1e12).reset_index(name="valor")
        unidad = "Billones COP"
        hover_fmt = "$%{value:,.2f} B"
    elif metrica == "entidades":
        data = grp["CODIGO_ENTIDAD"].nunique().reset_index(name="valor")
        unidad = "Entidades"
        hover_fmt = "%{value:,}"
    else:
        data = grp["N_CONTRATOS"].sum().reset_index(name="valor")
        unidad = "Contratos"
        hover_fmt = "%{value:,}"

    data["order_idx"] = data["ORDEN_CPS"].map({k: i for i, k in enumerate(ORDEN_ORDER)}).fillna(99)
    data = data.sort_values("order_idx")
    data["label"] = data["ORDEN_CPS"].map(ORDEN_LABELS).fillna(data["ORDEN_CPS"])
    data["color"] = data["ORDEN_CPS"].map(ORDEN_COLORS).fillna(CCE_GRIS_OSCURO)

    fig = go.Figure(go.Pie(
        labels=data["label"],
        values=data["valor"],
        hole=0.56,
        marker=dict(colors=data["color"].tolist(), line=dict(color="#FFFFFF", width=2.5)),
        textinfo="percent+label",
        insidetextorientation="auto",
        hovertemplate=f"<b>%{{label}}</b><br>{unidad}: {hover_fmt}<br>Participación: %{{percent}}<extra></extra>",
    ))
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.04, xanchor="center", x=0.5, font=dict(size=12)),
        annotations=[dict(
            text=f"<b>{unidad}</b>",
            x=0.5, y=0.5, font_size=13, showarrow=False,
            font_color=CCE_AZUL, font_family="Inter, Arial, sans-serif",
        )],
        height=370,
    )
    return fig


# ── 2. Evolución Anual por Carácter Territorial (2018–2026) ────────────────

def chart_evolucion_anual_orden(df: pd.DataFrame, metrica: str = "contratos", apilado: bool = True) -> go.Figure:
    if df.empty:
        return go.Figure()
    grp = df.groupby(["ANIO", "ORDEN_CPS"], observed=True)
    if metrica == "valor":
        data = (grp["VALOR_TOTAL"].sum() / 1e12).reset_index(name="valor")
        titulo_y = "Valor Contratado (Billones COP)"
        hover_fmt = "$%{y:,.2f} B"
    elif metrica == "entidades":
        data = grp["CODIGO_ENTIDAD"].nunique().reset_index(name="valor")
        titulo_y = "Entidades Únicas Activas"
        hover_fmt = "%{y:,}"
    else:
        data = grp["N_CONTRATOS"].sum().reset_index(name="valor")
        titulo_y = "Número de Contratos"
        hover_fmt = "%{y:,}"

    data["label"] = data["ORDEN_CPS"].map(ORDEN_LABELS).fillna(data["ORDEN_CPS"])
    data["ANIO_STR"] = data["ANIO"].astype(str)

    cat_order = [ORDEN_LABELS[k] for k in ORDEN_ORDER]
    color_map = {ORDEN_LABELS[k]: v for k, v in ORDEN_COLORS.items()}

    fig = px.bar(
        data,
        x="ANIO_STR",
        y="valor",
        color="label",
        category_orders={"label": cat_order, "ANIO_STR": sorted(data["ANIO_STR"].unique())},
        color_discrete_map=color_map,
        barmode="stack" if (apilado and metrica != "entidades") else "group",
        labels={"valor": titulo_y, "ANIO_STR": "Vigencia", "label": "Carácter Territorial"},
    )
    fig.update_traces(hovertemplate="<b>%{fullData.name}</b><br>Vigencia: %{x}<br>" + titulo_y + ": " + hover_fmt + "<extra></extra>")
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
        xaxis=dict(type="category"),
        yaxis=dict(gridcolor="#E6ECF2"),
        height=370,
    )
    return fig


# ── 3. Proveedor Final (Persona Natural vs Jurídica) y Plataforma SECOP ────

def chart_proveedor_binario(df: pd.DataFrame, metrica: str = "contratos") -> go.Figure:
    if df.empty:
        return go.Figure()
    grp = df.groupby("TIPO_PROVEEDOR_FINAL", observed=True)
    if metrica == "valor":
        data = (grp["VALOR_TOTAL"].sum() / 1e12).reset_index(name="valor")
        unidad = "Billones COP"
        hover_fmt = "$%{value:,.2f} B"
    else:
        data = grp["N_CONTRATOS"].sum().reset_index(name="valor")
        unidad = "Contratos"
        hover_fmt = "%{value:,}"

    data["label"] = data["TIPO_PROVEEDOR_FINAL"].replace({
        "PERSONA NATURAL": "Persona Natural",
        "PERSONA JURIDICA": "Persona Jurídica",
    })
    data["color"] = data["TIPO_PROVEEDOR_FINAL"].map(PROVEEDOR_COLORS).fillna(CCE_GRIS_OSCURO)

    fig = go.Figure(go.Pie(
        labels=data["label"],
        values=data["valor"],
        hole=0.56,
        marker=dict(colors=data["color"].tolist(), line=dict(color="#FFFFFF", width=2.5)),
        textinfo="percent+label",
        hovertemplate=f"<b>%{{label}}</b><br>{unidad}: {hover_fmt}<br>%{{percent}}<extra></extra>",
    ))
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.04, xanchor="center", x=0.5),
        annotations=[dict(text=f"<b>{unidad}</b>", x=0.5, y=0.5, font_size=12, showarrow=False, font_color=CCE_AZUL)],
        height=340,
    )
    return fig


def chart_genero_donut(df: pd.DataFrame, metrica: str = "contratos") -> go.Figure:
    """Dona de distribución por Género (Mujeres vs. Hombres en Personas Naturales)."""
    if df.empty:
        return go.Figure()
    if metrica == "valor":
        vm = float(df["VALOR_MUJER"].sum()) / 1e12
        vh = float(df["VALOR_HOMBRE"].sum()) / 1e12
        vo = max(float(df["VALOR_TOTAL"].sum()) / 1e12 - vm - vh, 0.0)
        unidad = "Billones COP"
        hover_fmt = "$%{value:,.2f} B"
        vals = [vm, vh, vo]
    else:
        cm = int(df["CONTRATOS_MUJER"].sum())
        ch = int(df["CONTRATOS_HOMBRE"].sum())
        co = max(int(df["N_CONTRATOS"].sum()) - cm - ch, 0)
        unidad = "Contratos"
        hover_fmt = "%{value:,}"
        vals = [cm, ch, co]

    labels = ["Mujeres", "Hombres", "No Definido"]
    colors = [CCE_MORADO, CCE_AZUL, "#94A3B8"]
    fig = go.Figure(go.Pie(
        labels=labels,
        values=vals,
        hole=0.56,
        marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2.5)),
        textinfo="percent+label",
        hovertemplate=f"<b>%{{label}}</b><br>{unidad}: {hover_fmt}<br>%{{percent}}<extra></extra>",
    ))
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.04, xanchor="center", x=0.5),
        annotations=[dict(text=f"<b>{unidad}</b>", x=0.5, y=0.5, font_size=12, showarrow=False, font_color=CCE_AZUL)],
        height=340,
    )
    return fig


def chart_transicion_secop(df: pd.DataFrame, metrica: str = "contratos") -> go.Figure:
    if df.empty:
        return go.Figure()
    grp = df.groupby(["ANIO", "FUENTE"], observed=True)
    if metrica == "valor":
        data = (grp["VALOR_TOTAL"].sum() / 1e12).reset_index(name="valor")
        titulo_y = "Valor (Billones COP)"
    else:
        data = grp["N_CONTRATOS"].sum().reset_index(name="valor")
        titulo_y = "Número de Contratos"

    tot_a = data.groupby("ANIO")["valor"].transform("sum")
    data["pct"] = np.where(tot_a > 0, data["valor"] / tot_a * 100.0, 0.0)
    data["ANIO_STR"] = data["ANIO"].astype(str)

    fig = px.bar(
        data,
        x="ANIO_STR",
        y="valor",
        color="FUENTE",
        color_discrete_map=FUENTE_COLORS,
        barmode="stack",
        custom_data=["pct"],
        labels={"valor": titulo_y, "ANIO_STR": "Vigencia", "FUENTE": "Plataforma"},
    )
    fig.update_traces(
        hovertemplate="<b>%{fullData.name}</b><br>Vigencia: %{x}<br>" + titulo_y + ": %{y:,.2f}<br>Participación anual: %{customdata[0]:.1f}%<extra></extra>"
        if metrica == "valor"
        else "<b>%{fullData.name}</b><br>Vigencia: %{x}<br>" + titulo_y + ": %{y:,}<br>Participación anual: %{customdata[0]:.1f}%<extra></extra>"
    )
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(gridcolor="#E6ECF2"),
        height=340,
    )
    return fig


# ── 4. Rankings de Entidades, Sectores y Departamentos ─────────────────────

def chart_top_entidades(df: pd.DataFrame, n: int = 20, por: str = "contratos") -> go.Figure:
    if df.empty:
        return go.Figure()
    grp = df.groupby(["NOMBRE_ENTIDAD", "ORDEN_CPS"], observed=True)
    if por == "valor":
        top = (grp["VALOR_TOTAL"].sum() / 1e12).reset_index(name="valor").nlargest(n, "valor")
        titulo_x = "Valor Contratado (Billones COP)"
        hover_val = "$%{x:,.3f} Billones"
    else:
        top = grp["N_CONTRATOS"].sum().reset_index(name="valor").nlargest(n, "valor")
        titulo_x = "Número de Contratos OPS"
        hover_val = "%{x:,} contratos"

    top = top.sort_values("valor", ascending=True)
    top["entidad_corta"] = top["NOMBRE_ENTIDAD"].astype(str).str[:54]
    top["color"] = top["ORDEN_CPS"].map(ORDEN_COLORS).fillna(CCE_AZUL)

    fig = go.Figure(go.Bar(
        x=top["valor"],
        y=top["entidad_corta"],
        customdata=np.stack([top["NOMBRE_ENTIDAD"], top["ORDEN_CPS"].map(ORDEN_LABELS).fillna(top["ORDEN_CPS"])], axis=-1),
        orientation="h",
        marker_color=top["color"].tolist(),
        text=top["valor"].apply(lambda v: f"${v:,.2f} B" if por == "valor" else f"{int(v):,}"),
        textposition="outside",
        hovertemplate="<b>%{customdata[0]}</b><br>Orden: %{customdata[1]}<br>" + titulo_x + ": " + hover_val + "<extra></extra>",
    ))
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        xaxis_title=titulo_x,
        yaxis_title="",
        xaxis=dict(gridcolor="#E6ECF2"),
        height=max(430, n * 27),
    )
    return fig


def chart_top_sectores(df: pd.DataFrame, n: int = 15, por: str = "contratos") -> go.Figure:
    if df.empty or "SECTOR" not in df.columns:
        return go.Figure()
    grp = df.groupby("SECTOR", observed=True)
    if por == "valor":
        top = (grp["VALOR_TOTAL"].sum() / 1e12).reset_index(name="valor").nlargest(n, "valor")
        titulo_x = "Valor Contratado (Billones COP)"
        hover_val = "$%{x:,.2f} B"
    elif por == "entidades":
        top = grp["CODIGO_ENTIDAD"].nunique().reset_index(name="valor").nlargest(n, "valor")
        titulo_x = "Entidades Únicas"
        hover_val = "%{x:,}"
    else:
        top = grp["N_CONTRATOS"].sum().reset_index(name="valor").nlargest(n, "valor")
        titulo_x = "Número de Contratos"
        hover_val = "%{x:,}"

    top = top.sort_values("valor", ascending=True)
    fig = go.Figure(go.Bar(
        x=top["valor"],
        y=top["SECTOR"],
        orientation="h",
        marker=dict(
            color=top["valor"],
            colorscale=[[0, "#DCE7F3"], [0.5, CCE_AZUL], [1, CCE_VINO_OSCURO]],
            showscale=False,
        ),
        text=top["valor"].apply(lambda v: f"${v:,.2f} B" if por == "valor" else f"{int(v):,}"),
        textposition="outside",
        hovertemplate=f"<b>%{{y}}</b><br>{titulo_x}: {hover_val}<extra></extra>",
    ))
    fig.update_layout(**LAYOUT_DEFAULTS, xaxis_title=titulo_x, yaxis_title="", height=max(400, n * 27))
    return fig


def chart_tipologias_objeto(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return go.Figure()
    vals = {
        "Apoyo a la Gestión": int(df["CONTRATOS_APOYO"].sum()),
        "Servicios Profesionales": int(df["CONTRATOS_PROFESIONAL"].sum()),
        "Técnico / Asistencial / Operativo": int(df["CONTRATOS_TECNICO"].sum()),
        "Otros Servicios": int(df["CONTRATOS_OTROS"].sum()),
    }
    data = pd.DataFrame({"Tipología": list(vals.keys()), "Contratos": list(vals.values())}).sort_values("Contratos", ascending=True)
    tot = max(data["Contratos"].sum(), 1)
    data["Pct"] = data["Contratos"] / tot * 100.0

    fig = go.Figure(go.Bar(
        x=data["Contratos"],
        y=data["Tipología"],
        orientation="h",
        marker_color=[CCE_GRIS_AZUL, CCE_NARANJA, CCE_MORADO, CCE_AZUL],
        text=data.apply(lambda r: f"{int(r['Contratos']):,} ({r['Pct']:.1f}%)", axis=1),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Contratos: %{x:,}<extra></extra>",
    ))
    fig.update_layout(**LAYOUT_DEFAULTS, xaxis_title="Número de Contratos", yaxis_title="", height=310)
    return fig


# ── 5. Agregaciones y Mapas de Calor Geográficos (Departamental y Municipal) ─

def aggregate_departamentos(df: pd.DataFrame) -> pd.DataFrame:
    df_d = df[df["DEPARTAMENTO"].notna() & (df["DEPARTAMENTO"] != "No Determinado") & (df["COD_DPTO"] != "00")].copy()
    if df_d.empty:
        return pd.DataFrame()

    # Contratos Persona Natural por departamento
    pn_d = (
        df_d[df_d["TIPO_PROVEEDOR_FINAL"] == "PERSONA NATURAL"]
        .groupby("COD_DPTO", observed=True)["N_CONTRATOS"]
        .sum()
        .reset_index(name="contratos_pn")
    )

    agg = (
        df_d.groupby(["COD_DPTO", "DEPARTAMENTO"], observed=True)
        .agg(
            contratos=("N_CONTRATOS", "sum"),
            valor_cop=("VALOR_TOTAL", "sum"),
            entidades=("CODIGO_ENTIDAD", "nunique"),
            municipios=("CODIGO_DIVIPOLA", lambda s: s[~s.astype(str).str.endswith("000")].nunique()),
            contratos_mujer=("CONTRATOS_MUJER", "sum"),
            contratos_hombre=("CONTRATOS_HOMBRE", "sum"),
            lat=("LATITUD", "mean"),
            lon=("LONGITUD", "mean"),
        )
        .reset_index()
    )
    agg = agg.merge(pn_d, on="COD_DPTO", how="left")
    agg["contratos_pn"] = agg["contratos_pn"].fillna(0)
    agg["valor_billones"] = agg["valor_cop"] / 1e12
    agg["valor_promedio_m"] = np.where(agg["contratos"] > 0, (agg["valor_cop"] / agg["contratos"]) / 1e6, 0.0)
    agg["pct_pn"] = np.where(agg["contratos"] > 0, agg["contratos_pn"] / agg["contratos"] * 100.0, 0.0)
    gen_def = agg["contratos_mujer"] + agg["contratos_hombre"]
    agg["pct_mujer"] = np.where(gen_def > 0, agg["contratos_mujer"] / gen_def * 100.0, 0.0)
    return agg


def chart_mapa_calor_departamentos(
    df: pd.DataFrame,
    geojson_depto: dict,
    metrica: str = "contratos",
    escala_nombre: str = "Institucional CCE (Azul-Naranja-Rojo)",
    estilo_mapa: str = "carto-positron",
) -> go.Figure:
    agg = aggregate_departamentos(df)
    if agg.empty:
        return go.Figure()

    metric_cfg = {
        "contratos": ("contratos", "Contratos OPS", ",.0f"),
        "valor": ("valor_billones", "Valor ($ Billones COP)", ",.2f"),
        "entidades": ("entidades", "Entidades Únicas", ",.0f"),
        "promedio": ("valor_promedio_m", "Valor Promedio ($ Millones)", ",.1f"),
        "pct_pn": ("pct_pn", "% Persona Natural", ".1f"),
        "pct_mujer": ("pct_mujer", "% Mujeres (Género def.)", ".1f"),
    }
    col_z, label_z, _ = metric_cfg.get(metrica, metric_cfg["contratos"])
    colorscale = COLOR_SCALES.get(escala_nombre, "YlOrRd")

    customdata = np.stack([
        agg["DEPARTAMENTO"],
        agg["contratos"],
        agg["valor_billones"],
        agg["entidades"],
        agg["municipios"],
        agg["valor_promedio_m"],
        agg["pct_mujer"],
    ], axis=-1)

    fig = go.Figure(go.Choroplethmap(
        geojson=geojson_depto,
        locations=agg["COD_DPTO"],
        featureidkey="id",
        z=agg[col_z],
        colorscale=colorscale,
        marker_opacity=0.84,
        marker_line_width=1.2,
        marker_line_color="#FFFFFF",
        colorbar=dict(
            title=dict(text=label_z, font=dict(size=12, color=CCE_AZUL)),
            thickness=16,
            len=0.75,
        ),
        customdata=customdata,
        hovertemplate=(
            "<b>🏛️ %{customdata[0]}</b><br>"
            "──────────────────────────<br>"
            "• <b>Contratos OPS:</b> %{customdata[1]:,}<br>"
            "• <b>Valor Contratado:</b> $%{customdata[2]:,.2f} Billones COP<br>"
            "• <b>Entidades Únicas:</b> %{customdata[3]:,}<br>"
            "• <b>Municipios Activos:</b> %{customdata[4]:,}<br>"
            "• <b>Valor Promedio / Contrato:</b> $%{customdata[5]:,.1f} Millones<br>"
            "• <b>% Mujeres (género def.):</b> %{customdata[6]:.1f}%<extra></extra>"
        ),
    ))

    if len(agg) == 1:
        center = dict(lat=float(agg["lat"].iloc[0]), lon=float(agg["lon"].iloc[0]))
        zoom = 6.5
    elif len(agg) <= 4:
        center = dict(lat=float(agg["lat"].mean()), lon=float(agg["lon"].mean()))
        zoom = 5.6
    else:
        center = dict(lat=4.5709, lon=-74.2973)
        zoom = 4.6

    fig.update_layout(
        map_style=estilo_mapa,
        map_zoom=zoom,
        map_center=center,
        margin=dict(l=0, r=0, t=10, b=0),
        height=560,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Arial, sans-serif"),
    )
    return fig


def aggregate_municipios(df: pd.DataFrame) -> pd.DataFrame:
    df_m = df[
        df["CODIGO_DIVIPOLA"].notna()
        & (~df["CODIGO_DIVIPOLA"].astype(str).str.endswith("000"))
        & df["LATITUD"].notna()
        & df["LONGITUD"].notna()
    ].copy()
    if df_m.empty:
        return pd.DataFrame()

    pn_m = (
        df_m[df_m["TIPO_PROVEEDOR_FINAL"] == "PERSONA NATURAL"]
        .groupby("CODIGO_DIVIPOLA", observed=True)["N_CONTRATOS"]
        .sum()
        .reset_index(name="contratos_pn")
    )

    agg = (
        df_m.groupby(["CODIGO_DIVIPOLA", "DEPARTAMENTO", "MUNICIPIO"], observed=True)
        .agg(
            contratos=("N_CONTRATOS", "sum"),
            valor_cop=("VALOR_TOTAL", "sum"),
            entidades=("CODIGO_ENTIDAD", "nunique"),
            contratos_mujer=("CONTRATOS_MUJER", "sum"),
            contratos_hombre=("CONTRATOS_HOMBRE", "sum"),
            lat=("LATITUD", "first"),
            lon=("LONGITUD", "first"),
        )
        .reset_index()
    )
    agg = agg.merge(pn_m, on="CODIGO_DIVIPOLA", how="left")
    agg["contratos_pn"] = agg["contratos_pn"].fillna(0)
    agg["valor_mm"] = agg["valor_cop"] / 1e9
    agg["valor_promedio_m"] = np.where(agg["contratos"] > 0, (agg["valor_cop"] / agg["contratos"]) / 1e6, 0.0)
    agg["pct_pn"] = np.where(agg["contratos"] > 0, agg["contratos_pn"] / agg["contratos"] * 100.0, 0.0)
    gen_def = agg["contratos_mujer"] + agg["contratos_hombre"]
    agg["pct_mujer"] = np.where(gen_def > 0, agg["contratos_mujer"] / gen_def * 100.0, 0.0)
    return agg


def chart_mapa_calor_municipios(
    df: pd.DataFrame,
    geojson_mpio: dict = None,
    metrica: str = "contratos",
    modo: str = "densidad",
    escala_nombre: str = "Institucional CCE (Azul-Naranja-Rojo)",
    estilo_mapa: str = "carto-positron",
) -> go.Figure:
    agg = aggregate_municipios(df)
    if agg.empty:
        return go.Figure()

    metric_cfg = {
        "contratos": ("contratos", "Contratos OPS"),
        "valor": ("valor_mm", "Valor ($ Miles de Millones)"),
        "entidades": ("entidades", "Entidades Únicas"),
        "promedio": ("valor_promedio_m", "Valor Promedio ($ Millones)"),
        "pct_pn": ("pct_pn", "% Persona Natural"),
        "pct_mujer": ("pct_mujer", "% Mujeres (Género def.)"),
    }
    col_z, label_z = metric_cfg.get(metrica, metric_cfg["contratos"])
    colorscale = COLOR_SCALES.get(escala_nombre, "YlOrRd")

    customdata = np.stack([
        agg["MUNICIPIO"],
        agg["DEPARTAMENTO"],
        agg["CODIGO_DIVIPOLA"],
        agg["contratos"],
        agg["valor_mm"],
        agg["entidades"],
        agg["valor_promedio_m"],
        agg["pct_mujer"],
    ], axis=-1)

    hover_template = (
        "<b>📍 %{customdata[0]} (%{customdata[1]})</b><br>"
        "DIVIPOLA: <b>%{customdata[2]}</b><br>"
        "──────────────────────────<br>"
        "• <b>Contratos OPS:</b> %{customdata[3]:,}<br>"
        "• <b>Valor Contratado:</b> $%{customdata[4]:,.1f} Miles de Millones COP<br>"
        "• <b>Entidades Únicas:</b> %{customdata[5]:,}<br>"
        "• <b>Valor Promedio / Contrato:</b> $%{customdata[6]:,.1f} Millones<br>"
        "• <b>% Mujeres (género def.):</b> %{customdata[7]:.1f}%<extra></extra>"
    )

    n_deptos = agg["DEPARTAMENTO"].nunique()
    if n_deptos == 1:
        center = dict(lat=float(agg["lat"].mean()), lon=float(agg["lon"].mean()))
        zoom = 6.9
        radius_heat = 28
    elif n_deptos <= 4:
        center = dict(lat=float(agg["lat"].mean()), lon=float(agg["lon"].mean()))
        zoom = 5.8
        radius_heat = 22
    else:
        center = dict(lat=4.5709, lon=-74.2973)
        zoom = 4.65
        radius_heat = 17

    fig = go.Figure()

    if modo == "coropletico" and geojson_mpio and geojson_mpio.get("features"):
        if n_deptos <= 6:
            valid_codes = set(agg["CODIGO_DIVIPOLA"].unique())
            sub_geo = {
                "type": "FeatureCollection",
                "features": [f for f in geojson_mpio["features"] if f.get("id") in valid_codes],
            }
        else:
            sub_geo = geojson_mpio

        fig.add_trace(go.Choroplethmap(
            geojson=sub_geo,
            locations=agg["CODIGO_DIVIPOLA"],
            featureidkey="id",
            z=agg[col_z],
            colorscale=colorscale,
            marker_opacity=0.82,
            marker_line_width=0.5,
            marker_line_color="rgba(255,255,255,0.6)",
            colorbar=dict(title=dict(text=label_z, font=dict(size=12, color=CCE_AZUL)), thickness=16, len=0.75),
            customdata=customdata,
            hovertemplate=hover_template,
        ))
    elif modo == "burbujas":
        vals = agg[col_z].clip(lower=0).fillna(0)
        max_v = vals.max() if vals.max() > 0 else 1
        sizes = 6 + 26 * np.sqrt(vals / max_v)
        fig.add_trace(go.Scattermap(
            lat=agg["lat"],
            lon=agg["lon"],
            mode="markers",
            marker=dict(
                size=sizes,
                color=agg[col_z],
                colorscale=colorscale,
                showscale=True,
                opacity=0.82,
                colorbar=dict(title=dict(text=label_z, font=dict(size=12, color=CCE_AZUL)), thickness=16, len=0.75),
            ),
            customdata=customdata,
            hovertemplate=hover_template,
        ))
    else:
        fig.add_trace(go.Densitymap(
            lat=agg["lat"],
            lon=agg["lon"],
            z=agg[col_z],
            radius=radius_heat,
            colorscale=colorscale,
            opacity=0.78,
            colorbar=dict(title=dict(text=label_z, font=dict(size=12, color=CCE_AZUL)), thickness=16, len=0.75),
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scattermap(
            lat=agg["lat"],
            lon=agg["lon"],
            mode="markers",
            marker=dict(size=6 if n_deptos > 4 else 9, color=CCE_AZUL, opacity=0.62),
            customdata=customdata,
            hovertemplate=hover_template,
            name="Municipios",
            showlegend=False,
        ))

    fig.update_layout(
        map_style=estilo_mapa,
        map_zoom=zoom,
        map_center=center,
        margin=dict(l=0, r=0, t=10, b=0),
        height=560,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Arial, sans-serif"),
    )
    return fig


def chart_matriz_calor_territorial(df: pd.DataFrame, dim_col: str = "ANIO", metrica: str = "contratos", top_n: int = 18) -> go.Figure:
    df_valid = df[df["DEPARTAMENTO"] != "No Determinado"].copy()
    if df_valid.empty:
        return go.Figure()

    if metrica == "valor":
        top_deptos = df_valid.groupby("DEPARTAMENTO", observed=True)["VALOR_TOTAL"].sum().nlargest(top_n).index.tolist()
        piv = (
            (df_valid[df_valid["DEPARTAMENTO"].isin(top_deptos)]
             .groupby(["DEPARTAMENTO", dim_col], observed=True)["VALOR_TOTAL"]
             .sum() / 1e9)
            .round(1)
            .unstack(fill_value=0)
        )
        unidad = "Miles de Millones COP"
    elif metrica == "entidades":
        top_deptos = df_valid.groupby("DEPARTAMENTO", observed=True)["CODIGO_ENTIDAD"].nunique().nlargest(top_n).index.tolist()
        piv = (
            df_valid[df_valid["DEPARTAMENTO"].isin(top_deptos)]
            .groupby(["DEPARTAMENTO", dim_col], observed=True)["CODIGO_ENTIDAD"]
            .nunique()
            .unstack(fill_value=0)
        )
        unidad = "Entidades"
    else:
        top_deptos = df_valid.groupby("DEPARTAMENTO", observed=True)["N_CONTRATOS"].sum().nlargest(top_n).index.tolist()
        piv = (
            df_valid[df_valid["DEPARTAMENTO"].isin(top_deptos)]
            .groupby(["DEPARTAMENTO", dim_col], observed=True)["N_CONTRATOS"]
            .sum()
            .unstack(fill_value=0)
        )
        unidad = "Contratos"

    piv = piv.reindex([d for d in top_deptos if d in piv.index])
    fig = px.imshow(
        piv,
        text_auto=True,
        aspect="auto",
        color_continuous_scale=[[0.0, "#F8FAFC"], [0.35, "#90B4D4"], [0.7, CCE_AZUL], [1.0, CCE_ROJO]],
        labels=dict(x="", y="Departamento", color=unidad),
    )
    fig.update_layout(**LAYOUT_DEFAULTS, xaxis_tickangle=-20, height=max(460, len(piv) * 28))
    return fig


def chart_top_departamentos(df: pd.DataFrame, n: int = 18, por: str = "contratos") -> go.Figure:
    agg = aggregate_departamentos(df)
    if agg.empty:
        return go.Figure()
    col_map = {
        "contratos": ("contratos", "Número de Contratos OPS", "%{x:,}"),
        "valor": ("valor_billones", "Valor Contratado (Billones COP)", "$%{x:,.2f} B"),
        "entidades": ("entidades", "Entidades Únicas", "%{x:,}"),
    }
    col, titulo_x, hover_fmt = col_map.get(por, col_map["contratos"])
    top = agg.nlargest(n, col).sort_values(col, ascending=True)

    fig = go.Figure(go.Bar(
        x=top[col],
        y=top["DEPARTAMENTO"],
        orientation="h",
        marker=dict(color=top[col], colorscale=[[0, "#DCE7F3"], [0.6, CCE_AZUL], [1, CCE_ROJO]], showscale=False),
        text=top[col].apply(lambda v: f"${v:,.2f} B" if por == "valor" else f"{int(v):,}"),
        textposition="outside",
        hovertemplate=f"<b>%{{y}}</b><br>{titulo_x}: {hover_fmt}<extra></extra>",
    ))
    fig.update_layout(**LAYOUT_DEFAULTS, xaxis_title=titulo_x, yaxis_title="", height=max(420, n * 27))
    return fig


def chart_distribucion_departamentos_por_orden(
    df: pd.DataFrame,
    metrica: str = "contratos",
    top_n: int = 18,
    porcentaje: bool = False,
) -> go.Figure:
    """
    Barras horizontales apiladas por Departamento desglosadas por Carácter Territorial
    (NACIONAL / DEPARTAMENTAL / MUNICIPAL), al estilo de la distribución departamental
    del Dashboard de referencia EMAE.
    """
    df_valid = df[df["DEPARTAMENTO"].notna() & (df["DEPARTAMENTO"] != "No Determinado")].copy()
    if df_valid.empty:
        return go.Figure()

    if metrica == "valor":
        grp = (df_valid.groupby(["DEPARTAMENTO", "ORDEN_CPS"], observed=True)["VALOR_TOTAL"].sum() / 1e12).reset_index(name="valor")
        titulo_x = "Valor Contratado ($ Billones COP)"
    elif metrica == "entidades":
        grp = df_valid.groupby(["DEPARTAMENTO", "ORDEN_CPS"], observed=True)["CODIGO_ENTIDAD"].nunique().reset_index(name="valor")
        titulo_x = "Entidades Únicas Activas"
    else:
        grp = df_valid.groupby(["DEPARTAMENTO", "ORDEN_CPS"], observed=True)["N_CONTRATOS"].sum().reset_index(name="valor")
        titulo_x = "Número de Contratos OPS"

    tot_dpto = grp.groupby("DEPARTAMENTO")["valor"].sum().nlargest(top_n).index.tolist()
    top = grp[grp["DEPARTAMENTO"].isin(tot_dpto)].copy()
    top["Carácter"] = top["ORDEN_CPS"].map(ORDEN_LABELS).fillna(top["ORDEN_CPS"])

    tot_por_dpto = top.groupby("DEPARTAMENTO")["valor"].transform("sum").clip(lower=1e-9)
    top["pct"] = top["valor"] / tot_por_dpto * 100.0

    x_col = "pct" if porcentaje else "valor"
    if porcentaje:
        titulo_x = "Participación dentro del Departamento (%)"

    cat_order = [ORDEN_LABELS[k] for k in ORDEN_ORDER]
    color_map = {ORDEN_LABELS[k]: v for k, v in ORDEN_COLORS.items()}

    fig = px.bar(
        top,
        y="DEPARTAMENTO",
        x=x_col,
        color="Carácter",
        orientation="h",
        color_discrete_map=color_map,
        category_orders={"DEPARTAMENTO": tot_dpto, "Carácter": cat_order},
        custom_data=["valor", "pct"],
        labels={x_col: titulo_x, "DEPARTAMENTO": "", "Carácter": "Carácter Territorial"},
    )
    if porcentaje:
        hover_tpl = "<b>%{y}</b> – %{fullData.name}<br>Participación: <b>%{x:.1f}%</b><br>Valor absoluto: %{customdata[0]:,.2f}<extra></extra>" if metrica == "valor" else "<b>%{y}</b> – %{fullData.name}<br>Participación: <b>%{x:.1f}%</b><br>Cantidad: %{customdata[0]:,}<extra></extra>"
    else:
        hover_tpl = "<b>%{y}</b> – %{fullData.name}<br>" + titulo_x + ": <b>$%{x:,.2f} B</b> (%{customdata[1]:.1f}%)<extra></extra>" if metrica == "valor" else "<b>%{y}</b> – %{fullData.name}<br>" + titulo_x + ": <b>%{x:,}</b> (%{customdata[1]:.1f}%)<extra></extra>"

    fig.update_traces(hovertemplate=hover_tpl)
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        barmode="stack",
        xaxis_title=titulo_x,
        yaxis=dict(autorange="reversed"),
        xaxis=dict(gridcolor="#E6ECF2", range=[0, 100] if porcentaje else None),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0, font=dict(size=11)),
        height=max(460, len(tot_dpto) * 26),
    )
    return fig


def chart_mapa_depto_orden_individual(
    df_orden: pd.DataFrame,
    geojson_depto: dict,
    metrica: str = "contratos",
    colorscale=None,
    estilo_mapa: str = "carto-positron",
) -> go.Figure:
    """Mapa coroplético compacto por departamento para el tríptico comparativo de carácter territorial."""
    agg = aggregate_departamentos(df_orden)
    if agg.empty:
        return go.Figure()

    col_map = {
        "contratos": ("contratos", "Contratos"),
        "valor": ("valor_billones", "Valor ($ B)"),
        "entidades": ("entidades", "Entidades"),
    }
    col_z, label_z = col_map.get(metrica, col_map["contratos"])
    customdata = np.stack([
        agg["DEPARTAMENTO"],
        agg["contratos"],
        agg["valor_billones"],
        agg["entidades"],
    ], axis=-1)

    fig = go.Figure(go.Choroplethmap(
        geojson=geojson_depto,
        locations=agg["COD_DPTO"],
        featureidkey="id",
        z=agg[col_z],
        colorscale=colorscale or "Blues",
        showscale=False,
        marker_opacity=0.86,
        marker_line_width=0.9,
        marker_line_color="#FFFFFF",
        customdata=customdata,
        hovertemplate=(
            "<b>🏛️ %{customdata[0]}</b><br>"
            "• Contratos: <b>%{customdata[1]:,}</b><br>"
            "• Valor Real: <b>$%{customdata[2]:,.2f} B</b><br>"
            "• Entidades: <b>%{customdata[3]:,}</b><extra></extra>"
        ),
    ))
    fig.update_layout(
        map=dict(style=estilo_mapa, center=dict(lat=4.5709, lon=-74.2973), zoom=4.1),
        margin=dict(l=0, r=0, t=0, b=0),
        height=390,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Arial, sans-serif"),
    )
    return fig


# ── 6. Serie Mensual con Bandas de Ley de Garantías Electorales ─────────────

def chart_serie_mensual_garantias(df_mes: pd.DataFrame, metrica: str = "contratos") -> go.Figure:
    if df_mes.empty:
        return go.Figure()
    grp = (
        df_mes.groupby("ANIO_MES", observed=True)
        .agg(contratos=("N_CONTRATOS", "sum"), valor=("VALOR_TOTAL", lambda s: s.sum() / 1e12))
        .reset_index()
        .sort_values("ANIO_MES")
    )
    col_y = "valor" if metrica == "valor" else "contratos"
    titulo_y = "Valor Mensual (Billones COP)" if metrica == "valor" else "Contratos Firmados por Mes"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=grp["ANIO_MES"],
        y=grp[col_y],
        mode="lines+markers",
        line=dict(color=CCE_AZUL, width=2.5),
        marker=dict(size=5, color=CCE_ROJO),
        fill="tozeroy",
        fillcolor="rgba(23, 64, 115, 0.10)",
        name=titulo_y,
        hovertemplate="<b>%{x}</b><br>" + titulo_y + (": $%{y:,.2f} B" if metrica == "valor" else ": %{y:,}") + "<extra></extra>",
    ))

    # Sombrear periodos de Ley de Garantías Electorales (Presidenciales/Congreso y Territoriales)
    bandas = [
        ("2018-01", "2018-06", "Ley Garantías Pres. 2018", "rgba(214, 28, 56, 0.10)"),
        ("2019-06", "2019-10", "Territoriales 2019", "rgba(217, 138, 60, 0.12)"),
        ("2022-01", "2022-06", "Ley Garantías Pres. 2022", "rgba(214, 28, 56, 0.10)"),
        ("2023-06", "2023-10", "Territoriales 2023", "rgba(217, 138, 60, 0.12)"),
        ("2026-01", "2026-06", "Presidenciales 2026", "rgba(214, 28, 56, 0.10)"),
    ]
    meses_presentes = set(grp["ANIO_MES"].tolist())
    x_min, x_max = grp["ANIO_MES"].min(), grp["ANIO_MES"].max()
    for x0, x1, txt, col_bg in bandas:
        if x1 >= x_min and x0 <= x_max:
            fig.add_vrect(
                x0=max(x0, x_min),
                x1=min(x1, x_max),
                fillcolor=col_bg,
                layer="below",
                line_width=0,
                annotation_text=txt,
                annotation_position="top left",
                annotation_font_size=10,
                annotation_font_color=CCE_VINO_OSCURO,
            )

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        xaxis_title="Mes de Firma (YYYY-MM)",
        yaxis_title=titulo_y,
        yaxis=dict(gridcolor="#E6ECF2"),
        xaxis=dict(tickangle=-35, nticks=22),
        height=430,
    )
    return fig
