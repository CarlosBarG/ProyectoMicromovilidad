
# ============================================================
# EDA DE SINIESTROS VIALES DE MICROMOVILIDAD - BOGOTÁ
# Periodo: 2018-2026
#
# Archivos:
#   ACCIDENTE.csv
#   VM_ACC_VEHICULO.csv
#
# Categorías de micromovilidad solicitadas:
#   BICICLETA, MOTOCICLO, MOTOTRICICLO
#
# IMPORTANTE:
# - FORMULARIO es la llave entre las dos tablas.
# - Un accidente puede tener varios vehículos.
# - Por eso NO se hace un merge directo para contar accidentes.
# - Primero se filtran los vehículos y después se obtienen
#   FORMULARIO únicos para trabajar a nivel de accidente.
# ============================================================

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")

# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

RUTA_ACCIDENTE = "ACCIDENTE.csv"
RUTA_VEHICULO = "VM_ACC_VEHICULO.csv"

CARPETA_SALIDA = "EDA_MICROMOVILIDAD_2018_2026"
os.makedirs(CARPETA_SALIDA, exist_ok=True)

ANIO_INICIO = 2018
ANIO_FIN = 2026

CATEGORIAS_MICROMOVILIDAD = [
    "BICICLETA",
    "MOTOCICLO",
    "MOTOTRICICLO"
]

# Columnas que realmente se utilizarán
COLUMNAS_ACCIDENTE = [
    "FORMULARIO",
    "FECHA_HORA_ACC",
    "ANO_OCURRENCIA_ACC",
    "HORA_OCURRENCIA_ACC",
    "MES_OCURRENCIA_ACC",
    "DIA_OCURRENCIA_ACC",
    "DIRECCION",
    "GRAVEDAD",
    "CLASE_ACC",
    "LOCALIDAD",
    "MUNICIPIO",
    "LATITUD",
    "LONGITUD",
    "PK_CALZADA",
    "BARRIO",
    "MVINOMBRE",
    "DISTANCIA_VIA"
]

COLUMNAS_VEHICULO = [
    "FORMULARIO",
    "CLASE",
    "SERVICIO",
    "MODALIDAD",
    "ENFUGA"
]

# ============================================================
# 2. FUNCIONES AUXILIARES
# ============================================================

def limpiar_texto(df, columnas):
    """Elimina espacios y normaliza cadenas."""
    for col in columnas:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()
            df[col] = df[col].replace({
                "": pd.NA,
                "nan": pd.NA,
                "None": pd.NA,
                "NULL": pd.NA,
                "null": pd.NA
            })
    return df


def guardar_tabla(df, nombre):
    ruta = os.path.join(CARPETA_SALIDA, nombre)
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    print(f"Guardado: {ruta}")


