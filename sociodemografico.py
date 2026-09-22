import os
import geopandas as gpd
import pandas as pd

# -------------------------------------------------------------------------
# Configuración de Archivos de Entrada y Salida
# -------------------------------------------------------------------------
# 1. Shapefile con los polígonos de AGEBs (Marco Geoestadístico INEGI)
ARCHIVO_SHP_AGEB = "shp/2025_1_19_A.shp"

# 2. CSV del Censo de Población y Vivienda a nivel AGEB/Manzana (INEGI)
CSV_CENSO_INEGI = "cpv2020.csv"

# 3. GeoJSON de salida exclusivo para datos sociodemográficos
SALIDA_GEOJSON_SOCIODEMOGRAFICO = "sociodemografico_ageb.geojson"


def cargar_datos_censales(ruta_csv):
    """Llee el CSV del Censo INEGI, filtra a nivel AGEB y extrae datos de población."""
    if not os.path.exists(ruta_csv):
        raise FileNotFoundError(f"No se encontró el archivo censal en: {ruta_csv}")

    print("Cargando y procesando datos del Censo INEGI...")
    df = pd.read_csv(ruta_csv, dtype={'ENTIDAD': str, 'MUN': str, 'LOC': str, 'AGEB': str})

    # Filtrar solo el resumen por AGEB (en INEGI la manzana '000' es el acumulado de la AGEB)
    if 'MZA' in df.columns:
        df = df[df['MZA'] == '000']

    # Crear clave geográfica estandarizada CVEGEO (13 dígitos)
    df['CVEGEO'] = (
        df['ENTIDAD'].str.zfill(2) +
        df['MUN'].str.zfill(3) +
        df['LOC'].str.zfill(4) +
        df['AGEB'].str.zfill(4)
    )

    # Seleccionar columnas sociodemográficas de interés
    columnas_interes = ['CVEGEO', 'POBTOT', 'P_0A2', 'P_3A5', 'P_60YMAS', 'PCON_DISC']
    df_sub = df[columnas_interes].copy()

    # Limpiar y convertir a enteros
    for col in ['POBTOT', 'P_0A2', 'P_3A5', 'P_60YMAS', 'PCON_DISC']:
        df_sub[col] = pd.to_numeric(df_sub[col], errors='coerce').fillna(0).astype(int)

    # Agrupar rango de niños de 0 a 5 años
    df_sub['NIÑOS_0A5'] = df_sub['P_0A2'] + df_sub['P_3A5']

    # Renombrar columnas para facilitar su uso en ArcGIS
    df_sub.rename(columns={
        'POBTOT': 'POBLACION_TOTAL',
        'P_60YMAS': 'ADULTOS_MAYORES',
        'PCON_DISC': 'PERSONAS_DISCAPACIDAD'
    }, inplace=True)

    return df_sub[['CVEGEO', 'POBLACION_TOTAL', 'NIÑOS_0A5', 'ADULTOS_MAYORES', 'PERSONAS_DISCAPACIDAD']]


def generar_geojson_sociodemografico():
    # 1. Cargar datos del Censo
    df_censo = cargar_datos_censales(CSV_CENSO_INEGI)

    # 2. Cargar Shapefile de AGEBs y asegurar proyección WGS84 (EPSG:4326)
    print("Cargando geometría de polígonos AGEB...")
    gdf_ageb = gpd.read_file(ARCHIVO_SHP_AGEB)
    
    if gdf_ageb.crs is None:
        raise ValueError("El archivo Shapefile no cuenta con un sistema de coordenadas (.prj) definido.")
    
    gdf_ageb = gdf_ageb.to_crs("EPSG:4326")

    # Identificar la columna que contiene la clave geográfica (CVEGEO)
    # Si la columna no se llama 'CVEGEO', toma la primera columna de texto del SHP
    col_cve = 'CVEGEO' if 'CVEGEO' in gdf_ageb.columns else gdf_ageb.columns[0]
    gdf_ageb['CVEGEO'] = gdf_ageb[col_cve].astype(str)

    # 3. Unir geometría con datos censales por CVEGEO
    print("Uniendo geometría con datos del Censo...")
    gdf_resultado = gdf_ageb.merge(df_censo, on='CVEGEO', how='inner')

    # 4. Seleccionar columnas finales y exportar GeoJSON
    columnas_finales = [
        'CVEGEO',
        'POBLACION_TOTAL',
        'NIÑOS_0A5',
        'ADULTOS_MAYORES',
        'PERSONAS_DISCAPACIDAD',
        'geometry'
    ]
    
    gdf_resultado = gdf_resultado[columnas_finales]
    gdf_resultado.to_file(SALIDA_GEOJSON_SOCIODEMOGRAFICO, driver="GeoJSON")
    
    print(f"GeoJSON sociodemográfico generado exitosamente ({len(gdf_resultado)} polígonos): {SALIDA_GEOJSON_SOCIODEMOGRAFICO}")


if __name__ == "__main__":
    generar_geojson_sociodemografico()