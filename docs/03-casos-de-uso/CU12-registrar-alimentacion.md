# CU12. Consultar contenido educativo

## 1. Información general

- **Código:** CU12
- **Nombre:** Consultar contenido educativo.
- **Versión:** 1.0
- **Actor principal:** Usuario autenticado.
- **Actores secundarios:** Administrador técnico de contenidos; profesional competente en salud o nutrición encargado de revisar el contenido.
- **Objetivo:** Permitir que el usuario consulte material educativo publicado en GlucoVida sobre conceptos generales de glucosa, composición nutricional e interpretación informativa de la información nutricional.
- **Prioridad:** Media-alta.
- **Tipo:** Caso de uso funcional.
- **Relaciones:** CU10. Consultar alimentos; CU11. Consultar información nutricional e impacto glucémico general.
- **Alcance:** Búsqueda, navegación y lectura de contenido educativo publicado y aprobado.
- **Fuera del alcance:** Diagnóstico, interpretación clínica individual, recomendaciones alimentarias personalizadas, dietas y correlaciones entre alimentos consultados y mediciones personales.

## 2. Descripción

El usuario accede al módulo educativo de GlucoVida para consultar artículos, guías breves o cápsulas informativas que expliquen conceptos generales relacionados con la glucosa y la composición nutricional de los alimentos.

El contenido podrá abordar temas como la diferencia entre carbohidratos y azúcares, la lectura de información nutricional, el significado y las limitaciones de una clasificación general de impacto glucémico, y la importancia de interpretar la información alimentaria en su contexto.

El contenido publicado deberá proceder de fuentes científicas o institucionales confiables, contar con una revisión profesional pertinente y mostrar la fecha de actualización cuando esté registrada.

GlucoVida presentará el contenido con fines educativos. No utilizará el historial personal de glucosa para seleccionar artículos, formular explicaciones individuales, inferir condiciones clínicas ni recomendar alimentos. La consulta educativa será independiente del registro y análisis de mediciones.

## 3. Precondiciones

1. La aplicación se encuentra disponible.
2. El usuario dispone de una sesión válida.
3. Existe contenido educativo publicado y habilitado para consulta, o el sistema puede mostrar un estado informativo cuando no existan publicaciones.
4. El contenido que se presenta como revisado cuenta con el estado de aprobación correspondiente.
5. Los artículos educativos publicados incluyen el aviso de responsabilidad definido para GlucoVida.

## 4. Postcondiciones

### 4.1. Consulta exitosa

1. El usuario visualiza el contenido educativo seleccionado.
2. El sistema presenta los metadatos disponibles, como título, categoría, fuentes y fecha de actualización.
3. El aviso de responsabilidad educativa aparece de forma visible.
4. La consulta no modifica los contenidos publicados ni los datos personales de glucosa.
5. No se crea una asociación entre el contenido consultado y el historial personal del usuario.

### 4.2. Contenido no disponible

1. El sistema informa que no existen publicaciones disponibles para la categoría o búsqueda solicitada.
2. El usuario puede realizar una nueva búsqueda o regresar al listado educativo.
3. El sistema no presenta borradores ni contenido que no haya sido aprobado para publicación.

## 5. Datos de entrada

- Categoría educativa, opcional.
- Término de búsqueda, opcional.
- Identificador del contenido seleccionado.
- Parámetros de paginación, cuando sean necesarios.

La consulta no debe recibir mediciones de glucosa, diagnósticos, medicamentos, registros de alimentos consumidos ni otros datos clínicos del usuario.

## 6. Datos de salida

El listado educativo podrá presentar:

- Identificador del contenido.
- Título.
- Descripción breve.
- Categoría temática.
- Fecha de publicación o actualización, cuando esté disponible.

El detalle del contenido podrá presentar:

- Título y cuerpo del artículo.
- Fuentes de referencia.
- Fecha de publicación o actualización.
- Identificación de que el contenido fue revisado, cuando corresponda.
- Aviso de responsabilidad educativa.

El sistema no debe presentar información de revisión profesional que no esté registrada o que no pueda verificarse.

## 7. Flujo principal