def guardar_grafico(nombre):
    ruta = os.path.join(CARPETA_SALIDA, nombre)
    plt.tight_layout()
    plt.savefig(ruta, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Gráfico: {ruta}")


def porcentaje(n, total):
    return round((n / total) * 100, 2) if total else 0


# ============================================================
# 3. CARGA DE DATOS
# ============================================================

print("\n" + "=" * 70)
print("CARGANDO DATOS")
print("=" * 70)

accidente = pd.read_csv(
    RUTA_ACCIDENTE,
    usecols=COLUMNAS_ACCIDENTE,
    low_memory=False
)

vehiculo = pd.read_csv(
    RUTA_VEHICULO,
    usecols=COLUMNAS_VEHICULO,
    low_memory=False
)

print(f"Accidentes cargados: {len(accidente):,}")
print(f"Vehículos cargados:  {len(vehiculo):,}")


# ============================================================
# 4. LIMPIEZA BÁSICA
# ============================================================

print("\n" + "=" * 70)
print("LIMPIEZA BÁSICA")
print("=" * 70)

columnas_texto_acc = [
    "FORMULARIO", "HORA_OCURRENCIA_ACC", "MES_OCURRENCIA_ACC",
    "DIA_OCURRENCIA_ACC", "DIRECCION", "GRAVEDAD", "CLASE_ACC",
    "LOCALIDAD", "MUNICIPIO", "BARRIO", "MVINOMBRE"
]

columnas_texto_veh = [
    "FORMULARIO", "CLASE", "SERVICIO", "MODALIDAD", "ENFUGA"
]

accidente = limpiar_texto(accidente, columnas_texto_acc)
vehiculo = limpiar_texto(vehiculo, columnas_texto_veh)

# Convertir año a numérico
accidente["ANO_OCURRENCIA_ACC"] = pd.to_numeric(
    accidente["ANO_OCURRENCIA_ACC"],
    errors="coerce"
)

# Convertir coordenadas
accidente["LATITUD"] = pd.to_numeric(accidente["LATITUD"], errors="coerce")
accidente["LONGITUD"] = pd.to_numeric(accidente["LONGITUD"], errors="coerce")

# Variables numéricas
for col in ["PK_CALZADA", "DISTANCIA_VIA"]:
    accidente[col] = pd.to_numeric(accidente[col], errors="coerce")

# Fecha/hora
accidente["FECHA_HORA_ACC"] = pd.to_datetime(
    accidente["FECHA_HORA_ACC"],
    errors="coerce"
)

# ============================================================
# 5. FILTRO TEMPORAL 2018-2026
# ============================================================

accidente = accidente[
    accidente["ANO_OCURRENCIA_ACC"].between(ANIO_INICIO, ANIO_FIN)
].copy()

print(f"Accidentes después del filtro {ANIO_INICIO}-{ANIO_FIN}: "
      f"{len(accidente):,}")

# ============================================================
# 6. REVISIÓN DE DUPLICADOS EN ACCIDENTES
# ============================================================

print("\n" + "=" * 70)
print("DUPLICADOS")
print("=" * 70)

duplicados_formulario = accidente["FORMULARIO"].duplicated().sum()

print(f"FORMULARIO duplicados: {duplicados_formulario:,}")

# La tabla ACCIDENTE debe ser una fila por accidente.
# Conservamos la primera aparición si existieran duplicados exactos
# de FORMULARIO.
if duplicados_formulario > 0:
    accidente = accidente.drop_duplicates(
        subset="FORMULARIO",
        keep="first"
    ).copy()

print(f"Accidentes únicos: {len(accidente):,}")


# ============================================================
# 7. FILTRAR VEHÍCULOS DE MICROMOVILIDAD
# ============================================================

vehiculo_micro = vehiculo[
    vehiculo["CLASE"].isin(CATEGORIAS_MICROMOVILIDAD)
].copy()

print("\n" + "=" * 70)
print("MICROMOVILIDAD")
print("=" * 70)

print(
    vehiculo_micro["CLASE"]
    .value_counts(dropna=False)
    .to_string()
)

# ============================================================
# 8. RELACIONAR VEHÍCULOS CON ACCIDENTES
# ============================================================

# Solo usamos FORMULARIO para relacionar ambas tablas.
# Primero obtenemos el año de cada accidente.
mapa_accidente = accidente[
    ["FORMULARIO", "ANO_OCURRENCIA_ACC"]
].drop_duplicates("FORMULARIO")

vehiculo_micro = vehiculo_micro.merge(
    mapa_accidente,
    on="FORMULARIO",
    how="inner"
)

print(f"\nRegistros de vehículos micromovilidad 2018-2026: "
      f"{len(vehiculo_micro):,}")

# ============================================================
# 9. ACCIDENTES ÚNICOS DE MICROMOVILIDAD
# ============================================================

formularios_micro = vehiculo_micro[
    "FORMULARIO"
].dropna().drop_duplicates()

acc_micro = accidente[
    accidente["FORMULARIO"].isin(formularios_micro)
].copy()

print(f"Accidentes únicos de micromovilidad: {len(acc_micro):,}")

# ============================================================
# 10. TIPO DE MICROMOVILIDAD POR ACCIDENTE
# ============================================================

# Un accidente puede involucrar más de un tipo.
# Para evitar duplicar accidentes en análisis generales,
# se construye una etiqueta:
#
#   BICICLETA
#   MOTOCICLO
#   MOTOTRICICLO
#   MULTIPLE

tipos_por_accidente = (
    vehiculo_micro
    .groupby("FORMULARIO")["CLASE"]
    .agg(lambda x: sorted(set(x.dropna())))
    .reset_index()
)

tipos_por_accidente["TIPO_MICROMOVILIDAD"] = (
    tipos_por_accidente["CLASE"]
    .apply(lambda x: x[0] if len(x) == 1 else "MULTIPLE")
)

acc_micro = acc_micro.merge(
    tipos_por_accidente[
        ["FORMULARIO", "TIPO_MICROMOVILIDAD"]
    ],
    on="FORMULARIO",
    how="left"
)

# ============================================================
# 11. TABLA DE TIPOS POR ACCIDENTE
# ============================================================

tabla_tipo = (
    acc_micro["TIPO_MICROMOVILIDAD"]
    .value_counts()
    .rename_axis("TIPO_MICROMOVILIDAD")
    .reset_index(name="ACCIDENTES")
)

tabla_tipo["PORCENTAJE"] = (
    tabla_tipo["ACCIDENTES"] /
    tabla_tipo["ACCIDENTES"].sum() * 100
).round(2)

guardar_tabla(tabla_tipo, "01_accidentes_por_tipo.csv")

# ============================================================
# 12. NULOS - ACCIDENTES GENERALES 2018-2026
# ============================================================

print("\n" + "=" * 70)
print("DATOS NULOS - ACCIDENTES")
print("=" * 70)

nulos_acc = pd.DataFrame({
    "VARIABLE": accidente.columns,
    "NULOS": accidente.isna().sum().values
})

nulos_acc["PORCENTAJE_NULOS"] = (
    nulos_acc["NULOS"] / len(accidente) * 100
).round(3)

nulos_acc = nulos_acc.sort_values(
    "PORCENTAJE_NULOS",
    ascending=False
)

print(nulos_acc.to_string(index=False))

guardar_tabla(nulos_acc, "02_nulos_accidentes.csv")

# ============================================================
# 13. NULOS - ACCIDENTES DE MICROMOVILIDAD
# ============================================================

print("\n" + "=" * 70)
print("DATOS NULOS - MICROMOVILIDAD")
print("=" * 70)

nulos_micro = pd.DataFrame({
    "VARIABLE": acc_micro.columns,
    "NULOS": acc_micro.isna().sum().values
})

nulos_micro["PORCENTAJE_NULOS"] = (
    nulos_micro["NULOS"] / len(acc_micro) * 100
).round(3)

nulos_micro = nulos_micro.sort_values(
    "PORCENTAJE_NULOS",
    ascending=False
)

print(nulos_micro.to_string(index=False))

guardar_tabla(nulos_micro, "03_nulos_accidentes_micromovilidad.csv")

# ============================================================
# 14. NULOS - VEHÍCULOS DE MICROMOVILIDAD
# ============================================================

nulos_veh = pd.DataFrame({
    "VARIABLE": vehiculo_micro.columns,
    "NULOS": vehiculo_micro.isna().sum().values
})

nulos_veh["PORCENTAJE_NULOS"] = (
    nulos_veh["NULOS"] / len(vehiculo_micro) * 100
).round(3)

nulos_veh = nulos_veh.sort_values(
    "PORCENTAJE_NULOS",
    ascending=False
)

print("\n" + "=" * 70)
print("DATOS NULOS - VEHÍCULOS")
print("=" * 70)

print(nulos_veh.to_string(index=False))

guardar_tabla(nulos_veh, "04_nulos_vehiculos_micromovilidad.csv")


# ============================================================
# 15. ACCIDENTES POR AÑO
# ============================================================

por_anio = (
    acc_micro
    .groupby("ANO_OCURRENCIA_ACC")
    .size()
    .reset_index(name="ACCIDENTES")
)

por_anio["PORCENTAJE"] = (
    por_anio["ACCIDENTES"] /
    por_anio["ACCIDENTES"].sum() * 100
).round(2)

guardar_tabla(por_anio, "05_accidentes_por_anio.csv")

plt.figure(figsize=(11, 6))
sns.lineplot(
    data=por_anio,
    x="ANO_OCURRENCIA_ACC",
    y="ACCIDENTES",
    marker="o"
)
plt.title("Accidentes de micromovilidad por año (2018-2026)")
plt.xlabel("Año")
plt.ylabel("Número de accidentes")
plt.xticks(por_anio["ANO_OCURRENCIA_ACC"])
guardar_grafico("01_accidentes_por_anio.png")


# ============================================================
# 16. AÑO x TIPO DE MICROMOVILIDAD
# ============================================================

anio_tipo = pd.crosstab(
    acc_micro["ANO_OCURRENCIA_ACC"],
    acc_micro["TIPO_MICROMOVILIDAD"]
).reset_index()

guardar_tabla(anio_tipo, "06_anio_tipo_micromovilidad.csv")

plt.figure(figsize=(12, 6))

for tipo in [
    "BICICLETA",
    "MOTOCICLO",
    "MOTOTRICICLO",
    "MULTIPLE"
]:
    if tipo in anio_tipo.columns:
        plt.plot(
            anio_tipo["ANO_OCURRENCIA_ACC"],
            anio_tipo[tipo],
            marker="o",
            label=tipo
        )

plt.title("Accidentes por año y tipo de micromovilidad")
plt.xlabel("Año")
plt.ylabel("Accidentes")
plt.legend()
guardar_grafico("02_anio_tipo_micromovilidad.png")


# ============================================================
# 17. HORA
# ============================================================

def extraer_hora(valor):
    if pd.isna(valor):
        return np.nan

    texto = str(valor).strip()

    # Intenta primero formatos de hora
    try:
        return pd.to_datetime(
            texto,
            errors="coerce"
        ).hour
    except:
        return np.nan


acc_micro["HORA_NUM"] = (
    acc_micro["HORA_OCURRENCIA_ACC"]
    .apply(extraer_hora)
)

# Si la columna anterior no pudo convertirse, intentar desde fecha-hora
faltantes_hora = acc_micro["HORA_NUM"].isna()

acc_micro.loc[faltantes_hora, "HORA_NUM"] = (
    acc_micro.loc[faltantes_hora, "FECHA_HORA_ACC"]
    .dt.hour
)

acc_micro["HORA_NUM"] = pd.to_numeric(
    acc_micro["HORA_NUM"],
    errors="coerce"
)

por_hora = (
    acc_micro
    .dropna(subset=["HORA_NUM"])
    .groupby("HORA_NUM")
    .size()
    .reindex(range(24), fill_value=0)
    .reset_index(name="ACCIDENTES")
)

por_hora["PORCENTAJE"] = (
    por_hora["ACCIDENTES"] /
    por_hora["ACCIDENTES"].sum() * 100
).round(2)

guardar_tabla(por_hora, "07_accidentes_por_hora.csv")

plt.figure(figsize=(13, 6))
sns.barplot(
    data=por_hora,
    x="HORA_NUM",
    y="ACCIDENTES"
)
plt.title("Accidentes de micromovilidad por hora")
plt.xlabel("Hora del día")
plt.ylabel("Número de accidentes")
guardar_grafico("03_accidentes_por_hora.png")


# ============================================================
# 18. DÍA DE LA SEMANA
# ============================================================

# Se utiliza la fecha real cuando está disponible.
acc_micro["DIA_SEMANA"] = (
    acc_micro["FECHA_HORA_ACC"].dt.day_name()
)

# Traducción al español
mapa_dias = {
    "Monday": "Lunes",
    "Tuesday": "Martes",
    "Wednesday": "Miércoles",
    "Thursday": "Jueves",
    "Friday": "Viernes",
    "Saturday": "Sábado",
    "Sunday": "Domingo"
}

acc_micro["DIA_SEMANA"] = (
    acc_micro["DIA_SEMANA"].map(mapa_dias)
)

orden_dias = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo"
]

