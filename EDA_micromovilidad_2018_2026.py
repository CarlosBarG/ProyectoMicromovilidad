# ============================================================
# EDA DE SINIESTROS VIALES DE MICROMOVILIDAD - BOGOTÁ
# Periodo: 2018-2026
#
# VERSION AMPLIADA:
# - Agrega diagramas circulares para composiciones porcentuales.
# - Todos los gráficos muestran los valores de los datos.
# - Los gráficos de barras muestran el valor encima/de lado de cada barra.
# - Los gráficos de líneas muestran el valor de cada punto.
# - El mapa de calor muestra el valor de cada celda.
# - Los diagramas circulares muestran cantidad + porcentaje.
#
# Archivos:
#   ACCIDENTE.csv
#   VM_ACC_VEHICULO.csv
#
# Categorías de micromovilidad:
#   BICICLETA, MOTOCICLO, MOTOTRICICLO
#
# IMPORTANTE:
# - FORMULARIO es la llave entre las dos tablas.
# - Un accidente puede tener varios vehículos.
# - Para contar accidentes se trabaja con FORMULARIO único.
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

# 
# 
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


def guardar_tabla(df, nombre, carpeta=CARPETA_SALIDA):
    """Guarda una tabla CSV."""
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre)
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    print(f"Guardado: {ruta}")


