# -*- coding: utf-8 -*-
"""
patch_valor_real_y_calidad.py
Aplica de forma quirúrgica sobre las tablas Parquet del Dashboard OPS (2018-2026):
1. Separación oficial de Cuantía Real (VALOR_TOTAL) vs. Cuantía Nominal Bruta (VALOR_NOMINAL),
   aislando errores extremos de digitación de ceros en SECOP:
     - Cualquier contrato individual con valor >= $1 Billón COP (1e12), o
     - Contrato individual de Persona Natural con valor >= $5.000 Millones COP (5e9)
   Se conservan el 100% de los 6.700.430 contratos en el conteo y se guarda la tabla
   auditable `ops_outliers_digitacion.parquet` con el ID Contrato exacto de cada atípico.
2. Normalización de capitalización en 3 sectores (`agricultura`, `defensa`, `interior`).
3. Empate adicional de alias DIVIPOLA para elevar georreferenciación municipal a >99.9%.
"""

import glob
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

DASH_DIR = Path(__file__).resolve().parent
ROOT_DIR = DASH_DIR.parent
DATA_DIR = DASH_DIR / "data"
ASSETS_DIR = DASH_DIR / "assets"

sys.path.insert(0, str(ROOT_DIR))
from exportar_gobiernos_xlsx import encabezados
from dashboard_ops.build_dashboard_data import (
    DPTO_STD_MAP,
    clasificar_gobierno_vec,
    limpiar_sector_serie,
)

UMBRAL_GENERAL = 1e12   # $1 Billón COP en un contrato individual OPS
UMBRAL_PN = 5e9         # $5.000 Millones COP en un contrato individual de Persona Natural

SECTOR_FIX = {
    "agricultura": "Agricultura y Desarrollo Rural",
    "defensa": "Defensa",
    "interior": "Interior",
}

DIVI_EXTRA_FIX = {
    ("Cundinamarca", "Bogotá"): ("11001", "Bogotá D.C.", 4.6493, -74.1070),
    ("Córdoba", "San Andrés Sotavento"): ("23670", "San Andrés De Sotavento", 9.1453, -75.5072),
    ("Sucre", "Toluviejo"): ("70823", "Tolú Viejo", 9.4508, -75.4383),
    ("Tolima", "Guayabal"): ("73055", "Armero", 4.9669, -74.8856),
    ("Norte de Santander", "Santodomigo De Silos"): ("54743", "Silos", 7.2044, -72.7564),
}


