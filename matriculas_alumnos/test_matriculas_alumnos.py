from dominio.alumno import Alumno
from servicio.alumnos_matriculados import AlumnosMatriculados

def mostrar_menu():
    print("\n--- Menú ---")
    print("1. Matricular alumno")
    print("2. Listar alumnos")
    print("3. Eliminar archivo de alumnos")
    print("4. Salir")

def main():
    while True:
        mostrar_menu()
        opcion = input("Selecciona una opción: ")

        if opcion == "1":
            nombre = input("Introduce el nombre del alumno: ")
            alumno = Alumno(nombre)
            AlumnosMatriculados.matricular_alumno(alumno)

        elif opcion == "2":
            alumnos = AlumnosMatriculados.listar_alumnos()
            if alumnos:
                print("\nAlumnos matriculados:")
                for a in alumnos:
                    print(a.strip())
            else:
                print("No hay alumnos matriculados.")

        elif opcion == "3":
            AlumnosMatriculados.eliminar_alumnos()
            print("Archivo de alumnos eliminado (si existía).")

        elif opcion == "4":
            print("Saliendo...")
            break

        else:
            print("Opción no válida. Intenta de nuevo.")

if __name__ == "__main__":
    main()