por_dia = (
    acc_micro["DIA_SEMANA"]
    .value_counts()
    .reindex(orden_dias, fill_value=0)
    .rename_axis("DIA_SEMANA")
    .reset_index(name="ACCIDENTES")
)

por_dia["PORCENTAJE"] = (
    por_dia["ACCIDENTES"] /
    por_dia["ACCIDENTES"].sum() * 100
).round(2)

guardar_tabla(por_dia, "08_accidentes_por_dia_semana.csv")

plt.figure(figsize=(11, 6))
sns.barplot(
    data=por_dia,
    x="DIA_SEMANA",
    y="ACCIDENTES",
    order=orden_dias
)
plt.title("Accidentes de micromovilidad por día de la semana")
plt.xlabel("Día")
plt.ylabel("Número de accidentes")
plt.xticks(rotation=20)
guardar_grafico("04_accidentes_por_dia_semana.png")


# ============================================================
# 19. HORA x DÍA
# ============================================================

hora_dia = pd.crosstab(
    acc_micro["DIA_SEMANA"],
    acc_micro["HORA_NUM"]
).reindex(orden_dias)

hora_dia = hora_dia.reindex(columns=range(24), fill_value=0)

guardar_tabla(
    hora_dia.reset_index(),
    "09_hora_dia.csv"
)

