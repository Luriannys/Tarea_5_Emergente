import os
import math
import re
from typing import List, Tuple, Optional, Dict, Set

# Constantes
ANCHO = 88  # Columnas (A a AA, AB, AC)
ALTO = 16   # Filas (1 a 16)
ANCHO_CELDA = 3  # Cada celda ocupa 3 caracteres

# Tipos de zonas
RESIDENCIAL = 'r'
COMERCIAL = 'c'
INDUSTRIAL = 'i'
VACIO = '.'

# Símbolos para arterias
HORIZONTAL = '='
VERTICAL = '|'
INTERSECCION = ':'

class Celda:
    """Representa una celda individual en la cuadrícula"""
    def __init__(self, contenido='.', nivel=0, es_zona=False, es_arteria=False):
        self.contenido = contenido  # Carácter mostrado
        self.nivel = nivel          # Nivel de crecimiento (0-27)
        self.es_zona = es_zona      # True si es una zona
        self.es_arteria = es_arteria # True si es arteria vial
        self.tipo_zona = None       # 'r', 'c', 'i' si es zona
        self.trafico = 0            # Nivel de tráfico (para arterias)
        self.trafico_anterior = 0   # Tráfico del tick anterior
        self.decrecio = False       # Si decreció en el tick anterior
        
    def __str__(self):
        if self.es_arteria:
            if self.trafico > 1 and self.contenido != INTERSECCION:
                return str(self.trafico)
            return self.contenido
        return self.contenido

