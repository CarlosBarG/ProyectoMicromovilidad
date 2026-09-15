# EDA de Siniestros Viales de Micromovilidad en Bogotá

Este proyecto realiza un **Análisis Exploratorio de Datos (EDA)** sobre los siniestros viales registrados en Bogotá durante el periodo **2018-2026**, con énfasis en vehículos de micromovilidad.

Las categorías consideradas son:

- BICICLETA
- MOTOCICLO
- MOTOTRICICLO

El análisis permite identificar patrones relacionados con el año, hora, día, mes, localidad, barrio, vías, tipo de accidente y gravedad.

## Archivos necesarios

Para ejecutar el proyecto se deben tener los siguientes archivos en la **misma carpeta**:

```text
EDA_micromovilidad_2018_2026.py
ACCIDENTE.csv
VM_ACC_VEHICULO.csv
```

## Requisitos

Se necesita tener instalado Python 3.10 o superior.
Las principales librerías utilizadas son:

- `pandas`
- `numpy`
- `matplotlib`
- `seaborn`

### Instalación de librerías

Abrir una terminal en la carpeta del proyecto y ejecutar:

```bash
pip install pandas numpy matplotlib seaborn
```

Si el comando anterior no funciona, utilizar:

```bash
python -m pip install pandas numpy matplotlib seaborn
```

## Ejecución

Ubicarse mediante la terminal en la carpeta donde se encuentran los archivos.

### Windows

```cmd
python EDA_micromovilidad_2018_2026.py
```

También se puede ejecutar con:

```cmd
py EDA_micromovilidad_2018_2026.py
```

### Linux / macOS

```bash
python3 EDA_micromovilidad_2018_2026.py
```

## Resultados

Al finalizar la ejecución se generará automáticamente la carpeta:

```text
EDA_MICROMOVILIDAD_2018_2026/
```

Esta carpeta contiene los resultados del análisis, incluyendo:

- Gráficos de barras.
- Gráficos de líneas.
- Diagramas circulares.
- Mapas de calor.
- Tablas de resultados en formato CSV.
- Dataset limpio de accidentes de micromovilidad.
- Reporte de calidad de los datos.
- Resumen ejecutivo.

## Consideraciones sobre los datos

- El programa utiliza `FORMULARIO` como llave para relacionar los accidentes con los vehículos, debido a que un accidente puede involucrar varios vehículos.
- Por esta razón, los accidentes de micromovilidad se contabilizan utilizando registros únicos de `FORMULARIO`, evitando contar varias veces un mismo accidente.
- El análisis se limita al periodo 2018-2026.

> **Nota:** El año 2026 corresponde a un periodo parcial, por lo que sus valores deben interpretarse con precaución al compararlos con años completos.

## Estructura esperada del proyecto

```text
Proyecto/
│
├── EDA_micromovilidad_2018_2026.py
├── ACCIDENTE.csv
├── VM_ACC_VEHICULO.csv
│
└── EDA_MICROMOVILIDAD_2018_2026/
    ├── gráficos/
    ├── tablas CSV
    ├── dataset limpio
    └── reporte de calidad
```
