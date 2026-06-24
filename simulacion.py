import json
import math
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


COLUMNAS = 29
FILAS = 16
ANCHO_CELDA = 3
NIVEL_MAXIMO = 27
DISTANCIA_ZONAS = 10

RESIDENCIAL = "r"
COMERCIAL = "c"
INDUSTRIAL = "i"
TIPOS_ZONA = {RESIDENCIAL, COMERCIAL, INDUSTRIAL}


@dataclass
class Zona:
    fila: int
    col: int
    tipo: str
    nivel: int = 1
    decrecio: bool = False


class Celda:

    def __init__(self):
        self.texto_zona = "   "
        self.es_zona = False
        self.tipo_zona: Optional[str] = None
        self.nivel_zona = 0
        self.arteria_horizontal = False
        self.arteria_vertical = False
        self.trafico = 0
        self.trafico_anterior = 0

    @property
    def es_arteria(self) -> bool:
        return self.arteria_horizontal or self.arteria_vertical

    @property
    def ocupada(self) -> bool:
        return self.es_zona or self.es_arteria

    def render(self) -> str:
        if not self.es_arteria:
            if self.es_zona:
                return self.texto_zona
            return "   "
        
        tiene_trafico = self.trafico > 1
        t_str = str(self.trafico) if tiene_trafico else None

        # Intersección
        if self.arteria_horizontal and self.arteria_vertical:
            return f":{t_str}:" if tiene_trafico else ":+:"
        
        # Arteria Horizontal
        if self.arteria_horizontal:
            return t_str * 3 if tiene_trafico else "==="
        
        # Arteria Vertical
        if self.arteria_vertical:
            return f"|{t_str}|" if tiene_trafico else "| |"
        
        return "   "