def guardar_grafico(nombre, carpeta=CARPETA_SALIDA):
    """Guarda el gráfico actual en PNG."""
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre)
    plt.tight_layout()
    plt.savefig(ruta, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Gráfico: {ruta}")


def porcentaje(n, total):
    return round((n / total) * 100, 2) if total else 0


def agregar_etiquetas_barras(ax, formato="{:.0f}", rotacion=0):
    """
    Agrega el valor de cada barra.
    Funciona tanto para barras verticales como horizontales.
    """
    for contenedor in ax.containers:
        try:
            etiquetas = [formato.format(v) for v in contenedor.datavalues]
            if len(etiquetas) == 0:
                continue
            if ax.get_yaxis().get_scale() == "linear":
                pass
            ax.bar_label(
                contenedor,
                labels=etiquetas,
                padding=3,
                fontsize=9,
                rotation=rotacion
            )
        except Exception:
            # Fallback manual para versiones de matplotlib que no expongan
            # datavalues de la misma forma.
            for barra in contenedor:
                if barra.get_width() > barra.get_height():
                    valor = barra.get_width()
                    ax.text(
                        valor,
                        barra.get_y() + barra.get_height() / 2,
                        formato.format(valor),
                        va="center",
                        ha="left",
                        fontsize=9
                    )
                else:
                    valor = barra.get_height()
                    ax.text(
                        barra.get_x() + barra.get_width() / 2,
                        valor,
                        formato.format(valor),
                        va="bottom",
                        ha="center",
                        fontsize=9
                    )


def agregar_etiquetas_linea(ax, x, y, formato="{:.0f}"):
    """Agrega el valor de cada punto de un gráfico de línea."""
    for xi, yi in zip(x, y):
        if pd.notna(yi):
            ax.annotate(
                formato.format(yi),
                (xi, yi),
                textcoords="offset points",
                xytext=(0, 7),
                ha="center",
                fontsize=8
            )


def autopct_porcentaje(valores):
    """Devuelve una función para matplotlib.pie que muestra solo el porcentaje."""
    total = np.sum(valores)

    def formato(pct):
        if pct < 1.0:
            return ""
        return f"{pct:.1f}%"

    return formato


def preparar_leyenda_circular(etiquetas, valores):
    """Crea etiquetas de leyenda con categoría, cantidad y porcentaje."""
    total = np.sum(valores)
    leyenda = []

    for etiqueta, valor in zip(etiquetas, valores):
        pct = (valor / total * 100) if total else 0
        leyenda.append(f"{etiqueta}: {int(valor):,} ({pct:.2f}%)")

    return leyenda


def grafico_circular(
    tabla,
    columna_categoria,
    columna_valor,
    titulo,
    nombre_archivo,
    carpeta=CARPETA_SALIDA,
    figsize=None
):
    """
    Genera un diagrama circular optimizado para evitar textos superpuestos.

    - Las categorías ya no se escriben directamente sobre el gráfico.
    - La leyenda contiene categoría + cantidad + porcentaje.
    - Solo se muestran porcentajes dentro del círculo cuando hay pocas
      categorías y el porcentaje es suficientemente grande.
    - Cuando hay muchas categorías, se elimina el texto interno y se usa
      únicamente la leyenda para mantener la legibilidad.
    """
    datos = tabla[[columna_categoria, columna_valor]].copy()
    datos = datos.dropna(subset=[columna_categoria, columna_valor])
    datos = datos[datos[columna_valor] > 0]

    if datos.empty:
        print(f"Sin datos para el gráfico circular: {titulo}")
        return

    valores = datos[columna_valor].to_numpy(dtype=float)
    etiquetas = datos[columna_categoria].astype(str).to_numpy()
    numero_categorias = len(datos)

    # Tamaño dinámico: los gráficos con más categorías necesitan más espacio.
    if figsize is None:
        if numero_categorias <= 4:
            figsize = (10, 8)
        elif numero_categorias <= 7:
            figsize = (11, 8)
        elif numero_categorias <= 10:
            figsize = (12, 8)
        else:
            figsize = (13, 9)

    fig, ax = plt.subplots(figsize=figsize)

    # Con muchas categorías los porcentajes dentro del pie también pueden
    # superponerse, por lo que solo se muestran con pocas categorías.
    mostrar_porcentajes = numero_categorias <= 7
    autopct = autopct_porcentaje(valores) if mostrar_porcentajes else None

    # IMPORTANTE: matplotlib.pyplot.pie() devuelve 2 elementos cuando
    # autopct=None y 3 elementos cuando autopct está definido.
    # Para evitar el error "not enough values to unpack", se manejan
    # ambos casos explícitamente.
    if mostrar_porcentajes:
        wedges, textos, autotextos = ax.pie(
            valores,
            labels=None,
            autopct=autopct,
            startangle=90,
            counterclock=False,
            pctdistance=0.68,
            textprops={"fontsize": 9},
            wedgeprops={"linewidth": 1, "edgecolor": "white"}
        )

        for texto in autotextos:
            texto.set_fontsize(9)
            texto.set_fontweight("bold")
    else:
        wedges, textos = ax.pie(
            valores,
            labels=None,
            autopct=None,
            startangle=90,
            counterclock=False,
            wedgeprops={"linewidth": 1, "edgecolor": "white"}
        )

    leyenda = preparar_leyenda_circular(etiquetas, valores)

    # La leyenda se coloca fuera del círculo para que los nombres largos
    # (localidades, vías, PK_CALZADA, etc.) nunca se monten entre sí.
    ax.legend(
        wedges,
        leyenda,
        title="Categoría: cantidad (porcentaje)",
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        fontsize=8,
        title_fontsize=9,
        frameon=True,
        borderaxespad=0.0
    )

    ax.set_title(titulo, fontsize=13, pad=18)
    ax.axis("equal")

    # Reservar espacio suficiente para la leyenda exterior.
    fig.subplots_adjust(left=0.03, right=0.68, top=0.88, bottom=0.06)

    guardar_grafico(nombre_archivo, carpeta)


# ============================================================
# FUNCIÓN PARA PIES CON TOP N + "OTROS"
# ============================================================

def preparar_top_otros(df, columna_categoria, columna_valor="ACCIDENTES", top_n=10):
    """Conserva las categorías principales y agrupa el resto como OTROS."""
    temp = df[[columna_categoria, columna_valor]].copy()
    temp = temp.dropna(subset=[columna_categoria, columna_valor])
    temp = temp.sort_values(columna_valor, ascending=False)

    if len(temp) <= top_n:
        return temp

    principales = temp.head(top_n).copy()
    resto = temp.iloc[top_n:][columna_valor].sum()

    if resto > 0:
        fila_otros = pd.DataFrame({
            columna_categoria: ["OTROS"],
            columna_valor: [resto]
        })
        principales = pd.concat([principales, fila_otros], ignore_index=True)

    return principales


def grafico_circular_top(
    df,
    columna_categoria,
    columna_valor,
    titulo,
    nombre_archivo,
    carpeta=CARPETA_SALIDA,
    top_n=10
):
    """Genera un pie legible conservando Top N y agrupando el resto en OTROS."""
    temp = preparar_top_otros(df, columna_categoria, columna_valor, top_n)
    grafico_circular(
        temp,
        columna_categoria,
        columna_valor,
        titulo,
        nombre_archivo,
        carpeta
    )


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

accidente["ANO_OCURRENCIA_ACC"] = pd.to_numeric(
    accidente["ANO_OCURRENCIA_ACC"], errors="coerce"
)

accidente["LATITUD"] = pd.to_numeric(
    accidente["LATITUD"], errors="coerce"
)
accidente["LONGITUD"] = pd.to_numeric(
    accidente["LONGITUD"], errors="coerce"
)

for col in ["PK_CALZADA", "DISTANCIA_VIA"]:
    accidente[col] = pd.to_numeric(accidente[col], errors="coerce")

accidente["FECHA_HORA_ACC"] = pd.to_datetime(
    accidente["FECHA_HORA_ACC"], errors="coerce"
)

# ============================================================
# 5. FILTRO TEMPORAL 2018-2026
# ============================================================

accidente = accidente[
    accidente["ANO_OCURRENCIA_ACC"].between(ANIO_INICIO, ANIO_FIN)
].copy()

print(
    f"Accidentes después del filtro {ANIO_INICIO}-{ANIO_FIN}: "
    f"{len(accidente):,}"
)

# ============================================================
# 6. REVISIÓN DE DUPLICADOS
# ============================================================

print("\n" + "=" * 70)
print("DUPLICADOS")
print("=" * 70)

duplicados_formulario = accidente["FORMULARIO"].duplicated().sum()
print(f"FORMULARIO duplicados: {duplicados_formulario:,}")

if duplicados_formulario > 0:
    accidente = accidente.drop_duplicates(
        subset="FORMULARIO", keep="first"
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
print(vehiculo_micro["CLASE"].value_counts(dropna=False).to_string())

# ============================================================
# 8. RELACIONAR VEHÍCULOS CON ACCIDENTES
# ============================================================

mapa_accidente = accidente[
    ["FORMULARIO", "ANO_OCURRENCIA_ACC"]
].drop_duplicates("FORMULARIO")

vehiculo_micro = vehiculo_micro.merge(
    mapa_accidente,
    on="FORMULARIO",
    how="inner"
)

print(
    f"\nRegistros de vehículos micromovilidad 2018-2026: "
    f"{len(vehiculo_micro):,}"
)

# ============================================================
# 9. ACCIDENTES ÚNICOS DE MICROMOVILIDAD
# ============================================================

formularios_micro = (
    vehiculo_micro["FORMULARIO"]
    .dropna()
    .drop_duplicates()
)

acc_micro = accidente[
    accidente["FORMULARIO"].isin(formularios_micro)
].copy()

print(f"Accidentes únicos de micromovilidad: {len(acc_micro):,}")

# ============================================================
# 10. TIPO DE MICROMOVILIDAD POR ACCIDENTE
# ============================================================

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
    tipos_por_accidente[["FORMULARIO", "TIPO_MICROMOVILIDAD"]],
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
# 12. DIAGRAMAS CIRCULARES GENERALES
# ============================================================

# 12.1 Composición de todos los accidentes de micromovilidad
#     Las categorías son mutuamente excluyentes porque MULTIPLE
#     agrupa accidentes que involucran más de un tipo.
grafico_circular(
    tabla_tipo,
    "TIPO_MICROMOVILIDAD",
    "ACCIDENTES",
    "Distribución de accidentes por tipo de micromovilidad",
    "12_01_circular_tipo_micromovilidad.png"
)

# 12.2 Bicicletas frente al resto de micromovilidad.
#     Este gráfico responde directamente a:
#     "¿Qué porcentaje de los accidentes de micromovilidad involucra bicicletas?"

total_accidentes_micro = len(acc_micro)
accidentes_bicicleta = (
    vehiculo_micro.loc[
        vehiculo_micro["CLASE"] == "BICICLETA", "FORMULARIO"
    ]
    .dropna()
    .drop_duplicates()
    .isin(acc_micro["FORMULARIO"])
    .sum()
)

# La operación anterior puede producir una serie booleana; para máxima claridad
# usamos directamente el conjunto de formularios.
formularios_bicicleta = set(
    vehiculo_micro.loc[
        vehiculo_micro["CLASE"] == "BICICLETA", "FORMULARIO"
    ].dropna().unique()
)

formularios_micro_set = set(acc_micro["FORMULARIO"].dropna().unique())
accidentes_bicicleta = len(formularios_bicicleta.intersection(formularios_micro_set))
accidentes_no_bicicleta = total_accidentes_micro - accidentes_bicicleta

tabla_bici_resto = pd.DataFrame({
    "CATEGORIA": ["Con bicicleta", "Sin bicicleta"],
    "ACCIDENTES": [accidentes_bicicleta, accidentes_no_bicicleta]
})

tabla_bici_resto["PORCENTAJE"] = (
    tabla_bici_resto["ACCIDENTES"] /
    tabla_bici_resto["ACCIDENTES"].sum() * 100
).round(2)

guardar_tabla(
    tabla_bici_resto,
    "02_bicicleta_vs_resto.csv"
)

grafico_circular(
    tabla_bici_resto,
    "CATEGORIA",
    "ACCIDENTES",
    "Accidentes de micromovilidad: con bicicleta vs sin bicicleta",
    "12_02_circular_bicicleta_vs_resto.png"
)

# ============================================================
# 13. NULOS - ACCIDENTES GENERALES 2018-2026
# ============================================================

nulos_acc = pd.DataFrame({
    "VARIABLE": accidente.columns,
    "NULOS": accidente.isna().sum().values
})

nulos_acc["PORCENTAJE_NULOS"] = (
    nulos_acc["NULOS"] / len(accidente) * 100
).round(3)

nulos_acc = nulos_acc.sort_values(
    "PORCENTAJE_NULOS", ascending=False
)

print("\n" + "=" * 70)
print("DATOS NULOS - ACCIDENTES")
print("=" * 70)
print(nulos_acc.to_string(index=False))
guardar_tabla(nulos_acc, "03_nulos_accidentes.csv")

# ============================================================
# 14. NULOS - ACCIDENTES DE MICROMOVILIDAD
# ============================================================

nulos_micro = pd.DataFrame({
    "VARIABLE": acc_micro.columns,
    "NULOS": acc_micro.isna().sum().values
})

nulos_micro["PORCENTAJE_NULOS"] = (
    nulos_micro["NULOS"] / len(acc_micro) * 100
).round(3)

nulos_micro = nulos_micro.sort_values(
    "PORCENTAJE_NULOS", ascending=False
)

print("\n" + "=" * 70)
print("DATOS NULOS - MICROMOVILIDAD")
print("=" * 70)
print(nulos_micro.to_string(index=False))
guardar_tabla(nulos_micro, "04_nulos_accidentes_micromovilidad.csv")

# ============================================================
# 15. NULOS - VEHÍCULOS DE MICROMOVILIDAD
# ============================================================

nulos_veh = pd.DataFrame({
    "VARIABLE": vehiculo_micro.columns,
    "NULOS": vehiculo_micro.isna().sum().values
})

nulos_veh["PORCENTAJE_NULOS"] = (
    nulos_veh["NULOS"] / len(vehiculo_micro) * 100
).round(3)

nulos_veh = nulos_veh.sort_values(
    "PORCENTAJE_NULOS", ascending=False
)

print("\n" + "=" * 70)
print("DATOS NULOS - VEHÍCULOS")
print("=" * 70)
print(nulos_veh.to_string(index=False))
guardar_tabla(nulos_veh, "05_nulos_vehiculos_micromovilidad.csv")

# ============================================================
# 16. ACCIDENTES POR AÑO
# ============================================================

por_anio = (
    acc_micro.groupby("ANO_OCURRENCIA_ACC")
    .size()
    .reset_index(name="ACCIDENTES")
)

por_anio["PORCENTAJE"] = (
    por_anio["ACCIDENTES"] /
    por_anio["ACCIDENTES"].sum() * 100
).round(2)

guardar_tabla(por_anio, "06_accidentes_por_anio.csv")

plt.figure(figsize=(11, 6))
ax = sns.lineplot(
    data=por_anio,
    x="ANO_OCURRENCIA_ACC",
    y="ACCIDENTES",
    marker="o"
)
plt.title("Accidentes de micromovilidad por año (2018-2026)")
plt.xlabel("Año")
plt.ylabel("Número de accidentes")
plt.xticks(por_anio["ANO_OCURRENCIA_ACC"])
agregar_etiquetas_linea(
    ax,
    por_anio["ANO_OCURRENCIA_ACC"],
    por_anio["ACCIDENTES"]
)
guardar_grafico("01_accidentes_por_anio.png")

# Circular: composición del total de accidentes por año.
# No sustituye la línea temporal; sirve para mostrar el peso porcentual de cada año.
grafico_circular(
    por_anio,
    "ANO_OCURRENCIA_ACC",
    "ACCIDENTES",
    "Distribución porcentual de accidentes por año",
    "12_06_circular_accidentes_por_anio.png"
)

# ============================================================
# 17. AÑO x TIPO DE MICROMOVILIDAD
# ============================================================

anio_tipo = pd.crosstab(
    acc_micro["ANO_OCURRENCIA_ACC"],
    acc_micro["TIPO_MICROMOVILIDAD"]
).reset_index()

guardar_tabla(anio_tipo, "07_anio_tipo_micromovilidad.csv")

plt.figure(figsize=(12, 6))
ax = plt.gca()

for tipo in ["BICICLETA", "MOTOCICLO", "MOTOTRICICLO", "MULTIPLE"]:
    if tipo in anio_tipo.columns:
        linea = ax.plot(
            anio_tipo["ANO_OCURRENCIA_ACC"],
            anio_tipo[tipo],
            marker="o",
            label=tipo
        )[0]
        for x, y in zip(
            anio_tipo["ANO_OCURRENCIA_ACC"],
            anio_tipo[tipo]
        ):
            if y > 0:
                ax.annotate(
                    f"{int(y):,}",
                    (x, y),
                    textcoords="offset points",
                    xytext=(0, 7),
                    ha="center",
                    fontsize=7
                )

plt.title("Accidentes por año y tipo de micromovilidad")
plt.xlabel("Año")
plt.ylabel("Accidentes")
plt.legend()
guardar_grafico("02_anio_tipo_micromovilidad.png")

# Circular individual por tipo: muestra qué años concentran los accidentes de cada tipo.
for tipo_circular in ["BICICLETA", "MOTOCICLO", "MOTOTRICICLO", "MULTIPLE"]:
    if tipo_circular in anio_tipo.columns:
        datos_pie_tipo = anio_tipo[["ANO_OCURRENCIA_ACC", tipo_circular]].copy()
        datos_pie_tipo = datos_pie_tipo.rename(columns={tipo_circular: "ACCIDENTES"})
        datos_pie_tipo = datos_pie_tipo[datos_pie_tipo["ACCIDENTES"] > 0]
        if not datos_pie_tipo.empty:
            grafico_circular(
                datos_pie_tipo,
                "ANO_OCURRENCIA_ACC",
                "ACCIDENTES",
                f"Distribución anual de accidentes: {tipo_circular}",
                f"12_07_circular_anio_{tipo_circular.lower()}.png"
            )

# ============================================================
# 18. HORA
# ============================================================

def extraer_hora(valor):
    if pd.isna(valor):
        return np.nan

    texto = str(valor).strip()

    try:
        partes = texto.split(":")
        if len(partes) >= 2:
            hora = int(partes[0])
            if 0 <= hora <= 23:
                return hora
    except Exception:
        pass

    try:
        fecha = pd.to_datetime(texto, errors="coerce")
        return fecha.hour if pd.notna(fecha) else np.nan
    except Exception:
        return np.nan


acc_micro["HORA_NUM"] = acc_micro["HORA_OCURRENCIA_ACC"].apply(extraer_hora)

faltantes_hora = acc_micro["HORA_NUM"].isna()
acc_micro.loc[faltantes_hora, "HORA_NUM"] = (
    acc_micro.loc[faltantes_hora, "FECHA_HORA_ACC"].dt.hour
)

acc_micro["HORA_NUM"] = pd.to_numeric(
    acc_micro["HORA_NUM"], errors="coerce"
)

por_hora = (
    acc_micro.dropna(subset=["HORA_NUM"])
    .groupby("HORA_NUM")
    .size()
    .reindex(range(24), fill_value=0)
    .reset_index(name="ACCIDENTES")
)

por_hora["PORCENTAJE"] = (
    por_hora["ACCIDENTES"] /
    por_hora["ACCIDENTES"].sum() * 100
).round(2)

guardar_tabla(por_hora, "08_accidentes_por_hora.csv")

plt.figure(figsize=(13, 6))
ax = sns.barplot(color="C0", data=por_hora, x="HORA_NUM", y="ACCIDENTES")
plt.title("Accidentes de micromovilidad por hora")
plt.xlabel("Hora del día")
plt.ylabel("Número de accidentes")
agregar_etiquetas_barras(ax)
guardar_grafico("03_accidentes_por_hora.png")

# Circular por franjas horarias para evitar 24 porciones poco legibles.
def franja_horaria(h):
    if 0 <= h <= 5:
        return "00-05"
    if 6 <= h <= 8:
        return "06-08"
    if 9 <= h <= 11:
        return "09-11"
    if 12 <= h <= 14:
        return "12-14"
    if 15 <= h <= 17:
        return "15-17"
    if 18 <= h <= 20:
        return "18-20"
    return "21-23"

por_franja = por_hora.copy()
por_franja["FRANJA_HORARIA"] = por_franja["HORA_NUM"].astype(int).apply(franja_horaria)
por_franja = (
    por_franja.groupby("FRANJA_HORARIA", sort=False)["ACCIDENTES"]
    .sum().reindex(["00-05", "06-08", "09-11", "12-14", "15-17", "18-20", "21-23"], fill_value=0)
    .rename_axis("FRANJA_HORARIA")
    .reset_index()
)
grafico_circular(
    por_franja,
    "FRANJA_HORARIA",
    "ACCIDENTES",
    "Distribución porcentual de accidentes por franja horaria",
    "12_08_circular_franja_horaria.png"
)

# ============================================================
# 19. DÍA DE LA SEMANA
# ============================================================

# Se usa la fecha real cuando está disponible y se conserva el
# dato original como respaldo.
dia_fecha = acc_micro["FECHA_HORA_ACC"].dt.day_name()

mapa_dias = {
    "Monday": "Lunes",
    "Tuesday": "Martes",
    "Wednesday": "Miércoles",
    "Thursday": "Jueves",
    "Friday": "Viernes",
    "Saturday": "Sábado",
    "Sunday": "Domingo"
}

acc_micro["DIA_SEMANA"] = dia_fecha.map(mapa_dias)

faltantes_dia = acc_micro["DIA_SEMANA"].isna()
acc_micro.loc[faltantes_dia, "DIA_SEMANA"] = (
    acc_micro.loc[faltantes_dia, "DIA_OCURRENCIA_ACC"]
    .str.title()
)

orden_dias = [
    "Lunes", "Martes", "Miércoles", "Jueves",
    "Viernes", "Sábado", "Domingo"
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

guardar_tabla(por_dia, "09_accidentes_por_dia_semana.csv")

plt.figure(figsize=(11, 6))
ax = sns.barplot(color="C0", 
    data=por_dia,
    x="DIA_SEMANA",
    y="ACCIDENTES",
    order=orden_dias
)
plt.title("Accidentes de micromovilidad por día de la semana")
plt.xlabel("Día")
plt.ylabel("Número de accidentes")
plt.xticks(rotation=20)
agregar_etiquetas_barras(ax)
guardar_grafico("04_accidentes_por_dia_semana.png")

# Circular: distribución por día de la semana.
# Es útil para mostrar porcentajes globales, aunque para comparar
# visualmente días con precisión el gráfico de barras es mejor.
grafico_circular(
    por_dia,
    "DIA_SEMANA",
    "ACCIDENTES",
    "Distribución porcentual de accidentes por día de la semana",
    "12_03_circular_dia_semana.png"
)

# ============================================================
# 19.1 MES
# ============================================================

orden_meses = [
    "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
    "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
]

por_mes = (
    acc_micro["MES_OCURRENCIA_ACC"]
    .fillna("SIN DATO")
    .astype(str).str.upper()
    .value_counts()
    .reindex(orden_meses, fill_value=0)
    .rename_axis("MES")
    .reset_index(name="ACCIDENTES")
)

por_mes["PORCENTAJE"] = (
    por_mes["ACCIDENTES"] / por_mes["ACCIDENTES"].sum() * 100
).round(2)

guardar_tabla(por_mes, "09_1_accidentes_por_mes.csv")

plt.figure(figsize=(12, 6))
ax = sns.barplot(color="C0", data=por_mes, x="MES", y="ACCIDENTES", order=orden_meses)
plt.title("Accidentes de micromovilidad por mes")
plt.xlabel("Mes")
plt.ylabel("Número de accidentes")
plt.xticks(rotation=35)
agregar_etiquetas_barras(ax)
guardar_grafico("04_1_accidentes_por_mes.png")

grafico_circular(
    por_mes,
    "MES",
    "ACCIDENTES",
    "Distribución porcentual de accidentes por mes",
    "12_09_circular_mes.png"
)

# ============================================================
# 20. HORA x DÍA
# ============================================================

hora_dia = pd.crosstab(
    acc_micro["DIA_SEMANA"],
    acc_micro["HORA_NUM"]
).reindex(orden_dias)

hora_dia = hora_dia.reindex(columns=range(24), fill_value=0)

guardar_tabla(hora_dia.reset_index(), "10_hora_dia.csv")

plt.figure(figsize=(15, 6))
sns.heatmap(
    hora_dia,
    annot=True,
    fmt="g",
    linewidths=0.3
)
plt.title("Accidentes de micromovilidad: día vs hora")
plt.xlabel("Hora")
plt.ylabel("Día")
guardar_grafico("05_heatmap_dia_hora.png")

# ============================================================
# 21. LOCALIDADES
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

guardar_tabla(por_localidad, "11_accidentes_por_localidad.csv")

top_localidades = por_localidad.head(15).sort_values("ACCIDENTES")

plt.figure(figsize=(11, 7))
ax = sns.barplot(color="C0", 
    data=top_localidades,
    x="ACCIDENTES",
    y="LOCALIDAD"
)
plt.title("Top 15 localidades con accidentes de micromovilidad")
plt.xlabel("Número de accidentes")
plt.ylabel("Localidad")
agregar_etiquetas_barras(ax)
guardar_grafico("06_top_localidades.png")

grafico_circular_top(
    por_localidad, "LOCALIDAD", "ACCIDENTES",
    "Distribución de accidentes por localidad (Top 10 + otros)",
    "12_10_circular_localidades.png", top_n=10
)

# ============================================================
# 22. BARRIOS
# ============================================================

por_barrio = (
    acc_micro["BARRIO"]
    .dropna()
    .value_counts()
    .rename_axis("BARRIO")
    .reset_index(name="ACCIDENTES")
)

guardar_tabla(por_barrio, "12_accidentes_por_barrio.csv")

top_barrios = por_barrio.head(20).sort_values("ACCIDENTES")

plt.figure(figsize=(11, 8))
ax = sns.barplot(color="C0", 
    data=top_barrios,
    x="ACCIDENTES",
    y="BARRIO"
)
plt.title("Top 20 barrios con accidentes de micromovilidad")
plt.xlabel("Número de accidentes")
plt.ylabel("Barrio")
agregar_etiquetas_barras(ax)
guardar_grafico("07_top_barrios.png")

grafico_circular_top(
    por_barrio, "BARRIO", "ACCIDENTES",
    "Distribución de accidentes por barrio (Top 10 + otros)",
    "12_11_circular_barrios.png", top_n=10
)

# ============================================================
# 23. VÍAS / MVINOMBRE
# ============================================================

mvi = acc_micro["MVINOMBRE"].dropna()
mvi = mvi[mvi.astype(str).str.strip() != ""]
mvi = mvi[
    ~mvi.astype(str).str.upper().isin([
        "SIN_NMG", "SIN NMG", "SIN NOMBRE"
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

guardar_tabla(por_via, "13_accidentes_por_via.csv")

top_vias = por_via.head(20).sort_values("ACCIDENTES")

plt.figure(figsize=(12, 9))
ax = sns.barplot(color="C0", 
    data=top_vias,
    x="ACCIDENTES",
    y="MVINOMBRE"
)
plt.title("Top 20 vías con accidentes de micromovilidad")
plt.xlabel("Número de accidentes")
plt.ylabel("Vía")
agregar_etiquetas_barras(ax)
guardar_grafico("08_top_vias.png")

grafico_circular_top(
    por_via, "MVINOMBRE", "ACCIDENTES",
    "Distribución de accidentes por vía (Top 10 + otras)",
    "12_12_circular_vias.png", top_n=10
)

# ============================================================
# 24. PK_CALZADA
# ============================================================

por_calzada = (
    acc_micro["PK_CALZADA"]
    .dropna()
    .value_counts()
    .rename_axis("PK_CALZADA")
    .reset_index(name="ACCIDENTES")
)

guardar_tabla(por_calzada, "14_accidentes_por_pk_calzada.csv")

top_calzadas = por_calzada.head(20).sort_values("ACCIDENTES")

plt.figure(figsize=(11, 8))
ax = sns.barplot(color="C0", 
    data=top_calzadas,
    x="ACCIDENTES",
    y="PK_CALZADA"
)
plt.title("Top 20 calzadas/segmentos por número de accidentes")
plt.xlabel("Número de accidentes")
plt.ylabel("PK_CALZADA")
agregar_etiquetas_barras(ax)
guardar_grafico("09_top_calzadas.png")

grafico_circular_top(
    por_calzada, "PK_CALZADA", "ACCIDENTES",
    "Distribución de accidentes por PK de calzada (Top 10 + otros)",
    "12_13_circular_pk_calzada.png", top_n=10
)

# ============================================================
# 25. CLASE DE ACCIDENTE
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

guardar_tabla(por_clase_acc, "15_tipo_accidente.csv")

plt.figure(figsize=(11, 6))
ax = sns.barplot(color="C0", 
    data=por_clase_acc,
    x="ACCIDENTES",
    y="CLASE_ACC"
)
plt.title("Tipo de accidente de micromovilidad")
plt.xlabel("Número de accidentes")
plt.ylabel("Tipo de accidente")
agregar_etiquetas_barras(ax)
guardar_grafico("10_tipo_accidente.png")

# Circular: aquí sí tiene mucho sentido porque las clases forman
# una composición del total de accidentes.
grafico_circular(
    por_clase_acc,
    "CLASE_ACC",
    "ACCIDENTES",
    "Distribución porcentual por clase de accidente",
    "12_04_circular_clase_accidente.png"
)

# ============================================================
# 26. GRAVEDAD
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

guardar_tabla(por_gravedad, "16_gravedad.csv")

plt.figure(figsize=(10, 6))
ax = sns.barplot(color="C0", 
    data=por_gravedad,
    x="ACCIDENTES",
    y="GRAVEDAD"
)
plt.title("Gravedad de accidentes de micromovilidad")
plt.xlabel("Número de accidentes")
plt.ylabel("Gravedad")
agregar_etiquetas_barras(ax)
guardar_grafico("11_gravedad.png")

# Circular: excelente para comunicar la proporción de heridos,
# muertos y solo daños.
grafico_circular(
    por_gravedad,
    "GRAVEDAD",
    "ACCIDENTES",
    "Distribución porcentual por gravedad del accidente",
    "12_05_circular_gravedad.png"
)

# ============================================================
# 27. GRAVEDAD POR AÑO
# ============================================================

anio_gravedad = pd.crosstab(
    acc_micro["ANO_OCURRENCIA_ACC"],
    acc_micro["GRAVEDAD"]
).reset_index()

guardar_tabla(anio_gravedad, "17_anio_gravedad.csv")

# Circular de gravedad para cada año.
for anio in sorted(acc_micro["ANO_OCURRENCIA_ACC"].dropna().unique()):
    datos_gravedad_anio = (
        acc_micro.loc[acc_micro["ANO_OCURRENCIA_ACC"] == anio, "GRAVEDAD"]
        .fillna("SIN DATO")
        .value_counts()
        .rename_axis("GRAVEDAD")
        .reset_index(name="ACCIDENTES")
    )
    grafico_circular(
        datos_gravedad_anio,
        "GRAVEDAD",
        "ACCIDENTES",
        f"Gravedad de accidentes - {int(anio)}",
        f"12_14_circular_gravedad_{int(anio)}.png"
    )

# ============================================================
# 28. ANÁLISIS POR CADA VEHÍCULO
# ============================================================

print("\n" + "=" * 70)
print("ANÁLISIS INDIVIDUAL DE CADA VEHÍCULO")
print("=" * 70)

for tipo in CATEGORIAS_MICROMOVILIDAD:

    print("\n" + "-" * 70)
    print(tipo)
    print("-" * 70)

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

    carpeta_tipo = os.path.join(CARPETA_SALIDA, tipo)
    os.makedirs(carpeta_tipo, exist_ok=True)

    # ---------- Año ----------
    tabla = (
        datos_tipo.groupby("ANO_OCURRENCIA_ACC")
        .size()
        .reset_index(name="ACCIDENTES")
    )
    tabla["PORCENTAJE"] = (
        tabla["ACCIDENTES"] / tabla["ACCIDENTES"].sum() * 100
    ).round(2)
    guardar_tabla(tabla, "01_por_anio.csv", carpeta_tipo)

    # ---------- Hora ----------
    tabla = (
        datos_tipo.groupby("HORA_NUM")
        .size()
        .reindex(range(24), fill_value=0)
        .reset_index(name="ACCIDENTES")
    )
    tabla["PORCENTAJE"] = (
        tabla["ACCIDENTES"] / tabla["ACCIDENTES"].sum() * 100
    ).round(2)
    guardar_tabla(tabla, "02_por_hora.csv", carpeta_tipo)

    # ---------- Día ----------
    tabla = (
        datos_tipo["DIA_SEMANA"]
        .value_counts()
        .reindex(orden_dias, fill_value=0)
        .rename_axis("DIA_SEMANA")
        .reset_index(name="ACCIDENTES")
    )
    tabla["PORCENTAJE"] = (
        tabla["ACCIDENTES"] / tabla["ACCIDENTES"].sum() * 100
    ).round(2)
    guardar_tabla(tabla, "03_por_dia.csv", carpeta_tipo)

    # ---------- Localidad ----------
    tabla = (
        datos_tipo["LOCALIDAD"]
        .fillna("SIN DATO")
        .value_counts()
        .rename_axis("LOCALIDAD")
        .reset_index(name="ACCIDENTES")
    )
    tabla["PORCENTAJE"] = (
        tabla["ACCIDENTES"] / tabla["ACCIDENTES"].sum() * 100
    ).round(2)
    guardar_tabla(tabla, "04_por_localidad.csv", carpeta_tipo)

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
            "SIN_NMG", "SIN NMG", "SIN NOMBRE"
        ])
    ].copy()
    tabla["PORCENTAJE"] = (
        tabla["ACCIDENTES"] / tabla["ACCIDENTES"].sum() * 100
    ).round(2)
    guardar_tabla(tabla, "05_por_via.csv", carpeta_tipo)

    # ---------- Tipo de accidente ----------
    tabla = (
        datos_tipo["CLASE_ACC"]
        .fillna("SIN DATO")
        .value_counts()
        .rename_axis("CLASE_ACC")
        .reset_index(name="ACCIDENTES")
    )
    tabla["PORCENTAJE"] = (
        tabla["ACCIDENTES"] / tabla["ACCIDENTES"].sum() * 100
    ).round(2)
    guardar_tabla(tabla, "06_tipo_accidente.csv", carpeta_tipo)

    # ---------- Gravedad ----------
    tabla = (
        datos_tipo["GRAVEDAD"]
        .fillna("SIN DATO")
        .value_counts()
        .rename_axis("GRAVEDAD")
        .reset_index(name="ACCIDENTES")
    )
    tabla["PORCENTAJE"] = (
        tabla["ACCIDENTES"] / tabla["ACCIDENTES"].sum() * 100
    ).round(2)
    guardar_tabla(tabla, "07_gravedad.csv", carpeta_tipo)

    # ---------- Mes ----------
    tabla_mes = (
        datos_tipo["MES_OCURRENCIA_ACC"]
        .fillna("SIN DATO").astype(str).str.upper()
        .value_counts().reindex(orden_meses, fill_value=0)
        .rename_axis("MES").reset_index(name="ACCIDENTES")
    )
    tabla_mes["PORCENTAJE"] = (tabla_mes["ACCIDENTES"] / tabla_mes["ACCIDENTES"].sum() * 100).round(2)
    guardar_tabla(tabla_mes, "08_por_mes.csv", carpeta_tipo)

    # ========================================================
    # GRÁFICOS INDIVIDUALES
    # ========================================================

    # Año
    tabla_anio = (
        datos_tipo.groupby("ANO_OCURRENCIA_ACC")
        .size().reset_index(name="ACCIDENTES")
    )
    plt.figure(figsize=(11, 6))
    ax = sns.lineplot(
        data=tabla_anio,
        x="ANO_OCURRENCIA_ACC",
        y="ACCIDENTES",
        marker="o"
    )
    plt.title(f"{tipo}: accidentes por año")
    plt.xlabel("Año")
    plt.ylabel("Accidentes")
    plt.xticks(tabla_anio["ANO_OCURRENCIA_ACC"])
    agregar_etiquetas_linea(
        ax,
        tabla_anio["ANO_OCURRENCIA_ACC"],
        tabla_anio["ACCIDENTES"]
    )
    guardar_grafico("01_por_anio.png", carpeta_tipo)

    # Hora
    tabla_hora = (
        datos_tipo.groupby("HORA_NUM")
        .size().reindex(range(24), fill_value=0)
        .reset_index(name="ACCIDENTES")
    )
    plt.figure(figsize=(13, 6))
    ax = sns.barplot(color="C0", 
        data=tabla_hora,
        x="HORA_NUM",
        y="ACCIDENTES"
    )
    plt.title(f"{tipo}: accidentes por hora")
    plt.xlabel("Hora")
    plt.ylabel("Accidentes")
    agregar_etiquetas_barras(ax)
    guardar_grafico("02_por_hora.png", carpeta_tipo)

    # Día
    tabla_dia = (
        datos_tipo["DIA_SEMANA"]
        .value_counts()
        .reindex(orden_dias, fill_value=0)
        .rename_axis("DIA_SEMANA")
        .reset_index(name="ACCIDENTES")
    )
    plt.figure(figsize=(11, 6))
    ax = sns.barplot(color="C0", 
        data=tabla_dia,
        x="DIA_SEMANA",
        y="ACCIDENTES",
        order=orden_dias
    )
    plt.title(f"{tipo}: accidentes por día")
    plt.xlabel("Día")
    plt.ylabel("Accidentes")
    plt.xticks(rotation=20)
    agregar_etiquetas_barras(ax)
    guardar_grafico("03_por_dia.png", carpeta_tipo)

    # Mes
    plt.figure(figsize=(12, 6))
    ax = sns.barplot(color="C0", data=tabla_mes, x="MES", y="ACCIDENTES", order=orden_meses)
    plt.title(f"{tipo}: accidentes por mes")
    plt.xlabel("Mes")
    plt.ylabel("Accidentes")
    plt.xticks(rotation=35)
    agregar_etiquetas_barras(ax)
    guardar_grafico("03_1_por_mes.png", carpeta_tipo)

    grafico_circular(
        tabla_mes, "MES", "ACCIDENTES",
        f"{tipo}: distribución por mes",
        "10_1_circular_mes.png", carpeta_tipo
    )

    # Localidad
    tabla_loc = (
        datos_tipo["LOCALIDAD"]
        .fillna("SIN DATO")
        .value_counts()
        .head(15)
        .sort_values()
        .rename_axis("LOCALIDAD")
        .reset_index(name="ACCIDENTES")
    )
    plt.figure(figsize=(11, 7))
    ax = sns.barplot(color="C0", 
        data=tabla_loc,
        x="ACCIDENTES",
        y="LOCALIDAD"
    )
    plt.title(f"{tipo}: top 15 localidades")
    plt.xlabel("Accidentes")
    plt.ylabel("Localidad")
    agregar_etiquetas_barras(ax)
    guardar_grafico("04_top_localidades.png", carpeta_tipo)

    # Vías
    tabla_via = datos_tipo["MVINOMBRE"].dropna().value_counts()
    tabla_via = tabla_via[
        ~tabla_via.index.astype(str).str.upper().isin([
            "SIN_NMG", "SIN NMG", "SIN NOMBRE"
        ])
    ].head(15).sort_values()
    tabla_via = (
        tabla_via.rename_axis("MVINOMBRE")
        .reset_index(name="ACCIDENTES")
    )
    plt.figure(figsize=(12, 8))
    ax = sns.barplot(color="C0", 
        data=tabla_via,
        x="ACCIDENTES",
        y="MVINOMBRE"
    )
    plt.title(f"{tipo}: top 15 vías")
    plt.xlabel("Accidentes")
    plt.ylabel("Vía")
    agregar_etiquetas_barras(ax)
    guardar_grafico("05_top_vias.png", carpeta_tipo)

    # Circular por gravedad para cada tipo.
    grafico_circular(
        datos_tipo["GRAVEDAD"].fillna("SIN DATO")
        .value_counts()
        .rename_axis("GRAVEDAD")
        .reset_index(name="ACCIDENTES"),
        "GRAVEDAD",
        "ACCIDENTES",
        f"{tipo}: distribución por gravedad",
        "06_circular_gravedad.png",
        carpeta_tipo
    )

    # Circular por clase de accidente para cada tipo.
    grafico_circular(
        datos_tipo["CLASE_ACC"].fillna("SIN DATO")
        .value_counts()
        .rename_axis("CLASE_ACC")
        .reset_index(name="ACCIDENTES"),
        "CLASE_ACC",
        "ACCIDENTES",
        f"{tipo}: distribución por clase de accidente",
        "07_circular_clase_accidente.png",
        carpeta_tipo
    )

    # Circular por año.
    grafico_circular(
        tabla_anio,
        "ANO_OCURRENCIA_ACC",
        "ACCIDENTES",
        f"{tipo}: distribución porcentual por año",
        "08_circular_anio.png",
        carpeta_tipo
    )

    # Circular por franja horaria.
    tabla_franja_tipo = tabla_hora.copy()
    tabla_franja_tipo["FRANJA_HORARIA"] = tabla_franja_tipo["HORA_NUM"].astype(int).apply(franja_horaria)
    tabla_franja_tipo = (
        tabla_franja_tipo.groupby("FRANJA_HORARIA", sort=False)["ACCIDENTES"]
        .sum().reindex(["00-05", "06-08", "09-11", "12-14", "15-17", "18-20", "21-23"], fill_value=0)
        .rename_axis("FRANJA_HORARIA")
        .reset_index()
    )
    grafico_circular(
        tabla_franja_tipo,
        "FRANJA_HORARIA",
        "ACCIDENTES",
        f"{tipo}: distribución por franja horaria",
        "09_circular_franja_horaria.png",
        carpeta_tipo
    )

    # Circular por día.
    grafico_circular(
        tabla_dia,
        "DIA_SEMANA",
        "ACCIDENTES",
        f"{tipo}: distribución por día de la semana",
        "10_circular_dia.png",
        carpeta_tipo
    )

    # Circular por localidad: Top 10 + otros.
    tabla_loc_circular = (
        datos_tipo["LOCALIDAD"].fillna("SIN DATO").value_counts()
        .rename_axis("LOCALIDAD").reset_index(name="ACCIDENTES")
    )
    grafico_circular_top(
        tabla_loc_circular, "LOCALIDAD", "ACCIDENTES",
        f"{tipo}: distribución por localidad (Top 10 + otros)",
        "11_circular_localidad.png", carpeta_tipo, top_n=10
    )

    # Circular por vía: Top 10 + otras.
    tabla_via_circular = datos_tipo["MVINOMBRE"].dropna().value_counts()
    tabla_via_circular = tabla_via_circular[
        ~tabla_via_circular.index.astype(str).str.upper().isin(["SIN_NMG", "SIN NMG", "SIN NOMBRE"])
    ].rename_axis("MVINOMBRE").reset_index(name="ACCIDENTES")
    grafico_circular_top(
        tabla_via_circular, "MVINOMBRE", "ACCIDENTES",
        f"{tipo}: distribución por vía (Top 10 + otras)",
        "12_circular_via.png", carpeta_tipo, top_n=10
    )

# ============================================================
# 29. MATRICES DE COMPARACIÓN ENTRE VEHÍCULOS
# ============================================================

hora_tipo = pd.crosstab(
    acc_micro["HORA_NUM"],
    acc_micro["TIPO_MICROMOVILIDAD"]
).reindex(range(24), fill_value=0)

guardar_tabla(hora_tipo.reset_index(), "18_comparacion_hora_tipo.csv")

dia_tipo = pd.crosstab(
    acc_micro["DIA_SEMANA"],
    acc_micro["TIPO_MICROMOVILIDAD"]
).reindex(orden_dias, fill_value=0)

guardar_tabla(dia_tipo.reset_index(), "19_comparacion_dia_tipo.csv")

localidad_tipo = pd.crosstab(
    acc_micro["LOCALIDAD"],
    acc_micro["TIPO_MICROMOVILIDAD"]
)

guardar_tabla(
    localidad_tipo.reset_index(),
    "20_comparacion_localidad_tipo.csv"
)

# ============================================================
# 30. COORDENADAS
# ============================================================

coordenadas_validas = acc_micro[
    acc_micro["LATITUD"].between(3.5, 5.0)
    & acc_micro["LONGITUD"].between(-75.0, -73.0)
].copy()

print("\n" + "=" * 70)
print("COORDENADAS")
print("=" * 70)
print(
    f"Accidentes con coordenadas potencialmente válidas: "
    f"{len(coordenadas_validas):,}"
)
print(
    f"Porcentaje: "
    f"{len(coordenadas_validas) / len(acc_micro) * 100:.2f}%"
)

# ============================================================
# 31. RESUMEN EJECUTIVO AUTOMÁTICO
# ============================================================

total_micro = len(acc_micro)

top_hora = por_hora.loc[por_hora["ACCIDENTES"].idxmax()]
top_dia = por_dia.loc[por_dia["ACCIDENTES"].idxmax()]
top_localidad = por_localidad.iloc[0]
top_via = por_via.iloc[0] if len(por_via) > 0 else None
top_clase = por_clase_acc.iloc[0]
top_gravedad = por_gravedad.iloc[0]

resumen = pd.DataFrame({
    "INDICADOR": [
        "Accidentes de micromovilidad",
        "Hora con más accidentes",
        "Accidentes en hora pico",
        "Porcentaje de accidentes en hora pico",
        "Día con más accidentes",
        "Accidentes en día pico",
        "Porcentaje en día pico",
        "Localidad con más accidentes",
        "Accidentes en localidad principal",
        "Porcentaje en localidad principal",
        "Vía con más accidentes",
        "Accidentes en vía principal",
        "Tipo de accidente predominante",
        "Accidentes del tipo predominante",
        "Porcentaje del tipo predominante",
        "Gravedad predominante",
        "Accidentes de gravedad predominante",
        "Porcentaje de gravedad predominante",
        "Accidentes con bicicleta",
        "Porcentaje con bicicleta"
    ],
    "VALOR": [
        total_micro,
        int(top_hora["HORA_NUM"]),
        int(top_hora["ACCIDENTES"]),
        porcentaje(top_hora["ACCIDENTES"], total_micro),
        top_dia["DIA_SEMANA"],
        int(top_dia["ACCIDENTES"]),
        porcentaje(top_dia["ACCIDENTES"], total_micro),
        top_localidad["LOCALIDAD"],
        int(top_localidad["ACCIDENTES"]),
        porcentaje(top_localidad["ACCIDENTES"], total_micro),
        top_via["MVINOMBRE"] if top_via is not None else "SIN DATO",
        int(top_via["ACCIDENTES"]) if top_via is not None else 0,
        top_clase["CLASE_ACC"],
        int(top_clase["ACCIDENTES"]),
        porcentaje(top_clase["ACCIDENTES"], total_micro),
        top_gravedad["GRAVEDAD"],
        int(top_gravedad["ACCIDENTES"]),
        porcentaje(top_gravedad["ACCIDENTES"], total_micro),
        accidentes_bicicleta,
        porcentaje(accidentes_bicicleta, total_micro)
    ]
})

guardar_tabla(resumen, "00_RESUMEN_EJECUTIVO.csv")

# ============================================================
# 32. DATASET LIMPIO A NIVEL DE ACCIDENTE
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
    "21_dataset_micromovilidad_2018_2026.csv"
)

# ============================================================
# 33. REPORTE DE CALIDAD
# ============================================================

reporte_calidad = pd.DataFrame({
    "VARIABLE": dataset_final.columns,
    "TIPO_DATO": dataset_final.dtypes.astype(str).values,
    "NULOS": dataset_final.isna().sum().values,
    "PORCENTAJE_NULOS": (
        dataset_final.isna().sum() / len(dataset_final) * 100
    ).round(3),
    "VALORES_UNICOS": [
        dataset_final[c].nunique(dropna=True)
        for c in dataset_final.columns
    ]
})

guardar_tabla(
    reporte_calidad,
    "22_reporte_calidad_dataset_final.csv"
)

# ============================================================
# 34. MENSAJE FINAL
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
 - Accidentes con bicicleta: {accidentes_bicicleta:,} ({porcentaje(accidentes_bicicleta, total_micro):.2f}%)

Los resultados fueron guardados en:
{CARPETA_SALIDA}/
""")
