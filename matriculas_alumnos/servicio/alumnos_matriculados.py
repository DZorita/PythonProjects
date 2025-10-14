from dominio.alumno import Alumno

class AlumnosMatriculados:
    ruta_archivo: str = "alumnos.txt"

    @staticmethod
    def matricular_alumno(alumno: Alumno):
        with open(AlumnosMatriculados.ruta_archivo, "a", encoding="utf-8") as f:
            f.write(f"{alumno}\n")

    @staticmethod
    def listar_alumnos():
        try:
            with open(AlumnosMatriculados.ruta_archivo, "r", encoding="utf-8") as f:
                return f.readlines()
        except FileNotFoundError:
            return []

    @staticmethod
    def eliminar_alumnos():
        import os
        if os.path.exists(AlumnosMatriculados.ruta_archivo):
            os.remove(AlumnosMatriculados.ruta_archivo)
