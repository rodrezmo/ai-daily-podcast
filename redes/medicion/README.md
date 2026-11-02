# Medición

## Qué se mide
- **Por clip y red:** vistas, me gusta, comentarios, compartidos.
- **Por red:** seguidores al inicio y al final de la semana.
- **Hacia el podcast:** clics por `utm_source` (si el host de podcast los ofrece) y reproducciones del episodio por origen.

## Links con UTM
`https://rodrezmo.github.io/ai-daily-podcast/?utm_source=<red>&utm_medium=social&utm_campaign=<fecha-episodio>`

## Qué falta
- Muchos hosts de podcast no atribuyen reproducciones a una red. Verificar qué ofrece el elegido. Si no hay atribución, se mide por picos de reproducciones el día de cada clip y se aclara que es una correlación.
- No se verificaron los límites de ninguna API de redes. Hacerlo antes de automatizar.

## Cómo cargar
Una fila por clip y por día en `metricas.csv` (columnas en el encabezado). `python3 resumen.py` genera la tabla semanal.