class SimCity:
    def __init__(self):
        self.grid = [[Celda() for _ in range(ANCHO)] for _ in range(ALTO)]
        self.zonas = []  # Lista de zonas [(fila, col, tipo, nivel)]
        self.arterias = []  # Lista de arterias [(fila1, col1, fila2, col2, tipo)]
        self.tick_actual = 0
        self.inicializar_grid()
        
    def inicializar_grid(self):
        """Inicializa la cuadrícula vacía con puntos"""
        for fila in range(ALTO):
            for col in range(ANCHO):
                self.grid[fila][col] = Celda('.')
        self.zonas = []
        self.arterias = []
        
    def coordenada_a_indices(self, coord: str) -> Tuple[int, int]:
        """Convierte coordenada como 'C4' a (fila, columna)"""
        # Separar letras y números
        match = re.match(r'([A-Z]+)(\d+)', coord.upper())
        if not match:
            raise ValueError(f"Coordenada inválida: {coord}")
        
        letras, numero = match.groups()
        col = 0
        for char in letras:
            col = col * 26 + (ord(char) - ord('A') + 1)
        col -= 1  # Convertir a 0-based
        
        fila = int(numero) - 1  # Convertir a 0-based
        
        if fila < 0 or fila >= ALTO or col < 0 or col >= ANCHO:
            raise ValueError(f"Coordenada fuera de rango: {coord}")
        
        return fila, col
    
    def indices_a_coordenada(self, fila: int, col: int) -> str:
        """Convierte (fila, columna) a coordenada como 'C4'"""
        if col < 0 or col >= ANCHO or fila < 0 or fila >= ALTO:
            raise ValueError(f"Índices fuera de rango: ({fila}, {col})")
        
        # Convertir columna a letras (Excel style)
        letras = ""
        num = col + 1
        while num > 0:
            num -= 1
            letras = chr(ord('A') + (num % 26)) + letras
            num //= 26
        
        return f"{letras}{fila + 1}"
    
    def colocar_zona(self, coord: str, tipo: str) -> bool:
        """Coloca una zona de 3x3 en la coordenada dada"""
        try:
            fila, col = self.coordenada_a_indices(coord)
        except ValueError as e:
            print(f"Error: {e}")
            return False
        
        # Verificar que la zona cabe en la cuadrícula
        if fila + 2 >= ALTO or col + 2 >= ANCHO:
            print(f"Error: La zona no cabe en la posición {coord}")
            return False
        
        # Verificar que todas las celdas estén vacías
        for df in range(3):
            for dc in range(3):
                if self.grid[fila + df][col + dc].contenido != '.':
                    print(f"Error: La celda {self.indices_a_coordenada(fila + df, col + dc)} está ocupada")
                    return False
        
        # Colocar la zona
        for df in range(3):
            for dc in range(3):
                celda = Celda(tipo, 1, True, False)
                celda.tipo_zona = tipo
                self.grid[fila + df][col + dc] = celda
        
        # Registrar la zona
        self.zonas.append((fila, col, tipo, 1))
        return True
    
    def colocar_arteria(self, inicio: str, fin: str) -> bool:
        """Coloca una arteria vial entre dos coordenadas"""
        try:
            fila1, col1 = self.coordenada_a_indices(inicio)
            fila2, col2 = self.coordenada_a_indices(fin)
        except ValueError as e:
            print(f"Error: {e}")
            return False
        
        # Determinar si es horizontal o vertical
        if fila1 == fila2:  # Horizontal
            if col1 > col2:
                col1, col2 = col2, col1
            # Verificar que todas las celdas estén vacías
            for c in range(col1, col2 + 1):
                if self.grid[fila1][c].contenido != '.':
                    print(f"Error: La celda {self.indices_a_coordenada(fila1, c)} está ocupada")
                    return False
            # Colocar arteria horizontal
            for c in range(col1, col2 + 1):
                celda = Celda(HORIZONTAL, 0, False, True)
                self.grid[fila1][c] = celda
            self.arterias.append((fila1, col1, fila1, col2, 'H'))
            
        elif col1 == col2:  # Vertical
            if fila1 > fila2:
                fila1, fila2 = fila2, fila1
            # Verificar que todas las celdas estén vacías
            for f in range(fila1, fila2 + 1):
                if self.grid[f][col1].contenido != '.':
                    print(f"Error: La celda {self.indices_a_coordenada(f, col1)} está ocupada")
                    return False
            # Colocar arteria vertical
            for f in range(fila1, fila2 + 1):
                celda = Celda(VERTICAL, 0, False, True)
                self.grid[f][col1] = celda
            self.arterias.append((fila1, col1, fila2, col1, 'V'))
            
        else:
            print("Error: Las arterias deben ser horizontales o verticales")
            return False
        
        # Actualizar intersecciones
        self.actualizar_intersecciones()
        return True
    
    def actualizar_intersecciones(self):
        """Actualiza las intersecciones donde se cruzan arterias"""
        # Primero, marcar todas las arterias como normales
        for fila in range(ALTO):
            for col in range(ANCHO):
                if self.grid[fila][col].es_arteria and self.grid[fila][col].contenido != INTERSECCION:
                    if self.grid[fila][col].contenido == '=':
                        self.grid[fila][col].contenido = HORIZONTAL
                    elif self.grid[fila][col].contenido == '|':
                        self.grid[fila][col].contenido = VERTICAL
        
        # Luego, encontrar y marcar intersecciones
        for fila in range(ALTO):
            for col in range(ANCHO):
                if self.grid[fila][col].es_arteria:
                    # Verificar si hay intersección (horizontal + vertical)
                    es_horizontal = self.grid[fila][col].contenido == HORIZONTAL
                    es_vertical = self.grid[fila][col].contenido == VERTICAL
                    
                    # Verificar si es parte de una intersección
                    if fila > 0 and fila < ALTO-1 and col > 0 and col < ANCHO-1:
                        # Buscar intersecciones
                        hay_horizontal = (self.grid[fila][col-1].contenido == HORIZONTAL or 
                                        self.grid[fila][col+1].contenido == HORIZONTAL)
                        hay_vertical = (self.grid[fila-1][col].contenido == VERTICAL or 
                                      self.grid[fila+1][col].contenido == VERTICAL)
                        
                        # Si es horizontal y hay vertical, es intersección
                        if (self.grid[fila][col].contenido == HORIZONTAL or 
                            self.grid[fila][col].contenido == VERTICAL):
                            if hay_horizontal and hay_vertical:
                                self.grid[fila][col].contenido = INTERSECCION
    
    def guardar(self, ruta: str):
        """Guarda la cuadrícula en un archivo"""
        try:
            with open(ruta, 'w') as f:
                # Guardar dimensiones
                f.write(f"{ANCHO} {ALTO}\n")
                
                # Guardar todas las celdas
                for fila in range(ALTO):
                    for col in range(ANCHO):
                        celda = self.grid[fila][col]
                        if celda.es_zona:
                            f.write(f"Z {fila} {col} {celda.tipo_zona} {celda.nivel}\n")
                        elif celda.es_arteria:
                            f.write(f"A {fila} {col} {celda.contenido} {celda.trafico}\n")
                
                # Guardar zonas como grupos
                f.write("ZONAS\n")
                for fila, col, tipo, nivel in self.zonas:
                    f.write(f"{fila} {col} {tipo} {nivel}\n")
                
                # Guardar arterias
                f.write("ARTERIAS\n")
                for f1, c1, f2, c2, tipo in self.arterias:
                    f.write(f"{f1} {c1} {f2} {c2} {tipo}\n")
                
            print(f"Ciudad guardada en {ruta}")
        except Exception as e:
            print(f"Error al guardar: {e}")
    
    def cargar(self, ruta: str):
        """Carga una cuadrícula desde un archivo"""
        try:
            with open(ruta, 'r') as f:
                # Reiniciar grid
                self.inicializar_grid()
                
                lines = f.readlines()
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    if not line:
                        i += 1
                        continue
                    
                    parts = line.split()
                    if parts[0] == "ZONAS":
                        i += 1
                        while i < len(lines) and lines[i].strip():
                            partes = lines[i].strip().split()
                            if partes:
                                fila, col, tipo, nivel = int(partes[0]), int(partes[1]), partes[2], int(partes[3])
                                # Colocar la zona
                                for df in range(3):
                                    for dc in range(3):
                                        celda = Celda(tipo, nivel, True, False)
                                        celda.tipo_zona = tipo
                                        self.grid[fila + df][col + dc] = celda
                                self.zonas.append((fila, col, tipo, nivel))
                            i += 1
                        continue
                    
                    elif parts[0] == "ARTERIAS":
                        i += 1
                        while i < len(lines) and lines[i].strip():
                            partes = lines[i].strip().split()
                            if partes:
                                f1, c1, f2, c2, tipo = int(partes[0]), int(partes[1]), int(partes[2]), int(partes[3]), partes[4]
                                # Colocar arteria
                                if tipo == 'H':
                                    for c in range(min(c1, c2), max(c1, c2) + 1):
                                        celda = Celda(HORIZONTAL, 0, False, True)
                                        self.grid[f1][c] = celda
                                else:  # 'V'
                                    for f in range(min(f1, f2), max(f1, f2) + 1):
                                        celda = Celda(VERTICAL, 0, False, True)
                                        self.grid[f][c1] = celda
                                self.arterias.append((f1, c1, f2, c2, tipo))
                            i += 1
                        self.actualizar_intersecciones()
                        continue
                    
                    # Formato simple: Z f c tipo nivel
                    elif parts[0] == "Z":
                        fila, col, tipo, nivel = int(parts[1]), int(parts[2]), parts[3], int(parts[4])
                        for df in range(3):
                            for dc in range(3):
                                celda = Celda(tipo, nivel, True, False)
                                celda.tipo_zona = tipo
                                self.grid[fila + df][col + dc] = celda
                        self.zonas.append((fila, col, tipo, nivel))
                    
                    # Formato simple: A f c simbolo trafico
                    elif parts[0] == "A":
                        fila, col, simbolo, trafico = int(parts[1]), int(parts[2]), parts[3], int(parts[4])
                        celda = Celda(simbolo, 0, False, True)
                        celda.trafico = trafico
                        self.grid[fila][col] = celda
                    
                    i += 1
                
            print(f"Ciudad cargada desde {ruta}")
        except Exception as e:
            print(f"Error al cargar: {e}")
            self.inicializar_grid()
    
    def imprimir_grid(self):
        """Imprime la cuadrícula en consola"""
        # Imprimir encabezado de columnas
        print("   ", end="")
        for col in range(ANCHO):
            coord = self.indices_a_coordenada(0, col)
            print(f"{coord:3}", end="")
        print()
        
        # Imprimir filas
        for fila in range(ALTO):
            print(f"{fila + 1:2} ", end="")
            for col in range(ANCHO):
                if col < ANCHO - 1:
                    print(f"{self.grid[fila][col]}", end="")
                else:
                    print(f"{self.grid[fila][col]}")
    
    def tick(self):
        """Ejecuta un tick de reloj"""
        self.tick_actual += 1
        print(f"\n=== TICK {self.tick_actual} ===")
        
        # 1. Calcular tráfico de arterias
        self.calcular_trafico()
        
        # 2. Evaluar crecimiento/decrecimiento de zonas
        self.evaluar_zonas()
        
        # 3. Actualizar tráfico anterior
        for fila in range(ALTO):
            for col in range(ANCHO):
                if self.grid[fila][col].es_arteria:
                    self.grid[fila][col].trafico_anterior = self.grid[fila][col].trafico
        
        # 4. Imprimir nuevo estado
        self.imprimir_grid()
    
    def calcular_trafico(self):
        """Calcula el tráfico para todas las arterias"""
        # Reiniciar tráfico
        for fila in range(ALTO):
            for col in range(ANCHO):
                if self.grid[fila][col].es_arteria:
                    self.grid[fila][col].trafico = 0
        
        # Para cada arteria, calcular tráfico basado en zonas adyacentes
        for fila in range(ALTO):
            for col in range(ANCHO):
                if self.grid[fila][col].es_arteria:
                    trafico = 0
                    # Verificar 4 direcciones
                    direcciones = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                    for df, dc in direcciones:
                        nf, nc = fila + df, col + dc
                        if 0 <= nf < ALTO and 0 <= nc < ANCHO:
                            if self.grid[nf][nc].es_zona:
                                trafico += int(math.sqrt(self.grid[nf][nc].nivel))
                    self.grid[fila][col].trafico = trafico
    
    def evaluar_zonas(self):
        """Evalúa crecimiento/decrecimiento de todas las zonas"""
        nuevas_zonas = []
        
        for fila, col, tipo, nivel in self.zonas:
            # Verificar si la zona sigue existiendo
            if not self.zona_existe(fila, col, tipo):
                continue
            
            votos_crecimiento = 0
            votos_decrecimiento = 0
            
            if tipo == RESIDENCIAL:
                votos_crecimiento, votos_decrecimiento = self.evaluar_zona_residencial(fila, col, nivel)
            elif tipo == COMERCIAL:
                votos_crecimiento, votos_decrecimiento = self.evaluar_zona_comercial(fila, col, nivel)
            elif tipo == INDUSTRIAL:
                votos_crecimiento, votos_decrecimiento = self.evaluar_zona_industrial(fila, col, nivel)
            
            # Decidir cambio
            if votos_crecimiento > votos_decrecimiento and nivel < 27:
                nuevo_nivel = nivel + 1
                self.actualizar_zona(fila, col, tipo, nuevo_nivel)
                nuevas_zonas.append((fila, col, tipo, nuevo_nivel))
            elif votos_decrecimiento > votos_crecimiento and nivel > 1:
                nuevo_nivel = nivel - 1
                self.actualizar_zona(fila, col, tipo, nuevo_nivel)
                nuevas_zonas.append((fila, col, tipo, nuevo_nivel))
            else:
                nuevas_zonas.append((fila, col, tipo, nivel))
        
        self.zonas = nuevas_zonas
    
    def zona_existe(self, fila: int, col: int, tipo: str) -> bool:
        """Verifica si una zona aún existe en la cuadrícula"""
        if fila + 2 >= ALTO or col + 2 >= ANCHO:
            return False
        for df in range(3):
            for dc in range(3):
                if not self.grid[fila + df][col + dc].es_zona or self.grid[fila + df][col + dc].tipo_zona != tipo:
                    return False
        return True
    
    def actualizar_zona(self, fila: int, col: int, tipo: str, nuevo_nivel: int):
        """Actualiza el nivel de una zona"""
        for df in range(3):
            for dc in range(3):
                celda = self.grid[fila + df][col + dc]
                celda.nivel = nuevo_nivel
                # Actualizar representación visual (mayúsculas según nivel)
                if nuevo_nivel <= 26:
                    if nuevo_nivel >= 1:
                        celda.contenido = tipo.upper() if nuevo_nivel > 1 else tipo
                    else:
                        celda.contenido = tipo
                else:
                    # Nivel 27 se muestra con mayúscula
                    celda.contenido = tipo.upper()
    
    def evaluar_zona_residencial(self, fila: int, col: int, nivel: int) -> Tuple[int, int]:
        """Evalúa crecimiento para zona residencial"""
        votos_crecimiento = 0
        votos_decrecimiento = 0
        
        # Zona central de la zona residencial
        cf, cc = fila + 1, col + 1
        
        # Crecimiento: arterias adyacentes
        direcciones = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for df, dc in direcciones:
            nf, nc = cf + df, cc + dc
            if 0 <= nf < ALTO and 0 <= nc < ANCHO:
                if self.grid[nf][nc].es_arteria:
                    votos_crecimiento += 1
                    if self.grid[nf][nc].trafico > 5:
                        votos_decrecimiento += 2
        
        # Crecimiento: zonas industriales a 10 celdas de distancia con nivel < 18
        for z_fila, z_col, z_tipo, z_nivel in self.zonas:
            if z_tipo == INDUSTRIAL:
                # Calcular distancia entre centros de zonas
                dist = max(abs(z_fila + 1 - cf), abs(z_col + 1 - cc))
                if dist <= 10 and z_nivel < 18:
                    votos_crecimiento += 1
                elif dist > 10:
                    votos_decrecimiento += 2
            elif z_tipo == COMERCIAL:
                dist = max(abs(z_fila + 1 - cf), abs(z_col + 1 - cc))
                if dist <= 10 and z_nivel > math.sqrt(nivel):
                    votos_crecimiento += 1
        
        return votos_crecimiento, votos_decrecimiento
    
    def evaluar_zona_comercial(self, fila: int, col: int, nivel: int) -> Tuple[int, int]:
        """Evalúa crecimiento para zona comercial"""
        votos_crecimiento = 0
        votos_decrecimiento = 0
        
        # Zona central de la zona comercial
        cf, cc = fila + 1, col + 1
        
        # Crecimiento: arterias con tráfico > 5
        direcciones = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for df, dc in direcciones:
            nf, nc = cf + df, cc + dc
            if 0 <= nf < ALTO and 0 <= nc < ANCHO:
                if self.grid[nf][nc].es_arteria:
                    if self.grid[nf][nc].trafico > 5:
                        votos_crecimiento += 1
                    # Decremento: arterias con tráfico decrecido
                    if self.grid[nf][nc].trafico < self.grid[nf][nc].trafico_anterior:
                        votos_decrecimiento += 2
        
        # Evaluar zonas cercanas
        for z_fila, z_col, z_tipo, z_nivel in self.zonas:
            dist = max(abs(z_fila + 1 - cf), abs(z_col + 1 - cc))
            if dist <= 10:
                if z_tipo == RESIDENCIAL:
                    votos_crecimiento += 1
                    if z_nivel < self.grid[z_fila + 1][z_col + 1].nivel:  # Decrementó
                        votos_decrecimiento += 2
                elif z_tipo == INDUSTRIAL:
                    if z_nivel > math.sqrt(nivel):
                        votos_crecimiento += 1
                    if z_nivel < self.grid[z_fila + 1][z_col + 1].nivel:  # Decrementó
                        votos_decrecimiento += 2
        
        return votos_crecimiento, votos_decrecimiento
    
    def evaluar_zona_industrial(self, fila: int, col: int, nivel: int) -> Tuple[int, int]:
        """Evalúa crecimiento para zona industrial"""
        votos_crecimiento = 0
        votos_decrecimiento = 0
        
        # Zona central de la zona industrial
        cf, cc = fila + 1, col + 1
        
        # Crecimiento: arterias adyacentes
        direcciones = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for df, dc in direcciones:
            nf, nc = cf + df, cc + dc
            if 0 <= nf < ALTO and 0 <= nc < ANCHO:
                if self.grid[nf][nc].es_arteria:
                    votos_crecimiento += 1
        
        # Evaluar zonas cercanas
        for z_fila, z_col, z_tipo, z_nivel in self.zonas:
            dist = max(abs(z_fila + 1 - cf), abs(z_col + 1 - cc))
            if dist <= 10:
                if z_tipo == RESIDENCIAL:
                    votos_crecimiento += 1
                    if z_nivel < self.grid[z_fila + 1][z_col + 1].nivel:  # Decrementó
                        votos_decrecimiento += 2
                elif z_tipo == COMERCIAL:
                    if z_nivel > math.sqrt(nivel):
                        votos_crecimiento += 1
                    if z_nivel < self.grid[z_fila + 1][z_col + 1].nivel:  # Decrementó
                        votos_decrecimiento += 2
                elif z_tipo == INDUSTRIAL:
                    if z_nivel < self.grid[z_fila + 1][z_col + 1].nivel:  # Decrementó
                        votos_decrecimiento += 2
        
        return votos_crecimiento, votos_decrecimiento
    
    def es_comando_valido(self, comando: str) -> bool:
        """Verifica si un comando es válido antes de procesarlo"""
        if not comando.strip():
            return True  # Enter vacío = tick
        
        partes = comando.strip().split()
        if not partes:
            return True
        
        cmd = partes[0].lower()
        
        if cmd in ['r', 'c', 'i']:
            return len(partes) == 2
        elif cmd == 'a':
            return len(partes) >= 3
        elif cmd in ['guardar', 'cargar', 'salir']:
            return len(partes) >= 1
        return False
    
    def procesar_comando(self, comando: str):
        """Procesa un comando del usuario"""
        if not comando.strip():
            # Enter vacío = tick
            self.tick()
            return
        
        partes = comando.strip().split()
        cmd = partes[0].lower()
        
        if cmd == 'salir':
            return 'salir'
        
        elif cmd == 'guardar':
            if len(partes) >= 2:
                self.guardar(partes[1])
            else:
                print("Uso: guardar <ruta_archivo>")
        
        elif cmd == 'cargar':
            if len(partes) >= 2:
                self.cargar(partes[1])
            else:
                print("Uso: cargar <ruta_archivo>")
        
        elif cmd in ['r', 'c', 'i']:
            if len(partes) >= 2:
                self.colocar_zona(partes[1], cmd)
            else:
                print(f"Uso: {cmd} <celda>")
        
        elif cmd == 'a':
            if len(partes) >= 3:
                self.colocar_arteria(partes[1], partes[2])
            else:
                print("Uso: a <celda_inicio> <celda_fin>")
        
        else:
            print(f"Comando desconocido: {cmd}")
        
        # Imprimir grid después de cada comando
        self.imprimir_grid()

