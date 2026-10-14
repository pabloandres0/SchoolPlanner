
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║      M.S.U.  ·  MINISTERIO DE SALUDOS UNIVERSALES  ·  DIVISIÓN HOLA-MUNDO     ║
╚══════════════════════════════════════════════════════════════════════════════╝

OBJETIVO OFICIAL
    Imprimir «Hello, World!» en la pantalla.

MÉTODO OFICIAL
    El más largo, redundante, indirecto y ofuscado que la burocracia permita.
    (La solicitud  print("Hello, World!")  fue rechazada por «falta de papeleo».)

USO
    python hola_mundo_absurdo.py             imprime ÚNICAMENTE «Hello, World!»
    python hola_mundo_absurdo.py --chismes   además narra el viaje completo por stderr

RECORRIDO DEL EXPEDIENTE (cada paso es un «Departamento» inscrito por una metaclase)
    10  Fuentes redundantes ..... Lagrange + Gödel + Church + tabla arcoíris SHA-256,
                                  con sabotaje incluido y votación por mayoría
    20  Lenguajes esotéricos .... compilador e intérprete de Brainfuck
    30  Máquinas virtuales ...... ensamblador, desensamblador y CPU de pila propios
    40  Correos ................. paquetes desordenados (asyncio) reensamblados con un montículo
    50  Ordenamiento lento ...... Slowsort
    60  Bases de datos .......... SQLite en memoria con CTE recursiva
    70  Darwinismo aplicado ..... algoritmo genético («la comadreja» de Dawkins)
    80  Criptografía redundante . cadena de códecs de ida y de vuelta
    85  Estadística inútil ...... media, mediana, desviación y entropía de Shannon
    90  Línea de ensamblaje ..... un hilo por letra, con turnos
    95  Notaría ................. verificación SHA-256 en tiempo constante
    99  Imprenta Nacional ....... árbol sintáctico hecho a mano + compile() + exec()

