"""
Estilos CSS institucionales compartidos – Colombia Compra Eficiente (ANCP - CCE).
Combina la identidad visual oficial del Dashboard EMAE con la arquitectura
de tarjetas solicitada en el bosquejo ejecutivo de Prestación de Servicios (OPS).
"""

import streamlit as st


INSTITUTIONAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Sidebar institucional CCE ──────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #174073 0%, #2B4C70 55%, #3E546C 100%);
}
[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label,
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stSlider label {
    color: #FFC000 !important;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
/* Arreglar contraste dentro de los inputs desplegables del sidebar en tema claro */
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: rgba(15, 34, 62, 0.75) !important;
    border: 1px solid rgba(255, 255, 255, 0.25) !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] [data-baseweb="tag"] {
    background-color: #D61C38 !important;
    color: #FFFFFF !important;
}
[data-testid="stSidebar"] input {
    color: #FFFFFF !important;
}

/* ── Header institucional principal (idéntico al Dashboard EMAE) ────────── */
.main-header {
    background: linear-gradient(135deg, #174073 0%, #533965 60%, #6A2444 100%);
    border-radius: 18px;
    padding: 1.65rem 2.2rem;
    color: #FFFFFF;
    margin-bottom: 1.35rem;
    box-shadow: 0 6px 28px rgba(23, 64, 115, 0.22);
    position: relative;
    overflow: hidden;
}
.color-strip {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 8px;
    background: linear-gradient(to right,
        #FFC000 0% 10%,
        #D98A3C 10% 20%,
        #9C7238 20% 30%,
        #5A666A 30% 40%,
        #3E546C 40% 50%,
        #174073 50% 60%,
        #533965 60% 70%,
        #6A2444 70% 80%,
        #9E2044 80% 90%,
        #D61C38 90% 100%
    );
}
.main-header h1 {
    font-size: 1.62rem;
    font-weight: 800;
    margin: 0;
    line-height: 1.2;
    padding-top: 0.35rem;
    color: #FFFFFF !important;
}
.main-header p {
    font-size: 0.90rem;
    opacity: 0.92;
    margin: 0.45rem 0 0 0;
    color: #F0F4F8 !important;
}
.main-header .tag {
    background: rgba(255, 255, 255, 0.18);
    border: 1px solid rgba(255, 255, 255, 0.22);
    border-radius: 20px;
    padding: 0.22rem 0.85rem;
    font-size: 0.74rem;
    font-weight: 600;
    display: inline-block;
    margin-top: 0.65rem;
    margin-right: 0.4rem;
    color: #FFFFFF !important;
}

/* ── Encabezados de sección ─────────────────────────────────────────────── */
.section-header {
    font-size: 1.12rem;
    font-weight: 700;
    color: #174073;
    border-bottom: 3px solid #D61C38;
    padding-bottom: 0.4rem;
    margin: 1.5rem 0 1rem 0;
}

/* ── BLOQUE BOSQUEJO EJECUTIVO (PORTADA PRINCIPAL OPS) ──────────────────── */
.ops-hero-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.8rem;
}
.ops-pill-header {
    background: linear-gradient(135deg, #135472 0%, #174073 100%);
    color: #FFFFFF;
    font-weight: 700;
    font-size: 0.98rem;
    text-align: center;
    padding: 0.78rem 1.4rem;
    border-radius: 12px;
    width: 100%;
    box-shadow: 0 4px 14px rgba(19, 84, 114, 0.22);
    border: 1px solid #0E3B52;
    line-height: 1.25;
}
.ops-value-box {
    background: #FFFFFF;
    border: 2.5px solid #4CAF50;
    border-radius: 12px;
    padding: 0.75rem 1.2rem;
    width: 92%;
    text-align: center;
    box-shadow: 0 4px 16px rgba(46, 139, 87, 0.10);
    transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.ops-value-box:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 22px rgba(46, 139, 87, 0.18);
}
.ops-value-main {
    font-size: 1.85rem;
    font-weight: 800;
    color: #112A46;
    line-height: 1.15;
    letter-spacing: -0.02em;
}
.ops-value-sub {
    font-size: 0.76rem;
    color: #5A666A;
    margin-top: 0.22rem;
    font-weight: 500;
}

/* Banner de carácter territorial */
.ops-territorial-banner {
    background: linear-gradient(90deg, #125270 0%, #174073 50%, #125270 100%);
    color: #FFFFFF;
    font-size: 1.08rem;
    font-weight: 700;
    text-align: center;
    padding: 0.75rem 1.5rem;
    border-radius: 12px;
    margin: 0.9rem 0 1.05rem 0;
    box-shadow: 0 4px 16px rgba(23, 64, 115, 0.20);
    border: 1px solid #0D3A50;
    letter-spacing: 0.02em;
}

/* Tarjeta columna territorial (NACIONAL / DEPARTAMENTAL / MUNICIPAL) */
.ops-col-panel {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 1.05rem 1.0rem 1.15rem 1.0rem;
    box-shadow: 0 4px 20px rgba(23, 64, 115, 0.08);
    border-top: 4px solid #174073;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.55rem;
    height: 100%;
}
.ops-col-panel.nacional      { border-top-color: #174073; }
.ops-col-panel.departamental { border-top-color: #533965; }
.ops-col-panel.municipal     { border-top-color: #1E8449; }

.ops-level-pill {
    background: linear-gradient(135deg, #145B7A 0%, #174073 100%);
    color: #FFFFFF;
    font-size: 0.98rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    padding: 0.52rem 1.35rem;
    border-radius: 10px;
    text-align: center;
    width: 82%;
    border: 1px solid #0E3B52;
    box-shadow: 0 3px 10px rgba(20, 91, 122, 0.22);
}
.ops-sub-pill {
    background: #145B7A;
    color: #FFFFFF;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    padding: 0.42rem 0.95rem;
    border-radius: 9px;
    text-align: center;
    width: 68%;
    margin-top: 0.35rem;
    line-height: 1.2;
}
.ops-sub-val {
    background: #FFFFFF;
    border: 2.2px solid #4CAF50;
    border-radius: 10px;
    padding: 0.55rem 0.75rem;
    width: 94%;
    text-align: center;
    box-shadow: 0 2px 10px rgba(76, 175, 80, 0.09);
}
.ops-sub-val .num {
    font-size: 1.38rem;
    font-weight: 800;
    color: #112A46;
    line-height: 1.15;
}
.ops-sub-val .sub {
    font-size: 0.72rem;
    color: #5A666A;
    margin-top: 0.16rem;
    font-weight: 500;
}

/* Fila TOTAL ENTIDADES (horizontal igual al bosquejo, alineada al píxel) */
.ops-ent-total-row {
    display: grid;
    grid-template-columns: 1fr 2.05fr;
    gap: 1.1rem;
    align-items: stretch;
    margin: 0.95rem 0 0.85rem 0;
}
@media (max-width: 768px) {
    .ops-ent-total-row {
        grid-template-columns: 1fr;
    }
}
.ops-ent-total-label {
    background: linear-gradient(135deg, #145B7A 0%, #174073 100%);
    color: #FFFFFF;
    font-size: 0.96rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    padding: 0.95rem 1.2rem;
    border-radius: 12px;
    text-align: center;
    border: 1px solid #0E3B52;
    box-shadow: 0 4px 12px rgba(20, 91, 122, 0.20);
    min-height: 78px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.ops-ent-total-box {
    background: #FFFFFF;
    border: 2.5px solid #4CAF50;
    border-radius: 12px;
    padding: 0.65rem 1.2rem;
    text-align: center;
    box-shadow: 0 4px 14px rgba(76, 175, 80, 0.10);
    min-height: 78px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}
.ops-ent-total-box .num {
    font-size: 1.75rem;
    font-weight: 800;
    color: #112A46;
    line-height: 1.1;
}
.ops-ent-total-box .sub {
    font-size: 0.76rem;
    color: #5A666A;
    margin-top: 0.2rem;
}

/* Tarjetas ENTIDADES NACIONALES / DEPARTAMENTALES / MUNICIPALES */
.ops-ent-card-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.4rem;
}
.ops-ent-pill {
    background: linear-gradient(135deg, #145B7A 0%, #174073 100%);
    color: #FFFFFF;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    padding: 0.55rem 1rem;
    border-radius: 10px;
    text-align: center;
    width: 88%;
    border: 1px solid #0E3B52;
    box-shadow: 0 3px 10px rgba(20, 91, 122, 0.18);
}

/* ── KPI Cards estándar EMAE para páginas secundarias ───────────────────── */
.kpi-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 1.1rem 1.3rem;
    border-left: 5px solid #174073;
    box-shadow: 0 4px 18px rgba(23, 64, 115, 0.08);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    height: 100%;
}
.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(23, 64, 115, 0.14);
}
.kpi-card.verde   { border-left-color: #1E8449; }
.kpi-card.rojo    { border-left-color: #D61C38; }
.kpi-card.naranja { border-left-color: #D98A3C; }
.kpi-card.morado  { border-left-color: #533965; }
.kpi-card.gris    { border-left-color: #3E546C; }

.kpi-label {
    font-size: 0.72rem;
    font-weight: 700;
    color: #5A666A;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.25rem;
}
.kpi-value {
    font-size: 1.65rem;
    font-weight: 800;
    color: #174073;
    line-height: 1.15;
}
.kpi-sub {
    font-size: 0.74rem;
    color: #5A666A;
    margin-top: 0.28rem;
}

/* Cajas informativas y tarjetas de entidad */
.info-box {
    background: #EBF3FA;
    border-left: 4px solid #174073;
    border-radius: 8px;
    padding: 0.85rem 1.1rem;
    font-size: 0.84rem;
    color: #174073;
    margin-bottom: 1rem;
}
.note-box {
    background: #FEF9E7;
    border-left: 4px solid #D98A3C;
    border-radius: 8px;
    padding: 0.8rem 1.15rem;
    font-size: 0.82rem;
    color: #3E546C;
    margin-top: 0.85rem;
}
.entity-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 1.3rem 1.6rem;
    box-shadow: 0 4px 18px rgba(23, 64, 115, 0.10);
    border-top: 5px solid #174073;
    margin-bottom: 0.8rem;
}
.entity-card h3 {
    color: #174073;
    font-size: 1.1rem;
    margin: 0 0 0.55rem 0;
}
.entity-row {
    display: flex;
    gap: 0.65rem;
    flex-wrap: wrap;
    margin-top: 0.55rem;
}
.entity-stat {
    background: #F0F6FF;
    border-radius: 8px;
    padding: 0.4rem 0.8rem;
    font-size: 0.80rem;
    color: #174073;
    font-weight: 600;
}
.badge {
    display: inline-block;
    padding: 0.22rem 0.75rem;
    border-radius: 999px;
    font-size: 0.73rem;
    font-weight: 600;
    color: #FFFFFF;
    margin: 0.12rem;
}
.banner-download {
    background: linear-gradient(135deg, #174073 0%, #275A96 100%);
    color: #FFFFFF;
    border-radius: 14px;
    padding: 1.35rem 1.7rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 18px rgba(23, 64, 115, 0.16);
}
.banner-download h2 { color: #FFFFFF !important; margin: 0 0 0.35rem 0; font-size: 1.28rem; }
.banner-download p  { color: #E3E8EE !important; margin: 0; font-size: 0.88rem; line-height: 1.45; }
</style>
"""


def inject_css():
    st.markdown(INSTITUTIONAL_CSS, unsafe_allow_html=True)
