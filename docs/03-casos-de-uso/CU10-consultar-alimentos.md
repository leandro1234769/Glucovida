# CU10. Consultar alimentos

## 1. Información general

- **Código:** CU10
- **Nombre:** Consultar alimentos.
- **Estado:** Cerrado funcionalmente.
- **Actor principal:** Usuario autenticado.
- **Objetivo:** Permitir que el usuario busque y consulte los alimentos del catálogo de GlucoVida para acceder a información general sobre su composición nutricional y, cuando exista una clasificación validada, su posible impacto glucémico general.
- **Prioridad:** Alta.
- **Relación:** CU11. Consultar información nutricional e impacto glucémico general.
- **Alcance:** Búsqueda, filtrado y selección de alimentos registrados en el catálogo.
- **Fuera del alcance:** Registro de consumo, correlación con mediciones personales, dietas y recomendaciones clínicas.

## 2. Descripción

El usuario accede al catálogo de alimentos de GlucoVida, busca por nombre completo o parcial y puede aplicar un filtro por categoría. El sistema presenta los resultados en orden alfabético y permite seleccionar un alimento para consultar su información nutricional mediante CU11.

El catálogo de la primera versión estará limitado a entre 50 y 100 alimentos de consumo frecuente en el contexto colombiano, organizados en las seis categorías definidas en el documento de Visión y Alcance.

Los resultados identificarán el alimento y podrán incluir una categoría general de impacto glucémico si esta existe y ha sido validada bajo una metodología documentada. La ausencia de esa categoría no debe impedir consultar el alimento.

El catálogo es independiente de las mediciones personales. Buscar o consultar un alimento no significa que el usuario lo haya consumido, y el sistema no guardará ni asociará esa consulta con su historial de glucosa.

## 3. Precondiciones

1. La aplicación está disponible.
2. El usuario dispone de una cuenta activa y de una sesión válida.
3. El catálogo contiene registros habilitados para consulta.
4. Las categorías activas están registradas en el sistema.

## 4. Postcondiciones

### 4.1. Consulta exitosa

1. El sistema presenta los alimentos que coinciden con los criterios.
2. Los resultados aparecen en orden alfabético.
3. El usuario puede seleccionar un alimento para abrir CU11.
4. El catálogo y las mediciones personales permanecen sin cambios.

### 4.2. Consulta sin resultados

1. El sistema informa que no se encontraron coincidencias.
2. El usuario puede cambiar los criterios y repetir la búsqueda.
3. No se generan registros de consumo ni se modifica información almacenada.

## 5. Datos de entrada

- Nombre completo o parcial del alimento, opcional.
- Categoría seleccionada, opcional.
- Parámetros de paginación, cuando correspondan.

Si no se especifican filtros, el sistema mostrará el catálogo habilitado conforme al orden alfabético y al límite de resultados configurado.

## 6. Datos de salida

Cada resultado podrá incluir:

- Identificador del alimento.
- Nombre del alimento.
- Categoría.
- Referencia breve de la porción, cuando esté disponible.
- Categoría general de impacto glucémico, únicamente cuando exista una clasificación validada para ese alimento.

Los detalles nutricionales se consultarán en CU11. Los resultados no incluirán información del historial de glucosa del usuario.

## 7. Flujo principal

1. El usuario inicia sesión y accede al módulo de alimentos.
2. El sistema verifica la sesión y presenta la interfaz del catálogo.
3. El usuario introduce un nombre completo o parcial, selecciona una categoría o deja los filtros vacíos.
4. El usuario ejecuta la búsqueda.
5. El sistema valida los criterios.
6. El backend consulta los registros habilitados que cumplen los filtros.
7. El sistema ordena los resultados alfabéticamente por nombre.
8. El sistema presenta los resultados mediante paginación cuando sea necesario.
9. El usuario selecciona un alimento.
10. El sistema abre CU11 para presentar la información nutricional del alimento seleccionado.
11. El caso de uso finaliza sin modificar el catálogo, registrar un consumo ni consultar las mediciones de glucosa del usuario.