Sólo usa la biblioteca estándar de Python (3.8 o superior). No hay nada que instalar.
"""

from __future__ import annotations

import abc
import argparse
import ast
import asyncio
import base64
import binascii
import codecs
import collections
import contextlib
import dataclasses
import enum
import fractions
import functools
import hashlib
import heapq
import hmac
import importlib
import itertools
import math
import random
import statistics
import string
import struct
import sys
import textwrap
import threading
import time
import typing
import uuid
import zlib


def importar_si_hay(nombre: str):
    """Plan B burocrático: si falta un módulo, el expediente sigue adelante sin él."""
    try:
        return importlib.import_module(nombre)
    except ImportError:
        return None


bz2 = importar_si_hay("bz2")
lzma = importar_si_hay("lzma")
sqlite3 = importar_si_hay("sqlite3")


# ═════════════════════════════════════════════════════════════════════════════
#  CAPÍTULO 0 · INFRAESTRUCTURA BUROCRÁTICA
# ═════════════════════════════════════════════════════════════════════════════

class ErrorDeBurocracia(Exception):
    """Falta un sello, una firma, una fotocopia o el café del funcionario."""


LIBRO_DE_SELLOS: collections.Counter = collections.Counter()


def sellar(etiqueta: str):
    """Decorador: estampa un sello en el libro oficial cada vez que se invoca la función."""
    def decorador(funcion):
        @functools.wraps(funcion)
        def envoltura(*args, **kwargs):
            LIBRO_DE_SELLOS[etiqueta] += 1
            return funcion(*args, **kwargs)
        return envoltura
    return decorador


def en_triplicado(funcion):
    """Decorador: ejecuta la función tres veces y exige que las tres copias coincidan.
    (Sólo para funciones puras; para las demás, la burocracia no tiene remedio.)"""
    @functools.wraps(funcion)
    def envoltura(*args, **kwargs):
        copias = [funcion(*args, **kwargs) for _ in range(3)]
        if any(copia != copias[0] for copia in copias[1:]):
            raise ErrorDeBurocracia(f"Las tres copias de «{funcion.__name__}» no coinciden")
        LIBRO_DE_SELLOS["copias en triplicado"] += 1
        return copias[0]
    return envoltura


@dataclasses.dataclass
class Expediente:
    """La carpeta amarilla que viaja de ventanilla en ventanilla."""

    verboso: bool = False
    numero: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()).upper())
    ordinales: list = dataclasses.field(default_factory=list)
    texto: str = ""
    bitacora: list = dataclasses.field(default_factory=list)

    def anotar(self, mensaje: str) -> None:
        linea = f"[M.S.U.] {mensaje}"
        self.bitacora.append(linea)
        if self.verboso:
            print(linea, file=sys.stderr)


@contextlib.contextmanager
def ventanilla(nombre: str, expediente: Expediente):
    """Cada departamento atiende en su propia ventanilla, con apertura y cierre solemnes."""
    inicio = time.perf_counter()
    expediente.anotar(f"▶ Se abre la ventanilla «{nombre}»")
    try:
        yield
    finally:
        milisegundos = (time.perf_counter() - inicio) * 1000
        expediente.anotar(f"■ Se cierra la ventanilla tras {milisegundos:.2f} ms de espera innecesaria\n")


class RegistroDeDepartamentos(abc.ABCMeta):
    """Metaclase: inscribe cada departamento concreto en el Padrón Oficial y, de paso,
    le estampa un sello a su método `procesar` sin que nadie se lo pida."""

    padron: list = []

    def __new__(mcs, nombre, bases, ns, **kwargs):
        procesar = ns.get("procesar")
        if procesar is not None and not getattr(procesar, "__isabstractmethod__", False):
            ns["procesar"] = sellar(f"{nombre}.procesar")(procesar)
        clase = super().__new__(mcs, nombre, bases, ns, **kwargs)
        if not clase.__abstractmethods__:      # sólo los departamentos concretos
            mcs.padron.append(clase)
        return clase


class Departamento(metaclass=RegistroDeDepartamentos):
    """Clase abstracta de la que descienden todos los funcionarios."""

    orden: int = 0
    nombre: str = "Departamento Sin Nombre"

    @abc.abstractmethod
    def procesar(self, expediente: Expediente) -> None:
        """Hace algo innecesario con el expediente."""


# ═════════════════════════════════════════════════════════════════════════════
#  CAPÍTULO 1 · FUENTES REDUNDANTES (una sola fuente sería sospechosa)
# ═════════════════════════════════════════════════════════════════════════════

# ── Fuente 1 · Interpolación de Lagrange con aritmética racional exacta ──────
# Hay un único polinomio de grado 12 que pasa por los puntos
#     (0, código de la 1.ª letra), (1, código de la 2.ª letra), … (12, código de la 13.ª)
# Éstos son sus coeficientes, del término independiente hacia arriba.
COEFICIENTES_DE_LAGRANGE = [
    fractions.Fraction(texto)
    for texto in (
        "72",
        "-11037827/9240",
        "917043223/277200",
        "-47519989/13440",
        "1450408591/725760",
        "-194718605/290304",
        "2037206149/14515200",
        "-8912843/483840",
        "279667/193536",
        "-26713/483840",
        "-3617/14515200",
        "1571/15966720",
        "-79/31933440",
    )
]
LONGITUD_DEL_MENSAJE = len(COEFICIENTES_DE_LAGRANGE)


def evaluar_polinomio(coeficientes: list, x: int) -> fractions.Fraction:
    """Regla de Horner: evalúa un polinomio con el mínimo de multiplicaciones
    (qué ironía, tratándose de este programa)."""
    acumulado = fractions.Fraction(0)
    for coeficiente in reversed(coeficientes):
        acumulado = acumulado * x + coeficiente
    return acumulado


@sellar("fuente·Lagrange")
@en_triplicado
def fuente_lagrange() -> list:
    valores = []
    for x in range(LONGITUD_DEL_MENSAJE):
        y = evaluar_polinomio(COEFICIENTES_DE_LAGRANGE, x)
        if y.denominator != 1:
            raise ErrorDeBurocracia(f"El polinomio dio {y} en x={x}; los códigos deben ser enteros")
        valores.append(int(y))
    return valores


# ── Fuente 2 · Numeración de Gödel ───────────────────────────────────────────
# El mensaje entero vive dentro de UN solo número:  2^c0 · 3^c1 · 5^c2 · 7^c3 · …
# donde cᵢ es el código de la i-ésima letra y las bases son los primos consecutivos.
NUMERO_DE_GODEL = int("".join((
    "3de26b63aad25179d442c185865a77f87c9eecdf8684acfa82c1c8fb",
    "a94d6b83921b30f2fe45477853ed57cc3efb71557c9a2ffb602cb9dd",
    "81d9c088b4eec901297c1ecb70c3bed03e240dc5c5b7471ae91e81ed",
    "7ad4996d678292a3c35faed687a3edc7ff7105e97a284dceb3d52792",
    "fc30134b848f0b2d85d93a477c3b3e342906dd38c2927e214c091a1a",
    "7feab63e42f5383593d8ef8f010027a9afb985959c122bf7d3851276",
    "5193a7aac5aa6cdbdf943bb694ce0bc8859278ece8bb697aa82a0917",
    "7429fe0c35bdb8d84a6038a18a77588d8c1fd834b7005340984f5d28",
    "774128b6b131bf07f973a15446ed3fb28f3fa1576c971686b922e908",
    "38a99f06df073a05e1120b3a6e1e9e47a829d1300385d5e5ff41b183",
    "d270881ba17fd87341c3162793047da6b488256035e64fe7a0a307f8",
    "aaf19119ec9fc648d270b3f80801a259729ca7190df15cc37437f3df",
    "ab6d10335d9dcc648ea531dafba02945437f82109cd7869b5ab6a259",
    "5b019b0f1eee90c9382e8ffda5b071de3cd423101968ce5cf86781e1",
    "8376f31342f002c0e390cccf870d66a18fd4a45bc38c905e0334b0e4",
    "1741a63f7db6096490ae0971852a550800b8a4044ed7d0d5e83cfeab",
    "69e80f6edc0cfceb4703dbc9475fafa61af632c05cb091a172d29059",
    "61464d4d3a995273183214a66fb9bd26e8037fa46a9bd7995e713b7d",
    "f4015000000000000000000",
)), 16)


def primos():
    """Criba de Eratóstenes incremental y perezosa: una infinidad de primos a domicilio,
    por si algún día el saludo se vuelve más largo."""
    compuestos: dict = {}
    candidato = 2
    while True:
        if candidato not in compuestos:
            yield candidato
            compuestos[candidato * candidato] = [candidato]
        else:
            for p in compuestos.pop(candidato):
                compuestos.setdefault(candidato + p, []).append(p)
        candidato += 1


@sellar("fuente·Gödel")
@en_triplicado
def fuente_godel(longitud: int) -> list:
    resto, exponentes = NUMERO_DE_GODEL, []
    for p in itertools.islice(primos(), longitud):
        exponente = 0
        while resto % p == 0:
            resto //= p
            exponente += 1
        exponentes.append(exponente)
    if resto != 1:
        raise ErrorDeBurocracia("Sobraron factores primos: el número de Gödel fue adulterado")
    return exponentes


# ── Fuente 3 · Aritmética de Church (los números son funciones, porque sí) ───
CERO = lambda f: lambda x: x                                    # noqa: E731
SUCESOR = lambda n: lambda f: lambda x: f(n(f)(x))              # noqa: E731
SUMA = lambda a: lambda b: lambda f: lambda x: a(f)(b(f)(x))    # noqa: E731
PRODUCTO = lambda a: lambda b: lambda f: a(b(f))                # noqa: E731
UNO = SUCESOR(CERO)
DOS = SUCESOR(UNO)
A_ENTERO = lambda n: n(lambda k: k + 1)(0)                      # noqa: E731

# Combinador Z: el combinador Y para lenguajes que evalúan con prisa. Permite hacer
# recursión sin que ninguna función se llame a sí misma por su nombre.
Z = lambda f: (lambda x: f(lambda v: x(x)(v)))(lambda x: f(lambda v: x(x)(v)))  # noqa: E731

# n  →  numeral de Church, por expansión binaria:  n = 2·(n // 2) + (n % 2)
CHURCH_DE = Z(
    lambda rec: lambda n: CERO
    if n == 0
    else SUMA(PRODUCTO(DOS)(rec(n // 2)))(UNO if n % 2 else CERO)
)

# Cada letra se guarda como (a, b, c) con  código = a·b + c
FACTORES_DE_CHURCH = (
    (8, 9, 0), (10, 10, 1), (11, 9, 9), (12, 9, 0), (10, 11, 1), (4, 11, 0), (2, 16, 0),
    (9, 9, 6), (3, 37, 0), (6, 19, 0), (4, 27, 0), (5, 20, 0), (3, 11, 0),
)


@sellar("fuente·Church")
@en_triplicado
def fuente_church() -> list:
    return [
        A_ENTERO(SUMA(PRODUCTO(CHURCH_DE(a))(CHURCH_DE(b)))(CHURCH_DE(c)))
        for a, b, c in FACTORES_DE_CHURCH
    ]


# ── Fuente 4 · Tabla arcoíris: sólo guardamos las huellas SHA-256 de las letras ─
HUELLAS_DE_LAS_LETRAS = (
    "44bd7ae60f478fae1061e11a7739f4b94d1daf917982d33b6fc8a01a63f89c21",
    "3f79bb7b435b05321651daefd374cdc681dc06faa65e374e38337b88ca046dea",
    "acac86c0e609ca906f632b0e2dacccb2b77d22b0621f20ebece1a4835b93f6f0",
    "acac86c0e609ca906f632b0e2dacccb2b77d22b0621f20ebece1a4835b93f6f0",
    "65c74c15a686187bb6bbf9958f494fc6b80068034a659a9ad44991b08c58f2d2",
    "d03502c43d74a30b936740a9517dc4ea2b2ad7168caa0a774cefe793ce0b33e7",
    "36a9e7f1c95b82ffb99743e0c5c4ce95d83c9a430aac59f84ef3cbfab6145068",
    "fcb5f40df9be6bae66c1d77a6c15968866a9e6cbd7314ca432b019d17392f6f4",
    "65c74c15a686187bb6bbf9958f494fc6b80068034a659a9ad44991b08c58f2d2",
    "454349e422f05297191ead13e21d3db520e5abef52055e4964b82fb213f593a1",
    "acac86c0e609ca906f632b0e2dacccb2b77d22b0621f20ebece1a4835b93f6f0",
    "18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4",
    "bb7208bc9b5d7c04f1236a82a0093a5e33f40423d5ba8d4266f7092c3ba43b62",
)


@sellar("fuente·Arcoíris")
@en_triplicado
def fuente_arcoiris() -> list:
    tabla_inversa = {hashlib.sha256(bytes([b])).hexdigest(): b for b in range(256)}
    return [tabla_inversa[huella] for huella in HUELLAS_DE_LAS_LETRAS]


# ── Sabotaje y votación por mayoría (cuádruple redundancia modular) ──────────
def sabotear(fuentes: dict, rng: random.Random) -> str:
    """Un agente de la oposición altera UN valor de UNA fuente. Cosas que pasan."""
    victima = rng.choice(sorted(fuentes))
    posicion = rng.randrange(len(fuentes[victima]))
    antes = fuentes[victima][posicion]
    fuentes[victima][posicion] = antes ^ rng.randrange(1, 128)
    despues = fuentes[victima][posicion]
    return (f"¡SABOTAJE! Alguien alteró la posición {posicion} de la fuente «{victima}»: "
            f"{antes} → {despues}")


@sellar("votación")
def votar(fuentes: dict) -> tuple:
    """Para cada posición gana el valor más votado. La democracia, aplicada a los bytes."""
    ganadores, disidencias = [], 0
    for columna in zip(*fuentes.values()):
        conteo = collections.Counter(columna)
        [(ganador, _votos)] = conteo.most_common(1)
        disidencias += len(conteo) > 1
        ganadores.append(ganador)
    return ganadores, disidencias


class DepartamentoDeFuentesRedundantes(Departamento):
    orden = 10
    nombre = "Departamento de Fuentes Redundantes (cuádruple redundancia modular)"

    def procesar(self, expediente: Expediente) -> None:
        fuentes = {
            "Lagrange": fuente_lagrange(),
            "Gödel": fuente_godel(LONGITUD_DEL_MENSAJE),
            "Church": fuente_church(),
            "Arcoíris": fuente_arcoiris(),
        }
        for fuente, valores in fuentes.items():
            expediente.anotar(f"La fuente «{fuente}» entregó {len(valores)} números")
        expediente.anotar(sabotear(fuentes, random.Random(0xC0FFEE)))
        ganadores, disidencias = votar(fuentes)
        expediente.anotar(f"Votación por mayoría: {disidencias} posición(es) con voto dividido, "
                          "todas resueltas democráticamente")
        expediente.ordinales = ganadores


# ═════════════════════════════════════════════════════════════════════════════
#  CAPÍTULO 2 · LENGUAJES ESOTÉRICOS (compilador + intérprete de Brainfuck)
# ═════════════════════════════════════════════════════════════════════════════

def _emitir_delta(delta: int) -> str:
    """Brainfuck que suma `delta` a la celda 0, usando la celda 1 como contador de un
    bucle de multiplicación (delta = a·b + r)."""
    signo = "+" if delta >= 0 else "-"
    n = abs(delta)
    if n < 10:
        return signo * n
    a = math.isqrt(n)
    b, r = divmod(n, a)
    return ">" + "+" * a + "[<" + signo * b + ">-]<" + signo * r


@sellar("compilador Brainfuck")
def compilar_a_brainfuck(ordinales: list) -> str:
    programa, actual = [], 0
    for objetivo in ordinales:
        programa.append(_emitir_delta(objetivo - actual))
        programa.append(".")
        actual = objetivo
    return "".join(programa)


class InterpreteBrainfuck:
    """Cinta de 30 000 celdas de un byte, ocho instrucciones y cero piedad."""

    def __init__(self, programa: str, celdas: int = 30000):
        self.programa = programa
        self.cinta = bytearray(celdas)
        self.salto = self._precalcular_saltos(programa)

    @staticmethod
    def _precalcular_saltos(programa: str) -> dict:
        pila, tabla = [], {}
        for posicion, instruccion in enumerate(programa):
            if instruccion == "[":
                pila.append(posicion)
            elif instruccion == "]":
                if not pila:
                    raise ErrorDeBurocracia("Un «]» huérfano pide asilo")
                inicio = pila.pop()
                tabla[inicio], tabla[posicion] = posicion, inicio
        if pila:
            raise ErrorDeBurocracia("Un «[» quedó sin cerrar")
        return tabla

    @sellar("ejecución Brainfuck")
    def ejecutar(self) -> bytes:
        cinta, salto, programa = self.cinta, self.salto, self.programa
        salida = bytearray()
        puntero = ip = 0
        while ip < len(programa):
            instruccion = programa[ip]
            if instruccion == "+":
                cinta[puntero] = (cinta[puntero] + 1) & 0xFF
            elif instruccion == "-":
                cinta[puntero] = (cinta[puntero] - 1) & 0xFF
            elif instruccion == ">":
                puntero += 1
            elif instruccion == "<":
                puntero -= 1
            elif instruccion == ".":
                salida.append(cinta[puntero])
            elif instruccion == "[" and cinta[puntero] == 0:
                ip = salto[ip]
            elif instruccion == "]" and cinta[puntero] != 0:
                ip = salto[ip]
            if not 0 <= puntero < len(cinta):
                raise ErrorDeBurocracia("El cabezal de la cinta se salió de la oficina")
            ip += 1
        return bytes(salida)


class DepartamentoDeLenguajesEsotericos(Departamento):
    orden = 20
    nombre = "Departamento de Lenguajes Esotéricos (Brainfuck)"

    def procesar(self, expediente: Expediente) -> None:
        programa = compilar_a_brainfuck(expediente.ordinales)
        expediente.anotar(f"Programa Brainfuck generado: {len(programa)} instrucciones")
        expediente.anotar(f"    {programa[:70]}…")
        salida = InterpreteBrainfuck(programa).ejecutar()
        if list(salida) != expediente.ordinales:
            raise ErrorDeBurocracia("La auditoría interna detectó que Brainfuck no es Brainfuck")
        expediente.anotar(f"Brainfuck devolvió {len(salida)} bytes idénticos a los que recibió. Misión cumplida.")
        expediente.ordinales = list(salida)


# ═════════════════════════════════════════════════════════════════════════════
#  CAPÍTULO 3 · MÁQUINAS VIRTUALES (ensamblador + desensamblador + CPU de pila)
# ═════════════════════════════════════════════════════════════════════════════

class Op(enum.IntEnum):
    PARAR = 0
    EMPUJAR = 1
    SUMAR = 2
    RESTAR = 3
    MULTIPLICAR = 4
    DUPLICAR = 5
    ESCRIBIR = 6


FORMATO_DE_INSTRUCCION = ">BH"   # 1 byte de operación + 2 bytes de operando (big-endian)


def generar_ensamblador(ordinales: list) -> str:
    """Un funcionario aburrido redacta, en lenguaje ensamblador, un programa que calcula
    cada letra por un camino distinto según sea divisible entre 3, par o impar."""
    lineas = ["; ─── Programa redactado por un funcionario aburrido ───"]
    for indice, codigo in enumerate(ordinales):
        lineas.append(f"; --- letra número {indice} ---")
        if codigo % 3 == 0:
            lineas += ["EMPUJAR 3", f"EMPUJAR {codigo // 3}", "MULTIPLICAR", "ESCRIBIR"]
        elif codigo % 2 == 0:
            lineas += [f"EMPUJAR {codigo // 2}", "DUPLICAR", "SUMAR", "ESCRIBIR"]
        else:
            lineas += [f"EMPUJAR {codigo + 5}", "EMPUJAR 5", "RESTAR", "ESCRIBIR"]
    lineas.append("PARAR")
    return "\n".join(lineas)


def ensamblar(texto_asm: str) -> bytes:
    codigo = bytearray()
    for linea in texto_asm.splitlines():
        linea = linea.split(";", 1)[0].strip()
        if not linea:
            continue
        partes = linea.split()
        try:
            operacion = Op[partes[0]]
        except KeyError:
            raise ErrorDeBurocracia(f"Instrucción desconocida: {partes[0]!r}") from None
        operando = int(partes[1]) if len(partes) > 1 else 0
        codigo += struct.pack(FORMATO_DE_INSTRUCCION, operacion, operando)
    return bytes(codigo)


def desensamblar(codigo: bytes):
    for indice, (operacion, operando) in enumerate(struct.iter_unpack(FORMATO_DE_INSTRUCCION, codigo)):
        sufijo = f" {operando}" if operacion == Op.EMPUJAR else ""
        yield f"{indice:04d}  {Op(operacion).name}{sufijo}"


class MaquinaVirtualDePila:
    """Procesador de siete instrucciones, sin saltos, sin memoria y sin futuro."""

    def __init__(self, codigo: bytes):
        self.programa = list(struct.iter_unpack(FORMATO_DE_INSTRUCCION, codigo))
        self.pila: list = []
        self.salida = bytearray()
        self.tabla = {
            Op.EMPUJAR: lambda n: self.pila.append(n),
            Op.SUMAR: lambda _: self._binaria(lambda a, b: a + b),
            Op.RESTAR: lambda _: self._binaria(lambda a, b: a - b),
            Op.MULTIPLICAR: lambda _: self._binaria(lambda a, b: a * b),
            Op.DUPLICAR: lambda _: self.pila.append(self.pila[-1]),
            Op.ESCRIBIR: lambda _: self.salida.append(self.pila.pop() & 0xFF),
        }

    def _binaria(self, operacion) -> None:
        b, a = self.pila.pop(), self.pila.pop()
        self.pila.append(operacion(a, b))

    @sellar("ciclos de CPU")
    def ejecutar(self) -> bytes:
        contador = 0
        while True:
            operacion, operando = self.programa[contador]
            contador += 1
            if operacion == Op.PARAR:
                return bytes(self.salida)
            self.tabla[Op(operacion)](operando)


class DepartamentoDeMaquinasVirtuales(Departamento):
    orden = 30
    nombre = "Departamento de Máquinas Virtuales (ensamblador, desensamblador y CPU propios)"

    def procesar(self, expediente: Expediente) -> None:
        ensamblador = generar_ensamblador(expediente.ordinales)
        codigo = ensamblar(ensamblador)
        expediente.anotar(f"Ensamblador: {len(ensamblador.splitlines())} líneas → "
                          f"{len(codigo)} bytes de código máquina")
        for linea in itertools.islice(desensamblar(codigo), 6):
            expediente.anotar(f"    {linea}")
        expediente.anotar("    …")
        salida = MaquinaVirtualDePila(codigo).ejecutar()
        if list(salida) != expediente.ordinales:
            raise ErrorDeBurocracia("La CPU calculó otra cosa; habrá que llamar al soporte técnico")
        expediente.ordinales = list(salida)


# ═════════════════════════════════════════════════════════════════════════════
#  CAPÍTULO 4 · CORREOS (un «TCP» casero sobre asyncio, con reensamblado por montículo)
# ═════════════════════════════════════════════════════════════════════════════

class DepartamentoDeCorreos(Departamento):
    orden = 40
    nombre = "Departamento de Correos (protocolo TCP casero sobre asyncio)"

    async def _servicio_postal(self, ordinales: list, rng: random.Random, expediente: Expediente) -> list:
        buzon: asyncio.Queue = asyncio.Queue()
        paquetes = list(enumerate(ordinales))          # (número de secuencia, carga útil)
        rng.shuffle(paquetes)
        expediente.anotar(f"Orden de salida de los paquetes: {[secuencia for secuencia, _ in paquetes]}")

        async def cartero(paquete):
            for _ in range(rng.randrange(1, 4)):       # el cartero se distrae un ratito
                await asyncio.sleep(0)
            await buzon.put(paquete)

        async def receptor() -> list:
            monticulo, esperado, ordenados = [], 0, []
            while esperado < len(ordinales):
                heapq.heappush(monticulo, await buzon.get())
                while monticulo and monticulo[0][0] == esperado:
                    ordenados.append(heapq.heappop(monticulo)[1])
                    esperado += 1
            return ordenados

        carteros = [asyncio.create_task(cartero(paquete)) for paquete in paquetes]
        ordenados = await receptor()
        await asyncio.gather(*carteros)
        return ordenados

    def procesar(self, expediente: Expediente) -> None:
        rng = random.Random(1789)                      # año de la Toma de la Bastilla
        buzon_de_resultados: list = []

        def en_su_propio_hilo() -> None:
            # El servicio postal corre en un hilo aparte, con su propio bucle de eventos,
            # para no pelearse con ningún bucle ajeno (Jupyter, IDLE, etc.).
            try:
                buzon_de_resultados.append(
                    asyncio.run(self._servicio_postal(expediente.ordinales, rng, expediente)))
            except BaseException as error:             # noqa: BLE001
                buzon_de_resultados.append(error)

        hilo = threading.Thread(target=en_su_propio_hilo, name="cartero-mayor")
        hilo.start()
        hilo.join()
        resultado = buzon_de_resultados[0]
        if isinstance(resultado, BaseException):
            raise resultado
        expediente.anotar("Todos los paquetes llegaron, desordenados pero llegaron. Reensamblados.")
        expediente.ordinales = resultado


# ═════════════════════════════════════════════════════════════════════════════
#  CAPÍTULO 5 · ORDENAMIENTO LENTO (Slowsort: «multiplica y rinde»)
# ═════════════════════════════════════════════════════════════════════════════

def lentosort(v: list, i: int, j: int) -> None:
    """Slowsort (Broder y Stolfi, 1986): ordena a propósito de la peor manera razonable.
    Ordena recursivamente las dos mitades, lleva el máximo al final y vuelve a empezar
    con todo lo demás."""
    if i >= j:
        return
    medio = (i + j) // 2
    lentosort(v, i, medio)
    lentosort(v, medio + 1, j)
    if v[medio] > v[j]:
        v[medio], v[j] = v[j], v[medio]
    lentosort(v, i, j - 1)


class DepartamentoDeOrdenamientoLento(Departamento):
    orden = 50
    nombre = "Departamento de Ordenamiento Lento (Slowsort de Broder y Stolfi)"

    def procesar(self, expediente: Expediente) -> None:
        rng = random.Random(1986)                      # año de publicación del Slowsort
        pares = list(enumerate(expediente.ordinales))
        rng.shuffle(pares)
        expediente.anotar(f"Se barajaron los papeles: {[posicion for posicion, _ in pares]}")
        lentosort(pares, 0, len(pares) - 1)
        expediente.anotar(f"Slowsort terminó con los papeles en orden: {[posicion for posicion, _ in pares]}")
        expediente.ordinales = [valor for _, valor in pares]


# ═════════════════════════════════════════════════════════════════════════════
#  CAPÍTULO 6 · BASES DE DATOS (concatenar letras con SQL, como Dios manda)
# ═════════════════════════════════════════════════════════════════════════════

class DepartamentoDeBasesDeDatos(Departamento):
    orden = 60
    nombre = "Departamento de Bases de Datos (SQLite en memoria, porque sí)"

    CONSULTA = textwrap.dedent("""
        WITH RECURSIVE ensamblado(pos, texto) AS (
            SELECT 0, ''
            UNION ALL
            SELECT g.posicion + 1, ensamblado.texto || char(g.codigo)
              FROM ensamblado
              JOIN glifos AS g ON g.posicion = ensamblado.pos
        )
        SELECT texto FROM ensamblado ORDER BY pos DESC LIMIT 1
    """)

    def procesar(self, expediente: Expediente) -> None:
        if sqlite3 is None:
            expediente.anotar("Este Python no trae SQLite; el funcionario concatenará con los dedos.")
            expediente.texto = "".join(map(chr, expediente.ordinales))
            return
        expediente.anotar("Consulta SQL a ejecutar:\n" + textwrap.indent(self.CONSULTA.strip(), "        "))
        with contextlib.closing(sqlite3.connect(":memory:")) as conexion:
            conexion.execute("CREATE TABLE glifos (posicion INTEGER PRIMARY KEY, codigo INTEGER NOT NULL)")
            conexion.executemany("INSERT INTO glifos (posicion, codigo) VALUES (?, ?)",
                                 list(enumerate(expediente.ordinales)))
            (texto,) = conexion.execute(self.CONSULTA).fetchone()
        expediente.anotar(f"La base de datos devolvió una cadena de {len(texto)} caracteres")
        expediente.texto = texto


# ═════════════════════════════════════════════════════════════════════════════
#  CAPÍTULO 7 · DARWINISMO APLICADO (algoritmo genético: la «comadreja» de Dawkins)
# ═════════════════════════════════════════════════════════════════════════════

class DepartamentoDeDarwinismoAplicado(Departamento):
    orden = 70
    nombre = "Departamento de Darwinismo Aplicado (evolución de «Hello, World!» desde el caos)"

    ALFABETO = string.printable[:95]   # los 95 caracteres ASCII imprimibles
    HIJOS_POR_GENERACION = 150
    TASA_DE_MUTACION = 0.08

    @staticmethod
    def aptitud(candidato: str, objetivo: str) -> int:
        return sum(a == b for a, b in zip(candidato, objetivo))

    def _mutar(self, padre: str, rng: random.Random) -> str:
        return "".join(
            rng.choice(self.ALFABETO) if rng.random() < self.TASA_DE_MUTACION else letra
            for letra in padre
        )

    def procesar(self, expediente: Expediente) -> None:
        rng = random.Random(1859)                      # año de «El origen de las especies»
        objetivo = expediente.texto
        padre = "".join(rng.choice(self.ALFABETO) for _ in objetivo)
        expediente.anotar(f"Generación 0000: {padre!r}  (sopa primordial)")
        generacion = 0
        while padre != objetivo:
            generacion += 1
            hijos = [self._mutar(padre, rng) for _ in range(self.HIJOS_POR_GENERACION)]
            padre = max([padre, *hijos], key=lambda candidato: self.aptitud(candidato, objetivo))
            if generacion % 20 == 0:
                expediente.anotar(f"Generación {generacion:04d}: {padre!r}")
            if generacion > 100_000:
                raise ErrorDeBurocracia("La especie se extinguió sin llegar a saludar")
        expediente.anotar(f"Generación {generacion:04d}: {padre!r}  (¡ha evolucionado la cortesía!)")
        expediente.texto = padre


# ═════════════════════════════════════════════════════════════════════════════
#  CAPÍTULO 8 · CRIPTOGRAFÍA REDUNDANTE (cifrar y descifrar para quedar igual)
# ═════════════════════════════════════════════════════════════════════════════

class PasoDeCodec(typing.NamedTuple):
    nombre: str
    ida: typing.Callable
    vuelta: typing.Callable


def _rot13(datos: bytes) -> bytes:
    """ROT13 es su propia inversa: la única función que ya venía con el deshacer incluido."""
    return codecs.encode(datos.decode("utf-8"), "rot13").encode("utf-8")


def construir_cadena_de_codecs() -> list:
    pasos = [
        PasoDeCodec("rot13", _rot13, _rot13),
        PasoDeCodec("base64", base64.b64encode, base64.b64decode),
        PasoDeCodec("zlib", zlib.compress, zlib.decompress),
        PasoDeCodec("hexadecimal", binascii.hexlify, binascii.unhexlify),
    ]
    if bz2 is not None:
        pasos.append(PasoDeCodec("bz2", bz2.compress, bz2.decompress))
    pasos.append(PasoDeCodec("base32", base64.b32encode, base64.b32decode))
    if lzma is not None:
        pasos.append(PasoDeCodec("lzma", lzma.compress, lzma.decompress))
    pasos.append(PasoDeCodec("ascii85", base64.a85encode, base64.a85decode))
    return pasos


class DepartamentoDeCriptografiaRedundante(Departamento):
    orden = 80
    nombre = "Departamento de Criptografía Redundante (cadena de códecs, ida y vuelta)"

    def procesar(self, expediente: Expediente) -> None:
        cadena = construir_cadena_de_codecs()
        datos = expediente.texto.encode("utf-8")
        expediente.anotar(f"Mensaje original: {len(datos)} bytes")
        for paso in cadena:
            datos = paso.ida(datos)
            expediente.anotar(f"    ida    · {paso.nombre:<12} → {len(datos):>4} bytes")
        for paso in reversed(cadena):
            datos = paso.vuelta(datos)
            expediente.anotar(f"    vuelta · {paso.nombre:<12} → {len(datos):>4} bytes")
        expediente.texto = datos.decode("utf-8")


# ═════════════════════════════════════════════════════════════════════════════
#  CAPÍTULO 9 · ESTADÍSTICA INÚTIL (datos que nadie pidió)
# ═════════════════════════════════════════════════════════════════════════════

class DepartamentoDeEstadisticaInutil(Departamento):
    orden = 85
    nombre = "Departamento de Estadística Inútil (informe que nadie leerá)"

    def procesar(self, expediente: Expediente) -> None:
        codigos = [ord(letra) for letra in expediente.texto]
        frecuencias = collections.Counter(expediente.texto)
        total = len(expediente.texto)
        entropia = -sum((n / total) * math.log2(n / total) for n in frecuencias.values())
        letra, veces = frecuencias.most_common(1)[0]
        expediente.anotar(f"Código medio: {statistics.mean(codigos):.3f} · "
                          f"mediana: {statistics.median(codigos)} · "
                          f"desviación típica: {statistics.pstdev(codigos):.3f}")
        expediente.anotar(f"Entropía de Shannon: {entropia:.4f} bits por símbolo · "
                          f"letra más popular: {letra!r} ({veces} votos)")


# ═════════════════════════════════════════════════════════════════════════════
#  CAPÍTULO 10 · LÍNEA DE ENSAMBLAJE (un hilo por letra, con turnos estrictos)
# ═════════════════════════════════════════════════════════════════════════════

class DepartamentoDeLineaDeEnsamblaje(Departamento):
    orden = 90
    nombre = "Departamento de Línea de Ensamblaje (un obrero por letra, con turnos)"

    def procesar(self, expediente: Expediente) -> None:
        texto = expediente.texto
        turno = {"actual": 0}
        puerta = threading.Condition()
        resultado: list = [None] * len(texto)

        def obrero(indice: int, letra: str) -> None:
            with puerta:
                puerta.wait_for(lambda: turno["actual"] == indice)
                resultado[indice] = letra
                turno["actual"] += 1
                puerta.notify_all()

        rng = random.Random(1913)                      # año de la línea de montaje de Ford
        contratacion = list(enumerate(texto))
        rng.shuffle(contratacion)
        expediente.anotar(f"Orden de contratación de los obreros: {[i for i, _ in contratacion]}")
        obreros = [
            threading.Thread(target=obrero, args=par, name=f"obrero-{par[0]:02d}")
            for par in contratacion
        ]
        for trabajador in obreros:
            trabajador.start()
        for trabajador in obreros:
            trabajador.join()
        expediente.anotar(f"{len(obreros)} obreros respetaron su turno y se fueron a casa")
        expediente.texto = "".join(resultado)


# ═════════════════════════════════════════════════════════════════════════════
#  CAPÍTULO 11 · NOTARÍA (fe pública para un saludo)
# ═════════════════════════════════════════════════════════════════════════════

HUELLA_OFICIAL = "c98c24b677eff44860afea6f493bbaec5bb1c4cbb209c6fc2bbb47f66ff2ad31"


class DepartamentoDeNotaria(Departamento):
    orden = 95
    nombre = "Notaría Pública (verificación en tiempo constante, por si hay espías)"

    def procesar(self, expediente: Expediente) -> None:
        huella = hashlib.sha256((expediente.texto + "\n").encode("utf-8")).hexdigest()
        if not hmac.compare_digest(huella, HUELLA_OFICIAL):
            raise ErrorDeBurocracia("La huella no coincide con la oficial: el saludo es falso")
        expediente.anotar(f"El notario da fe: SHA-256 = {huella[:24]}…")


# ═════════════════════════════════════════════════════════════════════════════
#  CAPÍTULO 12 · IMPRENTA NACIONAL (árbol sintáctico hecho a mano)
# ═════════════════════════════════════════════════════════════════════════════

class DepartamentoDeImprentaNacional(Departamento):
    orden = 99
    nombre = "Imprenta Nacional (AST artesanal, compile() y exec() con privilegios mínimos)"

    @staticmethod
    def _construir_ast(texto: str) -> ast.Module:
        """Fabrica a mano el árbol de   print(chr(72) + chr(101) + chr(108) + …)"""
        def llamar(nombre: str, *argumentos):
            return ast.Call(func=ast.Name(id=nombre, ctx=ast.Load()),
                            args=list(argumentos), keywords=[])

        letras = [llamar("chr", ast.Constant(value=ord(letra))) for letra in texto]
        concatenado = functools.reduce(
            lambda izquierda, derecha: ast.BinOp(left=izquierda, op=ast.Add(), right=derecha),
            letras,
        )
        modulo = ast.Module(body=[ast.Expr(value=llamar("print", concatenado))], type_ignores=[])
        return ast.fix_missing_locations(modulo)

    def procesar(self, expediente: Expediente) -> None:
        arbol = self._construir_ast(expediente.texto)
        expediente.anotar(f"Árbol sintáctico: {ast.dump(arbol)[:90]}…")
        codigo = compile(arbol, filename="<imprenta-nacional>", mode="exec")
        # El módulo de las funciones incorporadas se busca por su nombre en códigos ASCII,
        # no vaya a ser que alguien lea el programa y entienda algo.
        incorporadas = importlib.import_module("".join(map(chr, (98, 117, 105, 108, 116, 105, 110, 115))))
        ambiente = {"__builtins__": {nombre: getattr(incorporadas, nombre) for nombre in ("print", "chr")}}
        exec(codigo, ambiente)                          # ← aquí, por fin, sale el saludo
        expediente.anotar("¡Misión cumplida! El saludo fue impreso con todas las de la ley.")


# ═════════════════════════════════════════════════════════════════════════════
#  EPÍLOGO · EL MINISTERIO Y SU GATILLO
# ═════════════════════════════════════════════════════════════════════════════

class Ministerio:
    """Organiza el recorrido del expediente por todos los departamentos inscritos."""

    def __init__(self, verboso: bool = False):
        self.verboso = verboso

    def ejecutar(self) -> int:
        expediente = Expediente(verboso=self.verboso)
        expediente.anotar(f"Se abre el expediente n.º {expediente.numero}")
        departamentos = sorted(RegistroDeDepartamentos.padron, key=lambda clase: clase.orden)
        expediente.anotar(f"El expediente deberá visitar {len(departamentos)} departamentos\n")
        for clase in departamentos:
            departamento = clase()
            with ventanilla(departamento.nombre, expediente):
                departamento.procesar(expediente)
        resumen = ", ".join(f"{etiqueta} ×{veces}" for etiqueta, veces in sorted(LIBRO_DE_SELLOS.items()))
        expediente.anotar(f"Libro de sellos: {resumen}")
        expediente.anotar(f"Total de sellos estampados: {sum(LIBRO_DE_SELLOS.values())}")
        return 0


def main(argv=None) -> int:
    analizador = argparse.ArgumentParser(
        prog="hola_mundo_absurdo",
        description="Imprime «Hello, World!» de la manera más burocrática posible.",
    )
    analizador.add_argument("--chismes", action="store_true",
                            help="narra por stderr el recorrido completo del expediente")
    argumentos, _sobrantes = analizador.parse_known_args(argv)
    if argumentos.chismes and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(errors="replace")
    return Ministerio(verboso=argumentos.chismes).ejecutar()


if __name__ == "__main__":
    # Ojo: los identificadores de abajo están escritos con letras góticas de Unicode.
    # Python los normaliza (NFKC) y los lee como «main» y «SystemExit».
    _codigo_de_salida = 𝖒𝖆𝖎𝖓()
    if _codigo_de_salida:
        raise 𝕾𝖞𝖘𝖙𝖊𝖒𝕰𝖝𝖎𝖙(_codigo_de_salida)
