import csv

with open("Notas_Alumnos_UF1.csv", newline='', encoding='cp1252') as archivo_uf1:
    lector_uf1 = csv.DictReader(archivo_uf1, delimiter=';')
    datos_uf1 = {fila["Id"]: fila for fila in lector_uf1}

with open("Notas_Alumnos_UF2.csv", newline='', encoding='cp1252') as archivo_uf2:
    lector_uf2 = csv.DictReader(archivo_uf2, delimiter=';')
    datos_uf2 = {fila["Id"]: fila for fila in lector_uf2}


alumnos_combinados = []
for id_alumno in datos_uf1:
    alumno_uf1 = datos_uf1[id_alumno]
    alumno_uf2 = datos_uf2.get(id_alumno, {})

    alumno_final = {
        "Id": id_alumno,
        "Nombre": alumno_uf1["Nombre"],
        "Apellido": alumno_uf1["Apellidos"],
        "Nota_UF1": alumno_uf1["UF1"],
        "Nota_UF2": alumno_uf2.get("UF2", "")
    }

    alumnos_combinados.append(alumno_final)

with open("Notas_Alumnos.csv", mode='w', newline='', encoding='utf-8') as archivo_final:
    fieldnames = ["Id", "Nombre", "Apellido", "Nota_UF1", "Nota_UF2"]
    escritor = csv.DictWriter(archivo_final, fieldnames=fieldnames)
    escritor.writeheader()
    for alumno in alumnos_combinados:
        escritor.writerow(alumno)