## 8. Flujos alternativos

### FA01. Consulta sin filtros

1. El usuario abre el catálogo sin escribir un nombre ni seleccionar una categoría.
2. El sistema presenta los alimentos habilitados en orden alfabético.
3. El usuario puede seleccionar un alimento o aplicar filtros.

### FA02. Búsqueda por nombre parcial

1. El usuario introduce una parte del nombre.
2. El sistema busca coincidencias sin distinguir mayúsculas y minúsculas.
3. El sistema muestra los resultados coincidentes en orden alfabético.

### FA03. Filtro por categoría

1. El usuario selecciona una categoría válida.
2. El sistema recupera los alimentos de esa categoría.
3. Los resultados se presentan alfabéticamente.

### FA04. Búsqueda combinada

1. El usuario introduce un nombre y selecciona una categoría.
2. El sistema aplica ambos criterios.
3. Se presentan únicamente los alimentos que cumplen las dos condiciones.

### FA05. Sin coincidencias

1. El usuario realiza una búsqueda válida.
2. No existen alimentos que coincidan con los criterios.
3. El sistema informa que no hay resultados y permite cambiar la búsqueda.

### FA06. Cambio de criterios

1. El usuario modifica el nombre o la categoría.
2. El sistema ejecuta una nueva consulta.
3. Los resultados anteriores son sustituidos por los nuevos resultados.

## 9. Flujos de excepción

### FE01. Criterios inválidos

El sistema rechaza criterios que superen los límites de longitud o formato, informa el problema y solicita su corrección.

### FE02. Error de consulta

El sistema informa que la consulta no pudo completarse. No presenta resultados parciales como si fueran completos o actualizados.

### FE03. Sesión expirada

El sistema solicita una nueva autenticación y no devuelve el contenido protegido hasta validar la sesión.

### FE04. Alimento deshabilitado

Si el alimento seleccionado deja de estar habilitado antes de abrir CU11, el sistema informa que ya no está disponible y regresa al catálogo.

## 10. Reglas de negocio

- **RN-CU10-01.** El acceso al catálogo requiere una sesión válida de usuario autenticado.
- **RN-CU10-02.** Solo se mostrarán alimentos habilitados para consulta ordinaria.
- **RN-CU10-03.** La búsqueda admite nombre completo o parcial y no distingue mayúsculas y minúsculas.
- **RN-CU10-04.** Los filtros disponibles en la versión inicial son nombre y categoría.
- **RN-CU10-05.** Cuando se combinen nombre y categoría, ambos criterios deberán cumplirse.
- **RN-CU10-06.** Los resultados se ordenarán alfabéticamente por nombre.
- **RN-CU10-07.** Si el número de resultados supera el límite de presentación, se utilizará paginación o un mecanismo equivalente.
- **RN-CU10-08.** El catálogo inicial estará limitado a entre 50 y 100 alimentos y las seis categorías especificadas en Visión y Alcance.
- **RN-CU10-09.** Los alimentos ultraprocesados y los productos de marcas comerciales específicas quedan fuera del catálogo inicial.
- **RN-CU10-10.** La consulta de un alimento no se considerará registro de consumo.
- **RN-CU10-11.** El sistema no asociará la consulta del catálogo con mediciones personales de glucosa.
- **RN-CU10-12.** El sistema no usará las mediciones de glucosa para ordenar, filtrar o personalizar los resultados alimenticios.
- **RN-CU10-13.** La categoría general de impacto glucémico solo se mostrará cuando haya una metodología documentada y validada.
- **RN-CU10-14.** La ausencia de categoría de impacto no impedirá consultar el alimento y no dará lugar a una categoría inventada.
- **RN-CU10-15.** El catálogo no generará dietas, menús, cantidades terapéuticas ni recomendaciones personalizadas.
- **RN-CU10-16.** La consulta no modificará los alimentos ni sus datos nutricionales.

## 11. Requisitos funcionales asociados