def main():
    """Función principal del juego"""
    juego = SimCity()
    
    print("=" * 80)
    print("BIENVENIDO A SIMCITY 2526")
    print("=" * 80)
    print("\nComandos:")
    print("  r <celda>        - Crear zona residencial")
    print("  c <celda>        - Crear zona comercial")
    print("  i <celda>        - Crear zona industrial")
    print("  a <inicio> <fin> - Crear arteria vial")
    print("  guardar <archivo> - Guardar ciudad")
    print("  cargar <archivo> - Cargar ciudad")
    print("  salir            - Salir del juego")
    print("  [Enter]          - Avanzar un tick de reloj")
    print("\nEjemplos:")
    print("  r C4             - Crea zona residencial en C4")
    print("  a C7 P7          - Crea arteria horizontal de C7 a P7")
    print("  a F4 F9          - Crea arteria vertical de F4 a F9")
    print()
    
    juego.imprimir_grid()
    
    while True:
        try:
            comando = input("\n> ").strip()
            if not juego.es_comando_valido(comando):
                print("Comando inválido. Intente de nuevo.")
                continue
            
            resultado = juego.procesar_comando(comando)
            if resultado == 'salir':
                print("¡Gracias por jugar SimCity 2526!")
                break
        except KeyboardInterrupt:
            print("\n¡Gracias por jugar SimCity 2526!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()