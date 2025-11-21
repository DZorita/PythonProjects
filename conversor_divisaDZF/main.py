import requests
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk, messagebox


class ConversorDivisasApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor BCE - Tiempo Real")
        self.root.geometry("450x350")

        # Variables de datos
        self.rates = {}
        self.date_updated = "Desconocida"

        # 1. Carga Automática de datos al iniciar [cite: 48]
        self.fetch_data()

        # 2. Configurar la Interfaz de Usuario (GUI) [cite: 54]
        self.setup_gui()

    def fetch_data(self):
        """Descarga y parsea el XML del Banco Central Europeo."""
        url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"  # [cite: 14]
        try:
            response = requests.get(url)
            if response.status_code == 200:
                # Parseo del XML [cite: 49]
                root = ET.fromstring(response.content)

                # Espacio de nombres del XML (necesario para encontrar los tags correctamente)
                ns = {'ns': 'http://www.ecb.int/vocabulary/2002-08-01/eurofxref'}

                # Buscar el nodo que contiene la fecha y los cubos de monedas
                cube_node = root.find('.//ns:Cube/ns:Cube', ns)

                if cube_node is not None:
                    self.date_updated = cube_node.get('time')  # [cite: 51]

                    # Añadimos el Euro base manualmente
                    self.rates = {'EUR': 1.0}

                    # Iterar sobre las monedas hijas
                    for child in cube_node:
                        currency = child.get('currency')
                        rate = child.get('rate')
                        if currency and rate:
                            self.rates[currency] = float(rate)  # [cite: 53]
                else:
                    messagebox.showerror("Error", "No se pudo encontrar la estructura de datos XML esperada.")
            else:
                messagebox.showerror("Error", "No se pudo conectar con el BCE.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error de conexión: {e}")

    def setup_gui(self):
        """Crea los elementos visuales de la ventana."""
        # Título y Fecha
        ttk.Label(self.root, text="Conversor de Divisas (BCE)", font=('Arial', 16, 'bold')).pack(pady=10)
        ttk.Label(self.root, text=f"Datos actualizados: {self.date_updated}", foreground="green").pack()  # [cite: 63]

        # Frame para el formulario
        form_frame = ttk.Frame(self.root, padding=20)
        form_frame.pack()

        # Campo Cantidad [cite: 55]
        ttk.Label(form_frame, text="Cantidad:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.amount_entry = ttk.Entry(form_frame)
        self.amount_entry.insert(0, "1")  # Valor por defecto
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5)

        # Listado de monedas ordenado
        currency_list = sorted(self.rates.keys())

        # Desplegable Moneda Origen [cite: 56]
        ttk.Label(form_frame, text="De:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.combo_from = ttk.Combobox(form_frame, values=currency_list, state="readonly")
        self.combo_from.set("EUR")
        self.combo_from.grid(row=1, column=1, padx=5, pady=5)

        # Desplegable Moneda Destino [cite: 58]
        ttk.Label(form_frame, text="A:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.combo_to = ttk.Combobox(form_frame, values=currency_list, state="readonly")
        self.combo_to.set("USD")
        self.combo_to.grid(row=2, column=1, padx=5, pady=5)

        # Botón de Calcular [cite: 60]
        ttk.Button(self.root, text="Calcular Conversión", command=self.calculate).pack(pady=10)

        # Resultado [cite: 62]
        self.result_label = ttk.Label(self.root, text="", font=('Arial', 14, 'bold'), foreground="#333")
        self.result_label.pack(pady=10)

    def calculate(self):
        """Realiza la conversión cruzada usando el Euro como puente."""
        try:
            # Validación de entrada numérica
            amount_str = self.amount_entry.get().replace(',', '.')  # Permitir coma decimal
            amount = float(amount_str)

            currency_from = self.combo_from.get()
            currency_to = self.combo_to.get()

            if currency_from not in self.rates or currency_to not in self.rates:
                messagebox.showwarning("Aviso", "Selecciona monedas válidas.")
                return

            # Lógica Matemática (Conversión Cruzada) [cite: 68-72]
            # Fórmula: (Cantidad / TasaOrigen) * TasaDestino
            rate_from = self.rates[currency_from]
            rate_to = self.rates[currency_to]

            # Primero convertimos a EUR (dividir por tasa origen)
            amount_in_eur = amount / rate_from
            # Luego convertimos a la moneda final (multiplicar por tasa destino)
            final_result = amount_in_eur * rate_to

            self.result_label.config(text=f"{final_result:.2f} {currency_to}")

        except ValueError:
            messagebox.showerror("Error", "Por favor, introduce una cantidad numérica válida.")


# Punto de entrada de la aplicación
if __name__ == "__main__":
    root = tk.Tk()
    app = ConversorDivisasApp(root)
    root.mainloop()