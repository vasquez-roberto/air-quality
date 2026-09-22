# Air Quality & Sociodemographic Mapping Platform (Monterrey Metropolitan Area)

Sistema automatizado en Python para el monitoreo, la interpolación espacial de la calidad del aire ($PM_{2.5}$ y $PM_{10}$) y la integración de indicadores sociodemográficos por AGEB (Censo de Población y Vivienda 2020 - INEGI).

---

## Descripción del Proyecto

El objetivo de este proyecto es analizar la exposición a contaminantes atmosféricos en poblaciones vulnerables dentro del Área Metropolitana de Monterrey.

El pipeline ejecuta las siguientes fases principales:
1. **Captura de datos**: Consulta en tiempo real la API de **PurpleAir** utilizando los sensores registrados en la zona.
2. **Depuración**: Valida y descarta lecturas atípicas o erróneas basadas en los límites normativos de la EPA.
3. **Interpolación espacial**: Construye superficies continuas de concentración de contaminantes mediante **Triangulación Delaunay**.
4. **Cruce geográfico e integración censal**: Mapea la información a nivel de **AGEB urbana** (Área Geoestadística Básica del INEGI) uniendo los datos de calidad del aire con la información sociodemográfica extraída del Censo de Población y Vivienda 2020 (`cpv2020.csv`).

Como resultado, se exportan archivos **GeoJSON enriquecidos**, listos para desplegar en visores GIS (ArcGIS, QGIS, Mapbox, Leaflet). Al seleccionar o hacer clic sobre cualquier polígono, el visor despliega tanto el **valor interpolado del contaminante** como la **tabla de datos sociodemográficos** de la población residente.

---

## 🛠️ Funcionalidades Principales

- **Monitoreo en Tiempo Real**: Consulta automática a la API de PurpleAir para obtener lecturas actualizadas de $PM_{1.0}$ y $PM_{2.5}$.
- **Generación de Histórico**: Guardado acumulativo de lecturas válidas en un archivo `historico.csv` para análisis de series de tiempo.
- **Interpolación Lineal Integrada**: Asignación de concentraciones promedio a polígonos que contienen sensores e interpolación basada en la malla Delaunay para polígonos intermedios.
- **Enriquecimiento Socioambiental**: Cruce directo con la base de datos censal de INEGI para calcular niños de 0 a 5 años, adultos mayores y personas con discapacidad por AGEB.
- **Salidas WebGIS Listas**: Exportación directa a GeoJSON con proyecciones estandarizadas en WGS84 (`EPSG:4326`).

---

## Variables Integradas por AGEB

Cada polígono en las capas `AQ_PM25.geojson` y `AQ_PM10.geojson` contiene los siguientes atributos dentro de su propiedad `properties`:

| Atributo | Tipo | Descripción | Fuente |
| :--- | :--- | :--- | :--- |
| `CVEGEO` | String | Clave geográfica única de la AGEB (13 dígitos) | INEGI / SHP |
| `valor_interpolado` | Float | Concentración interpolada del contaminante ($\mu g/m^3$) | Interpolación Delaunay |
| `AQ` | String | Categoría de calidad del aire (*Bueno, Aceptable, Mala, etc.*) | Norma de Calidad del Aire |
| `POBLACION_TOTAL` | Integer | Población total residente en la AGEB (`POBTOT`) | CPV 2020 (INEGI) |
| `NIÑOS_0A5` | Integer | Población infantil de 0 a 5 años (`P_0A2` + `P_3A5`) | CPV 2020 (INEGI) |
| `ADULTOS_MAYORES` | Integer | Población de 60 años y más (`P_60YMAS`) | CPV 2020 (INEGI) |
| `PERSONAS_DISCAPACIDAD` | Integer | Población con alguna discapacidad (`PCON_DISC`) | CPV 2020 (INEGI) |
| `timestamp` | String | Fecha y hora UTC del procesamiento y lectura | Sistema |

---

## Estructura del Repositorio

```text
.
├── shp/
│   ├── 2025_1_19_A.shp          # Shapefile de AGEBs urbanas (INEGI)
│   ├── 2025_1_19_A.prj          # Archivo de proyección geográfica
│   └── ...
├── conjunto_de_datos_ageb_urbana_19_cpv2020.csv  # Base de datos censal de INEGI (cpv2020.csv)
├── sensores_detectados.csv      # Catálogo de sensores PurpleAir (ID, Latitud, Longitud)
├── .env                         # Claves y variables de entorno (API Key)
├── main.py                      # Script principal de captura, interpolación y cruce
├── sociodemografico.py          # Script auxiliar para generación de la capa base de censo
├── AQ_PM25.geojson              # Capa enriquecida final de PM2.5
├── AQ_PM10.geojson              # Capa enriquecida final de PM10
├── sensores.geojson             # Ubicación puntual de sensores procesados
└── historico.csv                # Histórico de lecturas registradas