1. El usuario inicia sesión e ingresa al módulo educativo.
2. El sistema verifica la sesión y consulta las publicaciones habilitadas.
3. El sistema presenta las categorías y el listado de contenidos disponibles.
4. El usuario selecciona una categoría, introduce un término de búsqueda o explora el listado.
5. El sistema valida los criterios de consulta.
6. El sistema recupera únicamente los contenidos publicados y habilitados.
7. El sistema presenta los resultados de acuerdo con el orden definido por la aplicación.
8. El usuario selecciona un artículo o recurso educativo.
9. El sistema verifica que el contenido continúe habilitado y aprobado para publicación.
10. El sistema presenta el contenido, sus metadatos disponibles y el aviso de responsabilidad educativa.
11. El usuario consulta la información.
12. El usuario puede regresar al listado y seleccionar otra publicación.
13. El caso de uso finaliza sin modificar las publicaciones ni consultar las mediciones personales de glucosa.

## 8. Flujos alternativos

### FA01. Consulta sin filtros

1. El usuario ingresa al módulo educativo sin introducir una búsqueda.
2. El sistema presenta los contenidos publicados y habilitados.
3. El usuario selecciona una publicación o aplica un filtro.

### FA02. Búsqueda por palabra o título

1. El usuario introduce un término de búsqueda.
2. El sistema busca coincidencias en los campos habilitados para búsqueda, como título y descripción.
3. El sistema presenta las publicaciones coincidentes.

### FA03. Filtro por categoría educativa

1. El usuario selecciona una categoría disponible.
2. El sistema recupera los contenidos publicados correspondientes a esa categoría.
3. El sistema muestra los resultados.

### FA04. No se encuentran contenidos

1. El usuario ejecuta una búsqueda válida.
2. El sistema no encuentra publicaciones coincidentes.
3. El sistema informa que no hay resultados y permite modificar los criterios.

### FA05. Regreso al listado

1. El usuario termina de leer una publicación.
2. El usuario selecciona la opción para regresar.
3. El sistema vuelve al listado educativo y conserva los criterios anteriores cuando sea técnicamente posible.

## 9. Flujos de excepción

### FE01. Criterios de búsqueda inválidos

1. El sistema recibe un criterio que supera los límites establecidos o tiene un formato no permitido.
2. El sistema rechaza el criterio inválido.
3. El sistema informa cómo corregirlo sin revelar detalles internos.

### FE02. Contenido retirado o deshabilitado

1. El usuario intenta abrir una publicación que ha sido retirada o deshabilitada.
2. El sistema impide mostrar el contenido como vigente.
3. El sistema informa que la publicación ya no está disponible y permite regresar al listado.

### FE03. Contenido pendiente de aprobación

1. El sistema detecta que el contenido no tiene el estado requerido para publicación.
2. El sistema impide su consulta ordinaria.
3. El sistema no presenta borradores ni versiones pendientes de revisión.

### FE04. Error al recuperar el contenido

1. El sistema no logra recuperar una publicación.
2. El sistema informa que la consulta no pudo completarse.
3. El sistema no presenta una versión no verificada como si fuera el contenido vigente.

### FE05. Sesión expirada

1. El sistema detecta que la sesión ya no es válida.
2. El sistema solicita una nueva autenticación.
3. El contenido protegido solo se devuelve después de comprobar la sesión conforme a las reglas de acceso.

## 10. Reglas de negocio

- **RN-CU12-01.** Solo se presentarán contenidos habilitados para consulta ordinaria.
- **RN-CU12-02.** El contenido que requiera revisión profesional no podrá publicarse como aprobado hasta completar el proceso definido.
- **RN-CU12-03.** El contenido educativo deberá basarse en fuentes científicas o institucionales confiables.
- **RN-CU12-04.** Las referencias utilizadas deberán conservarse como metadatos del contenido.
- **RN-CU12-05.** La fecha de actualización se mostrará cuando esté registrada.
- **RN-CU12-06.** Los artículos, guías y cápsulas educativas deberán incluir el siguiente aviso, visible y legible:

  “Esta información es exclusivamente de carácter educativo e informativo y no constituye un diagnóstico médico, prescripción ni reemplaza la valoración de un profesional de la salud competente”.

- **RN-CU12-07.** El contenido no debe diagnosticar enfermedades ni proponer tratamientos.
- **RN-CU12-08.** El contenido no debe generar dietas, menús ni planes de alimentación personalizados.
- **RN-CU12-09.** La información sobre impacto glucémico debe explicar los límites de cualquier clasificación general y no atribuirle capacidad de predecir la respuesta individual.
- **RN-CU12-10.** El contenido no podrá afirmar que un alimento es universalmente seguro o peligroso para todas las personas.
- **RN-CU12-11.** El sistema no utilizará los registros personales de glucosa para seleccionar, adaptar o generar contenido educativo.
- **RN-CU12-12.** El sistema no relacionará los artículos consultados con alimentos buscados ni con mediciones individuales.
- **RN-CU12-13.** Las visitas o consultas de contenido no se convertirán en registros de consumo.
- **RN-CU12-14.** Los cambios editoriales deben seguir un proceso controlado de revisión y publicación.
- **RN-CU12-15.** Los contenidos retirados o pendientes de aprobación no deben aparecer como publicaciones vigentes.
- **RN-CU12-16.** La consulta educativa no modificará los datos personales ni los registros del catálogo nutricional.