def main():
    t0 = time.time()
    print("=" * 72)
    print("PARCHE DE CALIDAD: CUANTÍA REAL VS. NOMINAL, SECTORES Y DIVIPOLA")
    print("=" * 72)

    # 1. Escanear únicamente contratos atípicos en los 5 CSVs (idéntica regla de deduplicación)
    archivos = [f for f in sorted(glob.glob(str(ROOT_DIR / "Resultados*.csv"))) if "2014 2016" not in f]
    cols = [
        "ID Contrato", "Fecha Firma", "Año firma", "Codigo Entidad", "Nit Entidad",
        "Nombre Entidad", "NOMBRE ENTIDAD UNIFICADO", "ORDEN", "ALCALDIA",
        "Departamento_final", "FUENTE", "Sector_final", "Sexo_final",
        "Tipo Proveedor", "Tipo_Proveedor_final", "Identificacion Proveedor",
        "Nombre Proveedor", "Valor del Contrato",
    ]

    seen_big = set()
    outlier_chunks = []

    for f in archivos:
        print(f"Escaneando atípicos en {Path(f).name}...", flush=True)
        for chunk in pd.read_csv(
            f, sep=";", header=None, names=encabezados, usecols=cols,
            chunksize=400000, low_memory=False, encoding="utf-8-sig",
            encoding_errors="replace", on_bad_lines="skip",
        ):
            fechas_10 = chunk["Fecha Firma"].fillna("").astype(str).str[:10]
            anios = pd.to_numeric(fechas_10.str[:4], errors="coerce").fillna(
                pd.to_numeric(chunk["Año firma"], errors="coerce")
            ).fillna(0).astype(int)
            mask_a = (anios >= 2018) & (anios <= 2026)
            if not mask_a.any():
                continue
            chunk = chunk[mask_a].copy()
            anios = anios[mask_a]
            fechas_10 = fechas_10[mask_a]

            val_num = pd.to_numeric(
                chunk["Valor del Contrato"].astype(str).str.strip().str.replace(",", ".").str.replace(" ", ""),
                errors="coerce",
            ).fillna(0.0)

            # Solo necesitamos revisar filas >= UMBRAL_PN (5e9)
            mask_big = val_num >= UMBRAL_PN
            if not mask_big.any():
                continue
            sub = chunk[mask_big].copy()
            sub["_val_num"] = val_num[mask_big].values
            sub["ANIO"] = anios[mask_big].values
            sub["_fecha10"] = fechas_10[mask_big].values

            # Deduplicar igual que el pipeline principal (orden descendente por valor)
            sub = sub.sort_values("_val_num", ascending=False)
            cids = sub["ID Contrato"].astype(str)
            sub = sub[~cids.isin(seen_big)].drop_duplicates(subset=["ID Contrato"], keep="first").copy()
            if sub.empty:
                continue
            seen_big.update(sub["ID Contrato"].astype(str))

            # Clasificación binaria Tipo_Proveedor_final
            tp_u = sub["Tipo Proveedor"].fillna("").astype(str).str.upper()
            tpf_u = sub["Tipo_Proveedor_final"].fillna("").astype(str).str.upper()
            m_nat = tp_u.str.contains(r"CEDULA|CÉDULA|PERSONA NATURAL|TARJETA DE IDENTIDAD|PASAPORTE|PERMISO|CARNE|CARNÉ|NUIP", regex=True)
            m_jur = tp_u.str.contains(r"PERSONA JURIDICA|PERSONA JURÍDICA|SOCIEDAD|EXTRANJERIA|EXTRANJERÍA", regex=True) | (tp_u == "NIT")
            sub["TIPO_PROVEEDOR_FINAL"] = np.where(
                m_nat, "PERSONA NATURAL",
                np.where(m_jur, "PERSONA JURIDICA", np.where(tpf_u.str.contains("NATURAL"), "PERSONA NATURAL", "PERSONA JURIDICA"))
            )

            # Aplicar regla de outlier de digitación
            is_out = (sub["_val_num"] >= UMBRAL_GENERAL) | ((sub["TIPO_PROVEEDOR_FINAL"] == "PERSONA NATURAL") & (sub["_val_num"] >= UMBRAL_PN))
            sub = sub[is_out].copy()
            if sub.empty:
                continue

            sub["MES"] = pd.to_numeric(sub["_fecha10"].str[5:7], errors="coerce").fillna(1).astype(int).clip(1, 12)
            sub["ANIO_MES"] = sub["ANIO"].astype(str) + "-" + sub["MES"].astype(str).str.zfill(2)
            sub["GOBIERNO"] = clasificar_gobierno_vec(sub["_fecha10"], sub["ANIO"])

            ord_s = sub["ORDEN"].fillna("DEPARTAMENTAL").astype(str).str.strip().str.upper()
            alc_s = sub["ALCALDIA"].fillna("").astype(str).str.strip().str.upper().isin(["SI", "SÍ"])
            ord_s = np.where(alc_s, "MUNICIPAL", np.where(ord_s == "TERRITORIAL", "DEPARTAMENTAL", ord_s))
            sub["ORDEN_CPS"] = np.where(pd.Series(ord_s).isin(["NACIONAL", "DEPARTAMENTAL", "MUNICIPAL"]), ord_s, "DEPARTAMENTAL")

            fuente_up = sub["FUENTE"].fillna("SECOP_I").astype(str).str.strip().str.upper()
            sub["FUENTE"] = np.where(fuente_up.str.contains("II|2"), "SECOP II", "SECOP I")

            cod_ent = sub["Codigo Entidad"].fillna("").astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
            nom_ent = sub["NOMBRE ENTIDAD UNIFICADO"].replace("", np.nan).fillna(sub["Nombre Entidad"]).fillna("NO DEFINIDA").astype(str).str.strip()
            sub["CODIGO_ENTIDAD"] = np.where(cod_ent == "", nom_ent, cod_ent)
            sub["NOMBRE_ENTIDAD"] = nom_ent

            sexo_up = sub["Sexo_final"].fillna("NO DEFINIDO").astype(str).str.strip().str.upper()
            sub["VAL_MUJER_OUT"] = np.where((sub["TIPO_PROVEEDOR_FINAL"] == "PERSONA NATURAL") & (sexo_up == "MUJER"), sub["_val_num"], 0.0)
            sub["VAL_HOMBRE_OUT"] = np.where((sub["TIPO_PROVEEDOR_FINAL"] == "PERSONA NATURAL") & (sexo_up == "HOMBRE"), sub["_val_num"], 0.0)
            sub["MOTIVO_ATIPICO"] = np.where(
                sub["_val_num"] >= UMBRAL_GENERAL,
                "Cuantía individual >= $1 Billón COP (error de digitación de ceros)",
                "Persona Natural individual >= $5.000 Millones COP (error de digitación)",
            )
            outlier_chunks.append(sub)

    df_out = pd.concat(outlier_chunks, ignore_index=True).sort_values("_val_num", ascending=False)
    print(f"\nTotal atípicos de digitación identificados: {len(df_out):,} contratos | Suma = ${df_out['_val_num'].sum()/1e12:,.2f} Billones COP")

    # Guardar tabla auditable de atípicos
    df_out_save = df_out[[
        "ANIO", "ANIO_MES", "ID Contrato", "ORDEN_CPS", "FUENTE",
        "CODIGO_ENTIDAD", "NOMBRE_ENTIDAD", "TIPO_PROVEEDOR_FINAL",
        "Identificacion Proveedor", "Nombre Proveedor", "_val_num", "MOTIVO_ATIPICO",
    ]].rename(columns={
        "ID Contrato": "ID_CONTRATO",
        "Identificacion Proveedor": "ID_PROVEEDOR",
        "Nombre Proveedor": "NOMBRE_PROVEEDOR",
        "_val_num": "VALOR_DIGITADO_COP",
    })
    df_out_save.to_parquet(DATA_DIR / "ops_outliers_digitacion.parquet", index=False, compression="snappy")

    # 2. Actualizar ops_base_entidades.parquet
    df_ent = pd.read_parquet(DATA_DIR / "ops_base_entidades.parquet")
    if "VALOR_NOMINAL" not in df_ent.columns:
        df_ent["VALOR_NOMINAL"] = df_ent["VALOR_TOTAL"]
    else:
        df_ent["VALOR_TOTAL"] = df_ent["VALOR_NOMINAL"]

    # Agregar sustracciones por clave (ANIO, GOBIERNO, ORDEN_CPS, CODIGO_ENTIDAD, FUENTE, TIPO_PROVEEDOR_FINAL)
    out_ent_key = ["ANIO", "GOBIERNO", "ORDEN_CPS", "CODIGO_ENTIDAD", "FUENTE", "TIPO_PROVEEDOR_FINAL"]
    out_ent_agg = (
        df_out.groupby(out_ent_key, observed=True)
        .agg(
            _sub_val=("_val_num", "sum"),
            _sub_muj=("VAL_MUJER_OUT", "sum"),
            _sub_hom=("VAL_HOMBRE_OUT", "sum"),
        )
        .reset_index()
    )

    # Si una clave tiene múltiples filas en df_ent (por municipio/sector), aplicar sustracción solo a la fila con mayor VALOR_NOMINAL
    df_ent = df_ent.sort_values("VALOR_NOMINAL", ascending=False).reset_index(drop=True)
    df_ent["_row_rank"] = df_ent.groupby(out_ent_key, observed=True).cumcount()
    out_ent_agg["_row_rank"] = 0

    df_ent = df_ent.merge(out_ent_agg, on=out_ent_key + ["_row_rank"], how="left")
    df_ent["_sub_val"] = df_ent["_sub_val"].fillna(0.0)
    df_ent["_sub_muj"] = df_ent["_sub_muj"].fillna(0.0)
    df_ent["_sub_hom"] = df_ent["_sub_hom"].fillna(0.0)

    df_ent["VALOR_TOTAL"] = (df_ent["VALOR_NOMINAL"] - df_ent["_sub_val"]).clip(lower=0.0)
    df_ent["VALOR_MUJER"] = (df_ent["VALOR_MUJER"] - df_ent["_sub_muj"]).clip(lower=0.0)
    df_ent["VALOR_HOMBRE"] = (df_ent["VALOR_HOMBRE"] - df_ent["_sub_hom"]).clip(lower=0.0)
    df_ent = df_ent.drop(columns=["_row_rank", "_sub_val", "_sub_muj", "_sub_hom"])

    # Limpieza de sectores en minúscula
    df_ent["SECTOR"] = df_ent["SECTOR"].replace(SECTOR_FIX)

    # Limpieza de alias DIVIPOLA adicionales
    for (dp_k, mp_k), (divi_n, mpio_n, lat_n, lon_n) in DIVI_EXTRA_FIX.items():
        m_fix = (df_ent["DEPARTAMENTO"] == dp_k) & (df_ent["MUNICIPIO"] == mp_k) & (df_ent["CODIGO_DIVIPOLA"].astype(str).str.endswith("000"))
        if m_fix.any():
            df_ent.loc[m_fix, "CODIGO_DIVIPOLA"] = divi_n
            df_ent.loc[m_fix, "MUNICIPIO"] = mpio_n
            df_ent.loc[m_fix, "LATITUD"] = lat_n
            df_ent.loc[m_fix, "LONGITUD"] = lon_n

    df_ent.to_parquet(DATA_DIR / "ops_base_entidades.parquet", index=False, compression="snappy")

    # 3. Actualizar ops_mensual.parquet
    df_mes = pd.read_parquet(DATA_DIR / "ops_mensual.parquet")
    if "VALOR_NOMINAL" not in df_mes.columns:
        df_mes["VALOR_NOMINAL"] = df_mes["VALOR_TOTAL"]
    else:
        df_mes["VALOR_TOTAL"] = df_mes["VALOR_NOMINAL"]

    # Mapear Departamento estándar en df_out
    from exportar_gobiernos_xlsx import normalizar_dpto
    dpto_out = df_out["Departamento_final"].fillna("").map(normalizar_dpto).map(
        lambda d: DPTO_STD_MAP.get(str(d).upper().strip(), ("No Determinado", "00"))[0]
    )
    df_out["DEPARTAMENTO"] = dpto_out

    mes_key = ["ANIO", "MES", "ANIO_MES", "GOBIERNO", "ORDEN_CPS", "FUENTE", "TIPO_PROVEEDOR_FINAL"]
    out_mes_agg = df_out.groupby(mes_key, observed=True)["_val_num"].sum().reset_index(name="_sub_val")

    df_mes = df_mes.sort_values("VALOR_NOMINAL", ascending=False).reset_index(drop=True)
    df_mes["_row_rank"] = df_mes.groupby(mes_key, observed=True).cumcount()
    out_mes_agg["_row_rank"] = 0

    df_mes = df_mes.merge(out_mes_agg, on=mes_key + ["_row_rank"], how="left")
    df_mes["VALOR_TOTAL"] = (df_mes["VALOR_NOMINAL"] - df_mes["_sub_val"].fillna(0.0)).clip(lower=0.0)
    df_mes = df_mes.drop(columns=["_row_rank", "_sub_val"])
    df_mes.to_parquet(DATA_DIR / "ops_mensual.parquet", index=False, compression="snappy")

    # 4. Limpiar perfiles distorsionados en ops_top_contratistas.parquet
    df_top = pd.read_parquet(DATA_DIR / "ops_top_contratistas.parquet")
    if not df_top.empty:
        out_prov_sub = (
            df_out.groupby(["Identificacion Proveedor", "TIPO_PROVEEDOR_FINAL"], observed=True)["_val_num"]
            .sum()
            .reset_index(name="_sub_val")
            .rename(columns={"Identificacion Proveedor": "IDENTIFICACION"})
        )
        out_prov_sub["IDENTIFICACION"] = out_prov_sub["IDENTIFICACION"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
        df_top["IDENTIFICACION"] = df_top["IDENTIFICACION"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
        df_top = df_top.merge(out_prov_sub, on=["IDENTIFICACION", "TIPO_PROVEEDOR_FINAL"], how="left")
        df_top["VALOR_TOTAL"] = (df_top["VALOR_TOTAL"] - df_top["_sub_val"].fillna(0.0)).clip(lower=0.0)
        df_top["VALOR_PROMEDIO"] = df_top["VALOR_TOTAL"] / df_top["N_CONTRATOS"].clip(lower=1)
        df_top = df_top.drop(columns=["_sub_val"])
        df_top.to_parquet(DATA_DIR / "ops_top_contratistas.parquet", index=False, compression="snappy")

    # 5. Actualizar ops_meta.json
    meta_path = DATA_DIR / "ops_meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    val_real_total = float(df_ent["VALOR_TOTAL"].sum())
    val_nom_total = float(df_ent["VALOR_NOMINAL"].sum())
    val_real_ord = df_ent.groupby("ORDEN_CPS")["VALOR_TOTAL"].sum().to_dict()

    meta["valor_total_cop"] = val_real_total
    meta["valor_nominal_cop"] = val_nom_total
    meta["n_contratos_outlier_digitacion"] = int(len(df_out))
    meta["valor_outliers_digitacion_cop"] = float(val_nom_total - val_real_total)
    meta["valor_por_orden"] = {k: float(v) for k, v in val_real_ord.items()}
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # Reporte de verificación
    m_divi = ~df_ent["CODIGO_DIVIPOLA"].astype(str).str.endswith("000")
    pct_divi = df_ent.loc[m_divi, "N_CONTRATOS"].sum() / df_ent["N_CONTRATOS"].sum() * 100.0
    print("\n" + "=" * 72)
    print("VERIFICACIÓN POST-PARCHE (CUANTÍA REAL DEPURADA)")
    print("=" * 72)
    print(f"Total Contratos (intacto):   {int(df_ent['N_CONTRATOS'].sum()):,}")
    print(f"Cuantía Real Depurada:       ${val_real_total/1e12:,.2f} Billones COP (Prom: ${val_real_total/df_ent['N_CONTRATOS'].sum()/1e6:,.2f} M/contrato)")
    print(f"Cuantía Nominal Bruta SECOP: ${val_nom_total/1e12:,.2f} Billones COP")
    print(f"Atípicos digitación aislados:{len(df_out):,} contratos (${(val_nom_total - val_real_total)/1e12:,.2f} Billones)")
    print("Desglose Real por ORDEN_CPS:")
    for o in ["NACIONAL", "DEPARTAMENTAL", "MUNICIPAL"]:
        sub_o = df_ent[df_ent["ORDEN_CPS"] == o]
        nc = int(sub_o["N_CONTRATOS"].sum())
        vr = float(sub_o["VALOR_TOTAL"].sum())
        ne = int(sub_o["CODIGO_ENTIDAD"].nunique())
        print(f"  - {o:<14}: {nc:>10,} contratos | ${vr/1e12:>6.2f} Billones | Prom: ${vr/max(nc,1)/1e6:>5.1f} M | {ne:,} entidades")
    print("\nCuantía Real por Vigencia:")
    vig_chk = df_ent.groupby("ANIO").agg(C=("N_CONTRATOS", "sum"), V=("VALOR_TOTAL", "sum"))
    for a, r in vig_chk.iterrows():
        print(f"  - {a}: {int(r['C']):>9,} contratos | ${r['V']/1e12:>6.2f} Billones | Prom: ${r['V']/r['C']/1e6:>5.1f} M")
    print(f"\nCobertura DIVIPOLA municipal: {pct_divi:.2f}%")
    print(f"Tiempo total del parche: {time.time() - t0:.1f}s")
    print("=" * 72)


if __name__ == "__main__":
    main()
