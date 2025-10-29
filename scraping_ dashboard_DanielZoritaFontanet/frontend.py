import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="Dashboard de Libros")

st.title("📚 Dashboard de 'Books to Scrape'")
st.write("Esta app visualiza los datos extraídos con BeautifulSoup.")

try:
    df = pd.read_csv("books.csv")

    min_price = float(df["price"].min())
    max_price = float(df["price"].max())

    selected_price_range = st.slider(
        "Seleccione la price de la libro",
        min_value=min_price,
        max_value=max_price,
        value=[min_price, max_price],
    )

    df_filtered = df[
        (df["price"] >= selected_price_range[0]) &
        (df["price"] <= selected_price_range[1])
        ]

    if df_filtered.empty:
        st.warning("No se encontraron libros con los filtros seleccionados.")
    else:
        st.header("Tabla de Libros Filtrados")
        st.write(f"Mostrando {len(df_filtered)} de {len(df)} libros.")
        st.dataframe(df_filtered, width='stretch')

        st.header("Gráfico Simple: Precio vs. Rating")
        st.write("Gráfico de dispersión de los libros filtrados.")

        st.bar_chart(
            df_filtered,
            x="price",
            y="rating"
        )

except FileNotFoundError:
    st.error("Error: No se encontró el archivo 'books.csv'.")
    st.write("Por favor, ejecuta primero el script `scraping.py` para generar los datos.")
except Exception as e:
    st.error(f"Ocurrió un error al cargar los datos: {e}")
