# 🏛️ Observatorio de Contratación – Prestación de Servicios (OPS 2018–2026)

![Colombia Compra Eficiente](assets/escudo.png)

Dashboard analítico interactivo en **Streamlit** para la **Agencia Nacional de Contratación Pública – Colombia Compra Eficiente (ANCP – CCE)** sobre la contratación de **Prestación de Servicios (OPS) con Personas Naturales** en SECOP I (`f789-7hwg`) y SECOP II (`jbjy-vk9h`), construido 100% desde **Datos Abiertos (`datos.gov.co`)** y conciliado con la herramienta oficial de visualización de CCE (*diferencia de +0,13% en contratos y +0,01% en valor al corte 01/09/2026*).

## ✨ Estructura del Dashboard

1. **Portada Ejecutiva (`app.py`):**
   - **Panel Ejecutivo Principal:** Número total y valor total de contratos de prestación de servicios con Personas Naturales (2018–2026, corte actualizado noviembre 2026), valor deflactado a precios constantes (PIB base 2015), desglose por carácter territorial (`NACIONAL`, `DEPARTAMENTAL`, `MUNICIPAL`) y conteo de entidades únicas.
   - Gráficos interactivos de participación territorial, evolución anual 2018–2026, distribución por enfoque de género (Mujeres vs. Hombres), transición SECOP I → SECOP II y mapa de calor geográfico.
2. **🏢 Entidades y Sectores (`pages/1_🏢_Entidades_y_Sectores.py`):** Buscador y ficha técnica por entidad, rankings Top N, sectores institucionales, tipologías del objeto contractual y directorio descargable.
3. **🗺️ Territorial (`pages/2_🗺️_Territorial.py`):** Mapas de calor coropléticos y de densidad para 33 departamentos y 1.100+ municipios DANE DIVIPOLA con auto-zoom, tríptico por carácter territorial, matriz 2D y rankings.
4. **📅 Evolución y Gobiernos (`pages/3_📅_Evolucion_y_Gobiernos.py`):** Comparativo por periodo presidencial (Santos II cierre 2018, Duque 2018–2022, Petro 2022–2026 y cierre post 7-Ago-2026), serie mensual con bandas de Ley de Garantías y matriz de estacionalidad.
5. **👥 Proveedores y Recurrencia (`pages/4_👥_Proveedores_y_Recurrencia.py`):** Radiografía de Personas Naturales únicas, enfoque de género, tipología de objeto, Top contratistas, multiplicidad anual ("Carrusel OPS") y continuidad interanual en la misma entidad.
6. **📥 Bases y Descargas (`pages/5_📥_Bases_y_Descargas.py`):** Ficha metodológica oficial (Datos Abiertos + Ficha Técnica + Conciliación CCE), reporte Word ilustrado, Excel multioja Nacional/Departamental/Municipal y exportación CSV (UTF-8 con BOM).

## 🚀 Cómo ejecutarlo localmente

Desde la carpeta raíz del proyecto:
```powershell
& "C:\ProgramData\anaconda3\Scripts\streamlit.exe" run dashboard_ops\app.py
```
O haciendo doble clic en `iniciar_dashboard_ops.bat`.

Si necesitas regenerar las bases `.parquet` tras actualizar los CSV de Datos Abiertos:
```powershell
& "C:\ProgramData\anaconda3\python.exe" dashboard_ops\build_dashboard_data_datos_abiertos.py
```