plt.figure(figsize=(15, 6))
sns.heatmap(
    hora_dia,
    annot=True,
    fmt="g"
)
plt.title("Accidentes de micromovilidad: día vs hora")
plt.xlabel("Hora")
plt.ylabel("Día")
guardar_grafico("05_heatmap_dia_hora.png")


# ============================================================
# 20. LOCALIDADES
# ============================================================

por_localidad = (
    acc_micro["LOCALIDAD"]
    .fillna("SIN DATO")
    .value_counts()
    .rename_axis("LOCALIDAD")
    .reset_index(name="ACCIDENTES")
)

por_localidad["PORCENTAJE"] = (
    por_localidad["ACCIDENTES"] /
    por_localidad["ACCIDENTES"].sum() * 100
).round(2)

guardar_tabla(
    por_localidad,
    "10_accidentes_por_localidad.csv"
)

top_localidades = por_localidad.head(15).sort_values(
    "ACCIDENTES"
)

plt.figure(figsize=(11, 7))
sns.barplot(
    data=top_localidades,
    x="ACCIDENTES",
    y="LOCALIDAD"
)
plt.title("Top 15 localidades con accidentes de micromovilidad")
plt.xlabel("Número de accidentes")
plt.ylabel("Localidad")
guardar_grafico("06_top_localidades.png")


# ============================================================
# 21. BARRIOS
# ============================================================

