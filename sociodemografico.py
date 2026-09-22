import os
import geopandas as gpd
import pandas as pd

# -------------------------------------------------------------------------
# Configuración de Archivos de Entrada y Salida
# -------------------------------------------------------------------------
ARCHIVO_SHP_AGEB = "shp/2025_1_19_A.shp"
CSV_CENSO_INEGI = "cpv2020.csv"
SALIDA_GEOJSON_SOCIODEMOGRAFICO = "sociodemografico_ageb.geojson"


def cargar_datos_censales(ruta_csv):
    """Carga y filtra los datos censales a nivel total de AGEB (MZA == '000')."""
    if not os.path.exists(ruta_csv):
        raise FileNotFoundError(f"No se encontró el archivo censal en: {ruta_csv}")

    print("Cargando datos del Censo INEGI...")
    df = pd.read_csv(
        ruta_csv, 
        dtype={'ENTIDAD': str, 'MUN': str, 'LOC': str, 'AGEB': str, 'MZA': str}
    )

    # Filter solo el resumen total de la AGEB
    if 'MZA' in df.columns:
        df = df[df['MZA'] == '000'].copy()

    # Excluir registros agregados a nivel municipal o estatal
    df = df[df['AGEB'] != '0000'].copy()

    # Construir clave CVEGEO_CENSO (13 dígitos)
    df['CVEGEO_CENSO'] = (
        df['ENTIDAD'].str.zfill(2) +
        df['MUN'].str.zfill(3) +
        df['LOC'].str.zfill(4) +
        df['AGEB'].str.zfill(4)
    )

    # Limpieza de columnas sociodemográficas
    columnas_interes = ['POBTOT', 'P_0A2', 'P_3A5', 'P_60YMAS', 'PCON_DISC']
    for col in columnas_interes:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        else:
            df[col] = 0

    # Indicador de niños de 0 a 5 años
    df['NIÑOS_0A5'] = df['P_0A2'] + df['P_3A5']

    df.rename(columns={
        'POBTOT': 'POBLACION_TOTAL',
        'P_60YMAS': 'ADULTOS_MAYORES',
        'PCON_DISC': 'PERSONAS_DISCAPACIDAD'
    }, inplace=True)

    cols_exportar = ['CVEGEO_CENSO', 'POBLACION_TOTAL', 'NIÑOS_0A5', 'ADULTOS_MAYORES', 'PERSONAS_DISCAPACIDAD']
    return df[cols_exportar]


def generar_geojson_sociodemografico():
    df_censo = cargar_datos_censales(CSV_CENSO_INEGI)
    print(f"Registros de AGEB procesados: {len(df_censo)}")

    print("Cargando Shapefile de AGEBs...")
    gdf_ageb = gpd.read_file(ARCHIVO_SHP_AGEB)

    if gdf_ageb.crs is None:
        raise ValueError("El Shapefile no tiene un CRS definido.")
    
    gdf_ageb = gdf_ageb.to_crs("EPSG:4326")

    # Identificar columna clave del Shapefile
    posibles_llaves = ['CVEGEO', 'CVE_AGEB', 'CODIGO']
    col_cve = next((col for col in posibles_llaves if col in gdf_ageb.columns), gdf_ageb.columns[0])
    gdf_ageb['CVEGEO_SHP'] = gdf_ageb[col_cve].astype(str).str.zfill(13)

    print("Realizando la unión espacial-tabular...")
    gdf_resultado = gdf_ageb.merge(
        df_censo, 
        left_on='CVEGEO_SHP', 
        right_on='CVEGEO_CENSO', 
        how='inner'
    )

    print(f"Polígonos coincidentes: {len(gdf_resultado)}")

    if len(gdf_resultado) == 0:
        print("ERROR: No hubo coincidencias en la clave CVEGEO.")
        return

    # Asignar CVEGEO final limpia
    gdf_resultado['CVEGEO'] = gdf_resultado['CVEGEO_SHP']

    # Filtrar geometrías inválidas
    gdf_resultado = gdf_resultado[gdf_resultado.geometry.notnull() & ~gdf_resultado.geometry.is_empty]

    columnas_finales = [
        'CVEGEO', 
        'POBLACION_TOTAL', 
        'NIÑOS_0A5', 
        'ADULTOS_MAYORES', 
        'PERSONAS_DISCAPACIDAD', 
        'geometry'
    ]
    
    gdf_final = gpd.GeoDataFrame(gdf_resultado[columnas_finales], geometry='geometry', crs="EPSG:4326")
    gdf_final.to_file(SALIDA_GEOJSON_SOCIODEMOGRAFICO, driver="GeoJSON")
    print(f"GeoJSON generado exitosamente: {SALIDA_GEOJSON_SOCIODEMOGRAFICO} ({len(gdf_final)} polígonos)")


if __name__ == "__main__":
    generar_geojson_sociodemografico()