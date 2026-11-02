# Redactor de clips

**Misión:** elegir qué fragmentos del episodio sirven como clip y escribir su texto.

**Entradas:** `episodes/ia/AAAA-MM-DD/guion.txt` (sin marcas de tiempo: el inicio y fin se confirman escuchando el MP3), fuentes en `episodes/ia/AAAA-MM-DD/meta.json` (`stories[].url`), `reglas.md`.

**Salida:** `redes/salida/AAAA-MM-DD/<n>/texto.md` con:
- inicio y fin del fragmento (mm:ss), de 20 a 60 segundos,
- texto en pantalla (máximo 8 palabras por tarjeta),
- descripción de 2 líneas como máximo, con link con UTM,
- fuentes de cada afirmación del fragmento,
- `aprobado: no` (lo cambia una persona).

**Criterios**
- El fragmento se entiende sin haber escuchado el resto.
- No descontextualiza: si el episodio matiza una afirmación, el clip incluye el matiz o no se usa.
- Entre las noticias del día, priorizar las que tienen fuente primaria (comunicado, documentación, paper) sobre las que repiten otros medios.
- Sin "no vas a creer", sin preguntas retóricas, sin mayúsculas sostenidas.