por_barrio = (
    acc_micro["BARRIO"]
    .dropna()
    .value_counts()
    .rename_axis("BARRIO")
    .reset_index(name="ACCIDENTES")
)

guardar_tabla(
    por_barrio,
    "11_accidentes_por_barrio.csv"
)

top_barrios = por_barrio.head(20).sort_values("ACCIDENTES")

plt.figure(figsize=(11, 8))
sns.barplot(
    data=top_barrios,
    x="ACCIDENTES",
    y="BARRIO"
)
plt.title("Top 20 barrios con accidentes de micromovilidad")
plt.xlabel("Número de accidentes")
plt.ylabel("Barrio")
guardar_grafico("07_top_barrios.png")


# ============================================================
# 22. VÍAS / MVINOMBRE
# ============================================================

# Se eliminan valores que NO representan nombres de vía.
mvi = acc_micro["MVINOMBRE"].copy()

mvi = mvi.dropna()
mvi = mvi[mvi.astype(str).str.strip() != ""]
mvi = mvi[
    ~mvi.astype(str).str.upper().isin([
        "SIN_NMG",
        "SIN NMG",
        "SIN NOMBRE"
    ])
]

por_via = (
    mvi.value_counts()
    .rename_axis("MVINOMBRE")
    .reset_index(name="ACCIDENTES")
)

por_via["PORCENTAJE"] = (
    por_via["ACCIDENTES"] /
    por_via["ACCIDENTES"].sum() * 100
).round(2)

guardar_tabla(
    por_via,
    "12_accidentes_por_via.csv"
)

top_vias = por_via.head(20).sort_values("ACCIDENTES")

plt.figure(figsize=(12, 9))
sns.barplot(
    data=top_vias,
    x="ACCIDENTES",
    y="MVINOMBRE"
)
plt.title("Top 20 vías con accidentes de micromovilidad")
plt.xlabel("Número de accidentes")
plt.ylabel("Vía")
guardar_grafico("08_top_vias.png")


# ============================================================
# 23. PK_CALZADA
# ============================================================

por_calzada = (
    acc_micro["PK_CALZADA"]
    .dropna()
    .value_counts()
    .rename_axis("PK_CALZADA")
    .reset_index(name="ACCIDENTES")
)

guardar_tabla(
    por_calzada,
    "13_accidentes_por_pk_calzada.csv"
)

top_calzadas = por_calzada.head(20).sort_values(
    "ACCIDENTES"
)

plt.figure(figsize=(11, 8))
sns.barplot(
    data=top_calzadas,
    x="ACCIDENTES",
    y="PK_CALZADA"
)
plt.title("Top 20 calzadas/segmentos por número de accidentes")
plt.xlabel("Número de accidentes")
plt.ylabel("PK_CALZADA")
guardar_grafico("09_top_calzadas.png")


# ============================================================
# 24. CLASE DE ACCIDENTE
# ============================================================

por_clase_acc = (
    acc_micro["CLASE_ACC"]
    .fillna("SIN DATO")
    .value_counts()
    .rename_axis("CLASE_ACC")
    .reset_index(name="ACCIDENTES")
)

por_clase_acc["PORCENTAJE"] = (
    por_clase_acc["ACCIDENTES"] /
    por_clase_acc["ACCIDENTES"].sum() * 100
).round(2)

guardar_tabla(
    por_clase_acc,
    "14_tipo_accidente.csv"
)

plt.figure(figsize=(11, 6))
sns.barplot(
    data=por_clase_acc,
    x="ACCIDENTES",
    y="CLASE_ACC"
)
plt.title("Tipo de accidente de micromovilidad")
plt.xlabel("Número de accidentes")
plt.ylabel("Tipo de accidente")
guardar_grafico("10_tipo_accidente.png")


# ============================================================
# 25. GRAVEDAD
# ============================================================

por_gravedad = (
    acc_micro["GRAVEDAD"]
    .fillna("SIN DATO")
    .value_counts()
    .rename_axis("GRAVEDAD")
    .reset_index(name="ACCIDENTES")
)

por_gravedad["PORCENTAJE"] = (
    por_gravedad["ACCIDENTES"] /
    por_gravedad["ACCIDENTES"].sum() * 100
).round(2)

guardar_tabla(
    por_gravedad,
    "15_gravedad.csv"
)

plt.figure(figsize=(10, 6))
sns.barplot(
    data=por_gravedad,
    x="ACCIDENTES",
    y="GRAVEDAD"
)
plt.title("Gravedad de accidentes de micromovilidad")
plt.xlabel("Número de accidentes")
plt.ylabel("Gravedad")
guardar_grafico("11_gravedad.png")


# ============================================================
# 26. GRAVEDAD POR AÑO
# ============================================================

anio_gravedad = pd.crosstab(
    acc_micro["ANO_OCURRENCIA_ACC"],
    acc_micro["GRAVEDAD"]
).reset_index()