## 11. Requisitos funcionales

- **RF-CU12-01.** El sistema debe permitir acceder al módulo educativo a un usuario autenticado.
- **RF-CU12-02.** Debe mostrar el listado de contenidos habilitados.
- **RF-CU12-03.** Debe permitir buscar contenido por los campos habilitados.
- **RF-CU12-04.** Debe permitir filtrar por categoría educativa, cuando existan categorías configuradas.
- **RF-CU12-05.** Debe permitir abrir el detalle de una publicación seleccionada.
- **RF-CU12-06.** Debe mostrar las fuentes registradas para el contenido.
- **RF-CU12-07.** Debe mostrar la fecha de actualización cuando exista.
- **RF-CU12-08.** Debe mostrar el aviso de responsabilidad educativa de forma visible.
- **RF-CU12-09.** Debe impedir la consulta ordinaria de contenido retirado, deshabilitado o pendiente de aprobación.
- **RF-CU12-10.** Debe presentar un mensaje cuando no existan resultados.
- **RF-CU12-11.** Debe permitir regresar al listado educativo.
- **RF-CU12-12.** Debe manejar errores de consulta sin exponer información técnica interna.
- **RF-CU12-13.** No debe utilizar las mediciones personales para personalizar o generar contenido.
- **RF-CU12-14.** No debe relacionar consultas educativas con alimentos consultados ni con mediciones de glucosa.

## 12. Seguridad, privacidad y calidad

1. El backend debe comprobar la sesión antes de devolver contenido protegido.
2. Las búsquedas deben validarse y ejecutarse mediante consultas seguras.
3. La aplicación no debe exponer publicaciones internas o borradores al usuario ordinario.
4. Los contenidos deberán mantener legibilidad, consistencia y referencias verificables.
5. Los errores no deben revelar detalles técnicos de la infraestructura.
6. No se debe recuperar ni procesar el historial de glucosa para mostrar el material educativo.
7. El contenido deberá revisarse y mantenerse conforme al procedimiento editorial vigente.
8. Los avisos de responsabilidad deben ser visibles y no quedar ocultos por elementos de la interfaz.

## 13. Criterios de aceptación

- **CA-CU12-01.** Un usuario autenticado puede acceder al módulo educativo.
- **CA-CU12-02.** El sistema presenta las publicaciones habilitadas.
- **CA-CU12-03.** La búsqueda devuelve las publicaciones que coinciden con sus criterios.
- **CA-CU12-04.** El filtro por categoría presenta los contenidos correspondientes.
- **CA-CU12-05.** El usuario puede abrir una publicación y leer su contenido.
- **CA-CU12-06.** Las fuentes se presentan cuando están registradas.
- **CA-CU12-07.** La fecha de actualización se presenta cuando está disponible.
- **CA-CU12-08.** El aviso de responsabilidad se muestra de forma visible en el contenido educativo.
- **CA-CU12-09.** Los artículos retirados o pendientes de aprobación no se muestran como vigentes.
- **CA-CU12-10.** Una búsqueda sin coincidencias produce un mensaje informativo.
- **CA-CU12-11.** Ante un error, la aplicación no presenta datos no verificados como contenido vigente.
- **CA-CU12-12.** La consulta no utiliza las mediciones personales del usuario para adaptar el contenido.
- **CA-CU12-13.** La consulta no genera dietas, diagnósticos ni recomendaciones clínicas.
- **CA-CU12-14.** El sistema no vincula contenidos consultados con alimentos ni con mediciones de glucosa.

## 14. Fuera del alcance

- Crear o editar contenido educativo desde la interfaz del usuario.
- Realizar consultas clínicas individuales.
- Recomendar alimentos según el historial de glucosa.
- Elaborar dietas, menús o planes de alimentación.
- Diagnosticar enfermedades o recomendar tratamientos.
- Correlacionar contenidos, consultas de alimentos y mediciones personales.