# Heurística de Conversión a Markdown

Esta heurística está implementada en `app/infrastructure/pdf_reader.py` y tiene como objetivo transformar el texto plano extraído del PDF en un documento Markdown legible sin depender de librerías pesadas como **pymupdf4llm**.

## Qué detecta

| Elemento | Señal en el texto plano | Conversión a Markdown |
|----------|------------------------|-----------------------|
| **Título** | Líneas en mayúsculas, o líneas cuyo número de caracteres es significativamente mayor que el promedio de la página. También se reconoce cuando la línea está precedida y seguida por una línea vacía. | `#` (nivel 1) o `##` (nivel 2) según la longitud del título. |
| **Subtítulo** | Texto en *Title Case* (mayúscula inicial en cada palabra) y longitud corta. | `##` o `###` según posición. |
| **Listas con viñetas** | Líneas que comienzan con `- `, `* ` o números seguidos de `.` (e.g., `1.`). | Convertido a listas Markdown (`- item`). |
| **Listas numeradas** | Líneas que empiezan con `1. `, `2. `, etc. | Mantiene numeración como lista (`1. item`). |
| **Tablas básicas** | Texto con columnas separadas por uno o más espacios y con una fila de encabezado seguida por una fila separadora de guiones (`---`). | Se genera una tabla Markdown simple usando `|`. **Limitación:** sólo funciona cuando las columnas están bien alineadas; no se detectan tablas complejas con celdas anidadas o sin separador de guiones. |
| **Párrafos** | Bloques de texto separados por dos saltos de línea (`\n\n`). | Se conserva como párrafos normales. |

## Qué **no** detecta
- Tablas con bordes gráficos o sin separador `---`.
- Formatos avanzados como listas anidadas, citas complejas, o bloques de código.
- Imágenes o contenido no textual (e.g., gráficos, diagramas). Estos se omiten.

## Ejemplos

### Entrada (texto plano)
```
INTRODUCCIÓN

Este documento explica el proceso.

OBJETIVOS

- Definir metas
- Evaluar resultados

TABLA DE RECUENTES

Nombre    Edad   Ciudad
----      ----   -----
Ana       30     Madrid
```

### Salida (Markdown)
```markdown
# INTRODUCCIÓN

Este documento explica el proceso.

## OBJETIVOS

- Definir metas
- Evaluar resultados

| Nombre | Edad | Ciudad |
|--------|------|--------|
| Ana | 30 | Madrid |
```

## Licencia y peso

- La heurística está escrita en puro **Python** y **no** introduce dependencias externas adicionales.
- El peso adicional al proyecto es **~30 KB** (código). No afecta significativamente el tiempo de arranque ni el tamaño de la imagen Docker.

## Futuras mejoras
- Soporte para listas anidadas.
- Detección de bloques de código con sangrías.
- Mejor reconocimiento de encabezados basados en tamaños de fuente (requiere análisis de metadatos de PDF).