- **RF-CU10-01.** El sistema debe permitir a un usuario autenticado ingresar al catálogo.
- **RF-CU10-02.** Debe permitir buscar por nombre completo o parcial.
- **RF-CU10-03.** Debe realizar la búsqueda sin distinguir mayúsculas y minúsculas.
- **RF-CU10-04.** Debe permitir filtrar los alimentos por categoría.
- **RF-CU10-05.** Debe aplicar correctamente los filtros combinados.
- **RF-CU10-06.** Debe ordenar los resultados alfabéticamente.
- **RF-CU10-07.** Debe permitir consultar el catálogo sin filtros.
- **RF-CU10-08.** Debe presentar un mensaje cuando no existan coincidencias.
- **RF-CU10-09.** Debe permitir modificar los criterios y repetir la búsqueda.
- **RF-CU10-10.** Debe permitir seleccionar un alimento para abrir CU11.
- **RF-CU10-11.** Debe excluir de la consulta ordinaria los alimentos deshabilitados.
- **RF-CU10-12.** Debe controlar el acceso mediante autenticación y autorización en el servidor.
- **RF-CU10-13.** Debe mostrar la categoría de impacto glucémico solo cuando haya sido validada.
- **RF-CU10-14.** No debe vincular las consultas de alimentos con mediciones personales.
- **RF-CU10-15.** No debe registrar una consulta como consumo de alimento.
- **RF-CU10-16.** No debe generar dietas ni recomendaciones clínicas personalizadas.

## 12. Seguridad, privacidad y calidad

1. Los criterios de búsqueda se validarán tanto en la interfaz como en el backend.
2. Las consultas a la base de datos utilizarán mecanismos seguros para prevenir inyección SQL.
3. El backend verificará la sesión del usuario.
4. El catálogo no consultará ni modificará los registros personales de glucosa.
5. Las consultas al catálogo no se utilizarán para inferir consumo ni para crear un perfil alimentario asociado a mediciones.
6. Los errores no expondrán consultas internas, estructura de base de datos ni detalles sensibles de infraestructura.
7. Los registros del catálogo deberán mantener consistencia entre nombre, categoría y estado de disponibilidad.

## 13. Criterios de aceptación

- **CA-CU10-01.** Un usuario autenticado puede acceder al catálogo.
- **CA-CU10-02.** La búsqueda por nombre completo devuelve las coincidencias existentes.
- **CA-CU10-03.** La búsqueda parcial funciona sin distinguir mayúsculas y minúsculas.
- **CA-CU10-04.** Un filtro por categoría muestra los alimentos de esa categoría.
- **CA-CU10-05.** Una búsqueda combinada aplica ambos criterios.
- **CA-CU10-06.** Los resultados aparecen en orden alfabético.
- **CA-CU10-07.** La consulta sin filtros presenta el catálogo habilitado conforme a la paginación.
- **CA-CU10-08.** Una búsqueda sin coincidencias presenta un mensaje comprensible.
- **CA-CU10-09.** El usuario puede seleccionar un alimento para abrir CU11.
- **CA-CU10-10.** Los alimentos deshabilitados no aparecen en las consultas ordinarias.
- **CA-CU10-11.** La categoría de impacto glucémico no se presenta sin validación documentada.
- **CA-CU10-12.** Consultar un alimento no registra su consumo ni modifica el catálogo.
- **CA-CU10-13.** La consulta no recupera, cruza ni presenta mediciones personales de glucosa.
- **CA-CU10-14.** El sistema no genera dietas ni recomendaciones personalizadas.

## 14. Fuera del alcance

- Crear, editar o eliminar alimentos desde la interfaz de consulta.
- Administrar categorías.
- Registrar consumos alimentarios.
- Cruzar alimentos consultados con mediciones personales.
- Personalizar el catálogo con base en el historial de glucosa.
- Generar dietas, menús o recomendaciones clínicas.
- Diagnosticar, tratar o predecir respuestas individuales de glucosa.