guardar_tabla(
    anio_gravedad,
    "16_anio_gravedad.csv"
)

# ============================================================
# 27. ANÁLISIS POR CADA VEHÍCULO
# ============================================================

print("\n" + "=" * 70)
print("ANÁLISIS INDIVIDUAL DE CADA VEHÍCULO")
print("=" * 70)

for tipo in CATEGORIAS_MICROMOVILIDAD:

    print("\n" + "-" * 70)
    print(tipo)
    print("-" * 70)

    # Accidentes únicos que involucran el tipo
    formularios_tipo = (
        vehiculo_micro.loc[
            vehiculo_micro["CLASE"] == tipo,
            "FORMULARIO"
        ]
        .dropna()
        .drop_duplicates()
    )

    datos_tipo = acc_micro[
        acc_micro["FORMULARIO"].isin(formularios_tipo)
    ].copy()

    print(f"Accidentes: {len(datos_tipo):,}")

    carpeta_tipo = os.path.join(
        CARPETA_SALIDA,
        tipo
    )
    os.makedirs(carpeta_tipo, exist_ok=True)

    # ---------- Año ----------
    tabla = (
        datos_tipo
        .groupby("ANO_OCURRENCIA_ACC")
        .size()
        .reset_index(name="ACCIDENTES")
    )

    tabla.to_csv(
        os.path.join(carpeta_tipo, "01_por_anio.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    # ---------- Hora ----------
    tabla = (
        datos_tipo
        .groupby("HORA_NUM")
        .size()
        .reindex(range(24), fill_value=0)
        .reset_index(name="ACCIDENTES")
    )

    tabla.to_csv(
        os.path.join(carpeta_tipo, "02_por_hora.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    # ---------- Día ----------
    tabla = (
        datos_tipo["DIA_SEMANA"]
        .value_counts()
        .reindex(orden_dias, fill_value=0)
        .rename_axis("DIA_SEMANA")
        .reset_index(name="ACCIDENTES")
    )

    tabla.to_csv(
        os.path.join(carpeta_tipo, "03_por_dia.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    # ---------- Localidad ----------
    tabla = (
        datos_tipo["LOCALIDAD"]
        .fillna("SIN DATO")
        .value_counts()
        .rename_axis("LOCALIDAD")
        .reset_index(name="ACCIDENTES")
    )

    tabla.to_csv(
        os.path.join(carpeta_tipo, "04_por_localidad.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    # ---------- Vía ----------
    tabla = (
        datos_tipo["MVINOMBRE"]
        .dropna()
        .value_counts()
        .rename_axis("MVINOMBRE")
        .reset_index(name="ACCIDENTES")
    )

    tabla = tabla[
        ~tabla["MVINOMBRE"].astype(str).str.upper().isin([
            "SIN_NMG",
            "SIN NMG",
            "SIN NOMBRE"
        ])
    ]

    tabla.to_csv(
        os.path.join(carpeta_tipo, "05_por_via.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    # ---------- Tipo de accidente ----------
    tabla = (
        datos_tipo["CLASE_ACC"]
        .fillna("SIN DATO")
        .value_counts()
        .rename_axis("CLASE_ACC")
        .reset_index(name="ACCIDENTES")
    )

    tabla.to_csv(
        os.path.join(carpeta_tipo, "06_tipo_accidente.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    # ---------- Gravedad ----------
    tabla = (
        datos_tipo["GRAVEDAD"]
        .fillna("SIN DATO")
        .value_counts()
        .rename_axis("GRAVEDAD")
        .reset_index(name="ACCIDENTES")
    )

    tabla.to_csv(
        os.path.join(carpeta_tipo, "07_gravedad.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    # ========================================================
    # GRÁFICOS INDIVIDUALES
    # ========================================================

    # Año
    tabla_anio = (
        datos_tipo
        .groupby("ANO_OCURRENCIA_ACC")
        .size()
        .reset_index(name="ACCIDENTES")
    )

    plt.figure(figsize=(11, 6))
    sns.lineplot(
        data=tabla_anio,
        x="ANO_OCURRENCIA_ACC",
        y="ACCIDENTES",
        marker="o"
    )
    plt.title(f"{tipo}: accidentes por año")
    plt.xlabel("Año")
    plt.ylabel("Accidentes")
    plt.xticks(tabla_anio["ANO_OCURRENCIA_ACC"])
    plt.tight_layout()
    plt.savefig(
        os.path.join(carpeta_tipo, "01_por_anio.png"),
        dpi=300,
        bbox_inches="tight"
    )
    plt.close()

    # Hora
    tabla_hora = (
        datos_tipo
        .groupby("HORA_NUM")
        .size()
        .reindex(range(24), fill_value=0)
        .reset_index(name="ACCIDENTES")
    )

    plt.figure(figsize=(13, 6))
    sns.barplot(
        data=tabla_hora,
        x="HORA_NUM",
        y="ACCIDENTES"
    )
    plt.title(f"{tipo}: accidentes por hora")
    plt.xlabel("Hora")
    plt.ylabel("Accidentes")
    plt.tight_layout()
    plt.savefig(
        os.path.join(carpeta_tipo, "02_por_hora.png"),
        dpi=300,
        bbox_inches="tight"
    )
    plt.close()

    # Día
    tabla_dia = (
        datos_tipo["DIA_SEMANA"]
        .value_counts()
        .reindex(orden_dias, fill_value=0)
        .rename_axis("DIA_SEMANA")
        .reset_index(name="ACCIDENTES")
    )

    plt.figure(figsize=(11, 6))
    sns.barplot(
        data=tabla_dia,
        x="DIA_SEMANA",
        y="ACCIDENTES",
        order=orden_dias
    )
    plt.title(f"{tipo}: accidentes por día")
    plt.xlabel("Día")
    plt.ylabel("Accidentes")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(
        os.path.join(carpeta_tipo, "03_por_dia.png"),
        dpi=300,
        bbox_inches="tight"
    )
    plt.close()

    # Localidad
    tabla_loc = (
        datos_tipo["LOCALIDAD"]
        .dropna()
        .value_counts()
        .head(15)
        .sort_values()
        .rename_axis("LOCALIDAD")
        .reset_index(name="ACCIDENTES")
    )

    plt.figure(figsize=(11, 7))
    sns.barplot(
        data=tabla_loc,
        x="ACCIDENTES",
        y="LOCALIDAD"
    )
    plt.title(f"{tipo}: top 15 localidades")
    plt.xlabel("Accidentes")
    plt.ylabel("Localidad")
    plt.tight_layout()
    plt.savefig(
        os.path.join(carpeta_tipo, "04_top_localidades.png"),
        dpi=300,
        bbox_inches="tight"
    )
    plt.close()

    # Vías
    tabla_via = (
        datos_tipo["MVINOMBRE"]
        .dropna()
        .value_counts()
    )

    tabla_via = tabla_via[
        ~tabla_via.index.astype(str).str.upper().isin([
            "SIN_NMG",
            "SIN NMG",
            "SIN NOMBRE"
        ])
    ].head(15).sort_values()

    tabla_via = (
        tabla_via
        .rename_axis("MVINOMBRE")
        .reset_index(name="ACCIDENTES")
    )

    plt.figure(figsize=(12, 8))
    sns.barplot(
        data=tabla_via,
        x="ACCIDENTES",
        y="MVINOMBRE"
    )
    plt.title(f"{tipo}: top 15 vías")
    plt.xlabel("Accidentes")
    plt.ylabel("Vía")
    plt.tight_layout()
    plt.savefig(
        os.path.join(carpeta_tipo, "05_top_vias.png"),
        dpi=300,
        bbox_inches="tight"
    )
    plt.close()


# ============================================================
# 28. MATRICES DE COMPARACIÓN ENTRE VEHÍCULOS
# ============================================================

# Hora x vehículo
hora_tipo = pd.crosstab(
    acc_micro["HORA_NUM"],
    acc_micro["TIPO_MICROMOVILIDAD"]
).reindex(range(24), fill_value=0)

guardar_tabla(
    hora_tipo.reset_index(),
    "17_comparacion_hora_tipo.csv"
)

# Día x vehículo
dia_tipo = pd.crosstab(
    acc_micro["DIA_SEMANA"],
    acc_micro["TIPO_MICROMOVILIDAD"]
).reindex(orden_dias, fill_value=0)

guardar_tabla(
    dia_tipo.reset_index(),
    "18_comparacion_dia_tipo.csv"
)

# Localidad x vehículo
localidad_tipo = pd.crosstab(
    acc_micro["LOCALIDAD"],
    acc_micro["TIPO_MICROMOVILIDAD"]
)

guardar_tabla(
    localidad_tipo.reset_index(),
    "19_comparacion_localidad_tipo.csv"
)


# ============================================================
# 29. COORDENADAS
# ============================================================

# Coordenadas válidas para Bogotá aproximadamente.
# Se eliminan solamente para el análisis espacial,
# NO se eliminan del dataset general.
coordenadas_validas = acc_micro[
    acc_micro["LATITUD"].between(3.5, 5.0)
    & acc_micro["LONGITUD"].between(-75.0, -73.0)
].copy()

print("\n" + "=" * 70)
print("COORDENADAS")
print("=" * 70)

print(f"Accidentes con coordenadas potencialmente válidas: "
      f"{len(coordenadas_validas):,}")

print(
    f"Porcentaje: "
    f"{len(coordenadas_validas) / len(acc_micro) * 100:.2f}%"
)

# ============================================================
# 30. RESUMEN EJECUTIVO AUTOMÁTICO
# ============================================================

total_micro = len(acc_micro)

top_hora = (
    por_hora.loc[
        por_hora["ACCIDENTES"].idxmax()
    ]
)

top_dia = (
    por_dia.loc[
        por_dia["ACCIDENTES"].idxmax()
    ]
)

top_localidad = (
    por_localidad.iloc[0]
)

top_via = (
    por_via.iloc[0]
    if len(por_via) > 0
    else None
)

top_clase = (
    por_clase_acc.iloc[0]
)

top_gravedad = (
    por_gravedad.iloc[0]
)

resumen = pd.DataFrame({
    "INDICADOR": [
        "Accidentes de micromovilidad",
        "Hora con más accidentes",
        "Accidentes en hora pico",
        "Día con más accidentes",
        "Accidentes en día pico",
        "Localidad con más accidentes",
        "Accidentes en localidad principal",
        "Vía con más accidentes",
        "Accidentes en vía principal",
        "Tipo de accidente predominante",
        "Accidentes del tipo predominante",
        "Gravedad predominante",
        "Accidentes de gravedad predominante"
    ],
    "VALOR": [
        total_micro,
        int(top_hora["HORA_NUM"]),
        int(top_hora["ACCIDENTES"]),
        top_dia["DIA_SEMANA"],
        int(top_dia["ACCIDENTES"]),
        top_localidad["LOCALIDAD"],
        int(top_localidad["ACCIDENTES"]),
        top_via["MVINOMBRE"] if top_via is not None else "SIN DATO",
        int(top_via["ACCIDENTES"]) if top_via is not None else 0,
        top_clase["CLASE_ACC"],
        int(top_clase["ACCIDENTES"]),
        top_gravedad["GRAVEDAD"],
        int(top_gravedad["ACCIDENTES"])
    ]
})

guardar_tabla(
    resumen,
    "00_RESUMEN_EJECUTIVO.csv"
)

# ============================================================
# 31. DATASET LIMPIO A NIVEL DE ACCIDENTE
# ============================================================

COLUMNAS_DATASET_FINAL = [
    "FORMULARIO",
    "ANO_OCURRENCIA_ACC",
    "FECHA_HORA_ACC",
    "HORA_NUM",
    "DIA_SEMANA",
    "MES_OCURRENCIA_ACC",
    "LOCALIDAD",
    "BARRIO",
    "MVINOMBRE",
    "PK_CALZADA",
    "LATITUD",
    "LONGITUD",
    "DISTANCIA_VIA",
    "CLASE_ACC",
    "GRAVEDAD",
    "TIPO_MICROMOVILIDAD"
]

dataset_final = acc_micro[COLUMNAS_DATASET_FINAL].copy()

guardar_tabla(
    dataset_final,
    "20_dataset_micromovilidad_2018_2026.csv"
)

# ============================================================
# 32. REPORTE DE CALIDAD
# ============================================================

reporte_calidad = pd.DataFrame({
    "VARIABLE": dataset_final.columns,
    "TIPO_DATO": dataset_final.dtypes.astype(str).values,
    "NULOS": dataset_final.isna().sum().values,
    "PORCENTAJE_NULOS": (
        dataset_final.isna().sum() /
        len(dataset_final) * 100
    ).round(3),
    "VALORES_UNICOS": [
        dataset_final[c].nunique(dropna=True)
        for c in dataset_final.columns
    ]
})

guardar_tabla(
    reporte_calidad,
    "21_reporte_calidad_dataset_final.csv"
)

# ============================================================
# 33. MENSAJE FINAL
# ============================================================

print("\n" + "=" * 70)
print("EDA FINALIZADO")
print("=" * 70)

print(f"""
Periodo analizado: {ANIO_INICIO}-{ANIO_FIN}
Accidentes totales analizados: {len(accidente):,}
Accidentes de micromovilidad: {len(acc_micro):,}

Categorías:
{chr(10).join(" - " + x for x in CATEGORIAS_MICROMOVILIDAD)}

Resultados principales:
 - Hora con más accidentes: {int(top_hora["HORA_NUM"]):02d}:00
 - Día con más accidentes: {top_dia["DIA_SEMANA"]}
 - Localidad principal: {top_localidad["LOCALIDAD"]}
 - Tipo de accidente principal: {top_clase["CLASE_ACC"]}
 - Gravedad principal: {top_gravedad["GRAVEDAD"]}

Los resultados fueron guardados en:
{CARPETA_SALIDA}/
""")
