# Redes del podcast diario de IA

Equipo de agentes que produce y mide el contenido de redes del podcast (diario, de noticias de IA; Radar IA). Vive en `redes/`; el sitio y el feed están en `docs/`.

## Flujo diario

1. El **redactor de clips** toma el guion o la transcripción del episodio y propone 1 a 3 fragmentos y un texto por red.
2. El **editor** corta el audio de cada fragmento y genera el video vertical con `pipeline/audiograma.sh`.
3. Una persona revisa fragmento, texto y fuentes. **Nada se publica sin esa aprobación.**
4. El **programador** carga lo aprobado.
5. El **analista** vuelca los números semanales y corre `medicion/resumen.py`.

El **estratega** revisa los resultados cada semana y ajusta formatos y horarios.

## Cuidado especial: exactitud

Es un podcast de noticias sobre un tema que cambia rápido. Cada afirmación en un clip tiene que tener la fuente anotada en `texto.md`. Si no se puede verificar, el fragmento no se publica. Ver `reglas.md`.

## Carga

Un episodio diario es mucho trabajo. El equipo está pensado para que la revisión humana lleve unos 15 minutos por día. Si no alcanza, se reduce la cantidad de clips, no la revisión.

## Pendiente

- Confirmar usuarios en cada red.
- Probar `pipeline/audiograma.sh` con un episodio real.
- Elegir host de podcast y ver qué estadísticas por origen ofrece.
