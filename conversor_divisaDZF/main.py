import requests
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk, messagebox

tasas = {'EUR': 1.0}

def actualizar_tasas():
    url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
    try:
        respuesta = requests.get(url)
        arbol = ET.fromstring(respuesta.content)
        ns = {'ns': 'http://www.ecb.int/vocabulary/2002-08-01/eurofxref'}
        cubo = arbol.find('.//ns:Cube/ns:Cube', ns)

        for nodo in cubo:
            moneda = nodo.get('currency')
            valor = float(nodo.get('rate'))
            tasas[moneda] = valor
            
    except Exception:
        messagebox.showerror("Error", "No se pudieron descargar las tasas.")

def calcular():
    try:
        cantidad = float(entrada_cantidad.get())
        origen = combo_de.get()
        destino = combo_a.get()

        resultado = (cantidad / tasas[origen]) * tasas[destino]

        etiqueta_resultado.config(text=f"{resultado:.2f} {destino}")

    except ValueError:
        messagebox.showwarning("Error", "Por favor escribe un número válido.")

root = tk.Tk()
root.title("Conversor Simple")
root.geometry("300x350")

actualizar_tasas()
lista_monedas = sorted(tasas.keys())

tk.Label(root, text="Cantidad:", font=("Arial", 10)).pack(pady=5)
entrada_cantidad = tk.Entry(root)
entrada_cantidad.pack(pady=5)

tk.Label(root, text="De:", font=("Arial", 10)).pack(pady=5)
combo_de = ttk.Combobox(root, values=lista_monedas, state="readonly")
combo_de.set("EUR")
combo_de.pack(pady=5)

tk.Label(root, text="A:", font=("Arial", 10)).pack(pady=5)
combo_a = ttk.Combobox(root, values=lista_monedas, state="readonly")
combo_a.set("USD")
combo_a.pack(pady=5)

tk.Button(root, text="CONVERTIR", command=calcular, bg="#dddddd").pack(pady=20)

etiqueta_resultado = tk.Label(root, text="0.00", font=("Arial", 16, "bold"), fg="blue")
etiqueta_resultado.pack(pady=10)

root.mainloop()