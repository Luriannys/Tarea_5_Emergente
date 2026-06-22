import pandas as pd

def mostrar_city(df: pd.DataFrame):
    print(df.to_string())

def agregar_zona(df: pd.DataFrame, tipo: str, inicio_x: str, inicio_y: int):
    tipo = tipo * 3
    columnas = list(df.columns)
    ind_col_base= columnas.index(inicio_x)

    columna = columnas[ind_col_base]
    for i in range(3):
        df.loc[inicio_y+i, columna] = tipo


city_df = pd.read_csv('city.csv', index_col=0)
mostrar_city(city_df)
city_df = city_df.fillna("   ")
agregar_zona(city_df, 'r', "AB", 10)

mostrar_city(city_df)

agregar_zona(city_df, 'i', "J", 13)

mostrar_city(city_df)

agregar_zona(city_df, 'c', "T", 2)

mostrar_city(city_df)