class SimCity:
    def __init__(self):
        self.grid: List[List[Celda]] = []
        self.zonas: List[Zona] = []
        self.tick_actual = 0
        self.inicializar_grid()

    def inicializar_grid(self):
        #Reinicia la ciudad a una cuadricula vacia.#
        self.grid = [[Celda() for _ in range(COLUMNAS)] for _ in range(FILAS)]
        self.zonas = []
        self.tick_actual = 0

    def coordenada_a_indices(self, coord: str) -> Tuple[int, int]:
        #Convierte una coordenada estilo Excel a indices.#
        match = re.fullmatch(r"([A-Z]+)(\d+)", coord.strip().upper())
        if not match:
            raise ValueError(f"Coordenada invalida: {coord}")

        letras, numero = match.groups()
        col = 0
        for char in letras:
            col = col * 26 + (ord(char) - ord("A") + 1)
        col -= 1

        fila = int(numero) - 1
        if fila < 0 or fila >= FILAS or col < 0 or col >= COLUMNAS:
            raise ValueError(f"Coordenada fuera de rango: {coord}")

        return fila, col

    def indices_a_coordenada(self, fila: int, col: int) -> str:
        #Convierte indices internos a coordenadas estilo Excel.#
        if fila < 0 or fila >= FILAS or col < 0 or col >= COLUMNAS:
            raise ValueError(f"Indices fuera de rango: ({fila}, {col})")

        letras = ""
        numero_columna = col + 1
        while numero_columna > 0:
            numero_columna -= 1
            letras = chr(ord("A") + numero_columna % 26) + letras
            numero_columna //= 26

        return f"{letras}{fila + 1}"

    def render_zona(self, tipo: str, nivel: int, indice_celda: int) -> str:
        inicio = indice_celda * ANCHO_CELDA
        caracteres = []
        for offset in range(ANCHO_CELDA):
            posicion = inicio + offset + 1
            caracteres.append(tipo.upper() if posicion <= nivel else tipo)
        return "".join(caracteres)

    def actualizar_zona_en_grid(self, zona: Zona):
        for df in range(3):
            for dc in range(3):
                indice_celda = df * 3 + dc
                celda = self.grid[zona.fila + df][zona.col + dc]
                celda.es_zona = True
                celda.tipo_zona = zona.tipo
                celda.nivel_zona = zona.nivel
                celda.texto_zona = self.render_zona(zona.tipo, zona.nivel, indice_celda)

    def colocar_zona(self, coord: str, tipo: str) -> bool:
        tipo = tipo.lower()
        if tipo not in TIPOS_ZONA:
            print(f"Error: tipo de zona invalido: {tipo}")
            return False

        try:
            fila, col = self.coordenada_a_indices(coord)
        except ValueError as error:
            print(f"Error: {error}")
            return False

        if fila + 2 >= FILAS or col + 2 >= COLUMNAS:
            print(f"Error: La zona no cabe desde {coord}")
            return False

        for df in range(3):
            for dc in range(3):
                celda = self.grid[fila + df][col + dc]
                if celda.ocupada:
                    ocupada = self.indices_a_coordenada(fila + df, col + dc)
                    print(f"Error: La celda {ocupada} ya esta ocupada")
                    return False

        zona = Zona(fila=fila, col=col, tipo=tipo, nivel=1)
        self.zonas.append(zona)
        self.actualizar_zona_en_grid(zona)
        return True

    def colocar_arteria(self, inicio: str, fin: str) -> bool:
        try:
            fila1, col1 = self.coordenada_a_indices(inicio)
            fila2, col2 = self.fin_arteria_a_indices(fila1, col1, fin)
        except ValueError as error:
            print(f"Error: {error}")
            return False

        if fila1 != fila2 and col1 != col2:
            print("Error: Las arterias deben ser horizontales o verticales")
            return False

        horizontal = fila1 == fila2
        if horizontal:
            paso = [(fila1, col) for col in range(min(col1, col2), max(col1, col2) + 1)]
        else:
            paso = [(fila, col1) for fila in range(min(fila1, fila2), max(fila1, fila2) + 1)]

        # Las arterias pueden cruzar otras arterias, pero no pueden pisar zonas.
        for fila, col in paso:
            if self.grid[fila][col].es_zona:
                ocupada = self.indices_a_coordenada(fila, col)
                print(f"Error: La celda {ocupada} contiene una zona")
                return False

        for fila, col in paso:
            if horizontal:
                self.grid[fila][col].arteria_horizontal = True
            else:
                self.grid[fila][col].arteria_vertical = True

        return True

    def fin_arteria_a_indices(self, fila_inicio: int, col_inicio: int, fin: str) -> Tuple[int, int]:
        fin = fin.strip().upper()

        if re.fullmatch(r"[A-Z]+", fin):
            return fila_inicio, self.columna_a_indice(fin)
        if re.fullmatch(r"\d+", fin):
            fila = int(fin) - 1
            if fila < 0 or fila >= FILAS:
                raise ValueError(f"Fila fuera de rango: {fin}")
            return fila, col_inicio
        return self.coordenada_a_indices(fin)

    def columna_a_indice(self, letras: str) -> int:
        col = 0
        for char in letras:
            col = col * 26 + (ord(char) - ord("A") + 1)
        col -= 1
        if col < 0 or col >= COLUMNAS:
            raise ValueError(f"Columna fuera de rango: {letras}")
        return col

    def guardar(self, ruta: str):
        datos = {
            "filas": FILAS,
            "columnas": COLUMNAS,
            "tick_actual": self.tick_actual,
            "zonas": [zona.__dict__ for zona in self.zonas],
            "arterias": [
                {
                    "fila": fila,
                    "col": col,
                    "horizontal": celda.arteria_horizontal,
                    "vertical": celda.arteria_vertical,
                    "trafico": celda.trafico,
                    "trafico_anterior": celda.trafico_anterior,
                }
                for fila in range(FILAS)
                for col in range(COLUMNAS)
                for celda in [self.grid[fila][col]]
                if celda.es_arteria
            ],
        }

        try:
            with open(ruta, "w", encoding="utf-8") as archivo:
                json.dump(datos, archivo, indent=2)
            print(f"Ciudad guardada en {ruta}")
        except OSError as error:
            print(f"Error al guardar: {error}")

    def cargar(self, ruta: str):
        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
        except (OSError, json.JSONDecodeError) as error:
            print(f"Error al cargar: {error}")
            return

        self.inicializar_grid()
        self.tick_actual = int(datos.get("tick_actual", 0))

        for zona_data in datos.get("zonas", []):
            zona = Zona(
                fila=int(zona_data["fila"]),
                col=int(zona_data["col"]),
                tipo=zona_data["tipo"],
                nivel=int(zona_data.get("nivel", 1)),
                decrecio=bool(zona_data.get("decrecio", False)),
            )
            self.zonas.append(zona)
            self.actualizar_zona_en_grid(zona)

        for arteria in datos.get("arterias", []):
            fila = int(arteria["fila"])
            col = int(arteria["col"])
            if 0 <= fila < FILAS and 0 <= col < COLUMNAS and not self.grid[fila][col].es_zona:
                celda = self.grid[fila][col]
                celda.arteria_horizontal = bool(arteria.get("horizontal", False))
                celda.arteria_vertical = bool(arteria.get("vertical", False))
                celda.trafico = int(arteria.get("trafico", 0))
                celda.trafico_anterior = int(arteria.get("trafico_anterior", 0))

        print(f"Ciudad cargada desde {ruta}")

    def imprimir_grid(self):
        print("   ", end="")
        for col in range(COLUMNAS):
            etiqueta = self.indices_a_coordenada(0, col)[:-1]
            print(f"{etiqueta:^{ANCHO_CELDA}}", end="")
        print()

        for fila in range(FILAS):
            print(f"{fila + 1:2} ", end="")
            for col in range(COLUMNAS):
                print(self.grid[fila][col].render(), end="")
            print()

    def tick(self):
        self.tick_actual += 1
        print(f"\n=== TICK {self.tick_actual} ===")
        self.calcular_trafico()
        self.evaluar_zonas()
        self.actualizar_trafico_anterior()
        self.imprimir_grid()

    def calcular_trafico(self):
        for fila in range(FILAS):
            for col in range(COLUMNAS):
                if self.grid[fila][col].es_arteria:
                    self.grid[fila][col].trafico = 0

        for fila in range(FILAS):
            for col in range(COLUMNAS):
                celda = self.grid[fila][col]
                if celda.es_arteria:
                    trafico_celda = 0
                    for nf, nc in self.vecinos_ortogonales(fila, col):
                        vecino = self.grid[nf][nc]
                        if vecino.es_zona:
                            # Suma de las raíces cuadradas de los niveles de las zonas adyacentes
                            trafico_celda += int(math.sqrt(vecino.nivel_zona))
                    celda.trafico = trafico_celda

    def actualizar_trafico_anterior(self):
        for fila in range(FILAS):
            for col in range(COLUMNAS):
                celda = self.grid[fila][col]
                if celda.es_arteria:
                    celda.trafico_anterior = celda.trafico

    def evaluar_zonas(self):
        cambios = []
        for zona in self.zonas:
            crecimiento, decrecimiento = self.votos_zona(zona)
            nuevo_nivel = zona.nivel
            decrecio = False

            if crecimiento > decrecimiento and zona.nivel < NIVEL_MAXIMO:
                nuevo_nivel += 1
            elif decrecimiento > crecimiento and zona.nivel > 1:
                nuevo_nivel -= 1
                decrecio = True

            cambios.append((zona, nuevo_nivel, decrecio))

        for zona, nuevo_nivel, decrecio in cambios:
            zona.nivel = nuevo_nivel
            zona.decrecio = decrecio
            self.actualizar_zona_en_grid(zona)

    def votos_zona(self, zona: Zona) -> Tuple[int, int]:
        if zona.tipo == RESIDENCIAL:
            return self.votos_residencial(zona)
        if zona.tipo == COMERCIAL:
            return self.votos_comercial(zona)
        if zona.tipo == INDUSTRIAL:
            return self.votos_industrial(zona)
        return 0, 0

    def votos_residencial(self, zona: Zona) -> Tuple[int, int]:
        crecer = 0
        decrecer = 0
        arterias = self.arterias_adyacentes(zona)

        crecer += len(arterias)
        decrecer += 2 * sum(1 for fila, col in arterias if self.grid[fila][col].trafico > 5)

        industriales_cercanas = 0
        for otra in self.zonas_cercanas(zona):
            if otra.tipo == INDUSTRIAL:
                industriales_cercanas += 1
                if otra.nivel < 18:
                    crecer += 1
            elif otra.tipo == COMERCIAL:
                if otra.nivel > math.sqrt(zona.nivel):
                    crecer += 1
                if otra.decrecio:
                    decrecer += 2

        # El enunciado penaliza desde la 11a zona industrial cercana.
        decrecer += 2 * max(0, industriales_cercanas - 10)
        return crecer, decrecer

    def votos_comercial(self, zona: Zona) -> Tuple[int, int]:
        crecer = 0
        decrecer = 0

        for fila, col in self.arterias_adyacentes(zona):
            celda = self.grid[fila][col]
            if celda.trafico > 5:
                crecer += 1
            if celda.trafico < celda.trafico_anterior:
                decrecer += 2

        for otra in self.zonas_cercanas(zona):
            if otra.tipo == RESIDENCIAL:
                crecer += 1
                if otra.decrecio:
                    decrecer += 2
            elif otra.tipo == INDUSTRIAL:
                if otra.nivel > math.sqrt(zona.nivel):
                    crecer += 1
                if otra.decrecio:
                    decrecer += 2

        return crecer, decrecer

    def votos_industrial(self, zona: Zona) -> Tuple[int, int]:
        crecer = len(self.arterias_adyacentes(zona))
        decrecer = 0

        for otra in self.zonas_cercanas(zona):
            if otra.tipo == RESIDENCIAL:
                crecer += 1
                if otra.decrecio:
                    decrecer += 2
            elif otra.tipo == COMERCIAL:
                if otra.nivel > math.sqrt(zona.nivel):
                    crecer += 1
                if otra.decrecio:
                    decrecer += 2
            elif otra.tipo == INDUSTRIAL and otra.decrecio:
                decrecer += 2

        return crecer, decrecer

    def zonas_cercanas(self, zona: Zona) -> List[Zona]:
        return [
            otra
            for otra in self.zonas
            if otra is not zona and self.distancia_zonas(zona, otra) <= DISTANCIA_ZONAS
        ]

    def distancia_zonas(self, a: Zona, b: Zona) -> int:
        centro_a = (a.fila + 1, a.col + 1)
        centro_b = (b.fila + 1, b.col + 1)
        return max(abs(centro_a[0] - centro_b[0]), abs(centro_a[1] - centro_b[1]))

    def arterias_adyacentes(self, zona: Zona) -> List[Tuple[int, int]]:
        adyacentes = set()
        for df in range(3):
            for dc in range(3):
                fila = zona.fila + df
                col = zona.col + dc
                for nf, nc in self.vecinos_ortogonales(fila, col):
                    dentro_de_zona = zona.fila <= nf <= zona.fila + 2 and zona.col <= nc <= zona.col + 2
                    if not dentro_de_zona and self.grid[nf][nc].es_arteria:
                        adyacentes.add((nf, nc))
        return list(adyacentes)

    def vecinos_ortogonales(self, fila: int, col: int) -> List[Tuple[int, int]]:
        vecinos = []
        for df, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nf, nc = fila + df, col + dc
            if 0 <= nf < FILAS and 0 <= nc < COLUMNAS:
                vecinos.append((nf, nc))
        return vecinos

    def coord_desde_argumentos(self, partes: List[str], inicio: int) -> Tuple[str, int]:
        #Lee una coordenada que puede venir como C4 o separada como C 4.#
        if inicio >= len(partes):
            raise ValueError("Falta coordenada")

        actual = partes[inicio]
        if re.fullmatch(r"[A-Za-z]+\d+", actual):
            return actual, inicio + 1

        if inicio + 1 < len(partes) and re.fullmatch(r"[A-Za-z]+", partes[inicio]) and re.fullmatch(r"\d+", partes[inicio + 1]):
            return partes[inicio] + partes[inicio + 1], inicio + 2

        raise ValueError(f"Coordenada invalida: {actual}")

    def procesar_comando(self, comando: str):
        #Procesa comandos del usuario.#
        if not comando.strip():
            self.tick()
            return None

        partes = comando.strip().split()
        cmd = partes[0].lower()

        try:
            if cmd == "salir":
                return "salir"

            if cmd == "guardar":
                if len(partes) != 2:
                    print("Uso: guardar <ruta_archivo>")
                else:
                    self.guardar(partes[1])

            elif cmd == "cargar":
                if len(partes) != 2:
                    print("Uso: cargar <ruta_archivo>")
                else:
                    self.cargar(partes[1])

            elif cmd in TIPOS_ZONA:
                coord, siguiente = self.coord_desde_argumentos(partes, 1)
                if siguiente != len(partes):
                    print(f"Uso: {cmd} <celda>")
                else:
                    self.colocar_zona(coord, cmd)

            elif cmd == "a":
                inicio, siguiente = self.coord_desde_argumentos(partes, 1)
                if siguiente >= len(partes):
                    print("Uso: a <celda_inicio> <fin>")
                else:
                    fin = "".join(partes[siguiente:])
                    self.colocar_arteria(inicio, fin)

            else:
                print(f"Comando desconocido: {cmd}")

        except ValueError as error:
            print(f"Error: {error}")

        self.imprimir_grid()
        return None


def main():
    juego = SimCity()

    print("=" * 80)
    print("BIENVENIDO A SIMCITY 2526")
    print("=" * 80)
    print("Comandos:")
    print("  r <celda>          Crear zona residencial, ej. r C4")
    print("  c <celda>          Crear zona comercial, ej. c T2")
    print("  i <celda>          Crear zona industrial, ej. i J13")
    print("  a <inicio> <fin>   Crear arteria, ej. a C7 P o a F4 9")
    print("  guardar <archivo>  Guardar ciudad")
    print("  cargar <archivo>   Cargar ciudad")
    print("  salir              Salir")
    print("  [Enter]            Avanzar un tick")
    print()

    juego.imprimir_grid()

    while True:
        try:
            comando = input("\n> ")
            resultado = juego.procesar_comando(comando)
            if resultado == "salir":
                print("Gracias por jugar SimCity 2526.")
                break
        except KeyboardInterrupt:
            print("\nGracias por jugar SimCity 2526.")
            break


if __name__ == "__main__":
    main()
