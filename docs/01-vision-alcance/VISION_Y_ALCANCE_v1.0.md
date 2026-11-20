# GlucoVida
## Documento de Visión, Alcance y Requisitos Generales

**Versión:** 1.2  
**Tipo de documento:** Visión, alcance, requisitos generales y reglas transversales  
**Producto:** Aplicación web GlucoVida  
**Estado:** Alcance funcional actualizado para el MVP

## 1. Introducción

GlucoVida es una aplicación web orientada a registrar, organizar y visualizar mediciones personales de glucosa, complementada con un catálogo informativo sobre la composición nutricional de los alimentos y su posible impacto glucémico general.

La aplicación busca facilitar que los usuarios mantengan un historial organizado de sus mediciones, consulten estadísticas descriptivas, visualicen su evolución temporal y accedan a información nutricional comprensible y respaldada por fuentes confiables.

Para la primera versión, GlucoVida adopta un enfoque informativo y educativo. No elaborará dietas, planes de alimentación personalizados ni prescripciones; tampoco diagnosticará enfermedades, recomendará tratamientos o predecirá la respuesta individual de glucosa ante un alimento.

El catálogo de alimentos y la gestión de mediciones personales serán funcionalidades independientes. Consultar un alimento no significa que el usuario lo haya consumido, y GlucoVida no asociará las consultas del catálogo con las mediciones personales de glucosa.

## 2. Descripción del problema

Las personas que registran sus niveles de glucosa pueden necesitar una forma organizada de guardar sus mediciones, revisar valores anteriores y observar sus cambios a lo largo del tiempo. También pueden buscar información nutricional general para comprender mejor la composición de los alimentos.

Cuando estos datos se encuentran dispersos o se presentan sin referencias claras, puede resultar más difícil revisarlos y comprenderlos. GlucoVida busca responder a esa necesidad mediante una aplicación que reúna la gestión de mediciones, las estadísticas descriptivas, la visualización de la evolución y un catálogo informativo de alimentos.

La solución no pretende determinar qué debe comer una persona ni establecer relaciones clínicas entre un alimento y una medición individual. Su finalidad es ofrecer herramientas de organización y consulta de información, manteniendo límites claros frente a la atención profesional en salud.

## 3. Visión del producto

Desarrollar una aplicación web segura y comprensible que permita gestionar mediciones personales de glucosa, consultar estadísticas y gráficas históricas, y acceder de forma independiente a información nutricional general sobre alimentos, con énfasis en su contenido de carbohidratos y su posible impacto glucémico.

GlucoVida priorizará la integridad de los datos, la privacidad, la trazabilidad de las fuentes, la claridad de la información y una delimitación responsable de sus funcionalidades.

## 4. Objetivo general

Desarrollar una aplicación web que permita a los usuarios gestionar sus propias mediciones de glucosa, consultar estadísticas y visualizar su evolución temporal, así como buscar alimentos y consultar información nutricional general sobre su composición y posible impacto glucémico, sin generar dietas, prescripciones, diagnósticos ni correlaciones entre alimentos consultados y mediciones individuales.

## 5. Objetivos específicos

1. Permitir el registro seguro de usuarios y la administración de sus cuentas.
2. Facilitar el registro de mediciones de glucosa con fecha, hora, unidad y contexto opcional.
3. Permitir consultar, editar y eliminar las mediciones propias del usuario bajo las reglas definidas.
4. Presentar estadísticas descriptivas de las mediciones registradas.
5. Visualizar la evolución temporal de las mediciones mediante gráficas cronológicas.
6. Proporcionar un catálogo limitado de alimentos frecuentes en el contexto colombiano.
7. Mostrar información nutricional disponible con unidades y cantidades de referencia claras.
8. Mostrar una categoría general de impacto glucémico únicamente cuando exista una metodología documentada y validada.
9. Mantener la procedencia y trazabilidad de la información nutricional.
10. Proteger los datos personales y sensibles mediante controles de acceso, minimización y medidas de seguridad adecuadas.

## 6. Usuarios y actores

### 6.1. Usuario registrado

Persona con una cuenta activa que puede gestionar sus mediciones de glucosa y consultar estadísticas, gráficas y el catálogo informativo conforme a los permisos de la aplicación.

### 6.2. Profesional competente en nutrición o salud

Responsable de revisar la exactitud y pertinencia de los datos nutricionales o del contenido educativo dentro de su ámbito de competencia. Su participación en la validación de contenidos no significa que la aplicación preste atención clínica individual.

### 6.3. Administrador técnico de contenidos

Responsable de la gestión técnica del catálogo, la incorporación de datos previamente revisados, la tramitación de reportes y la trazabilidad de las modificaciones. No sustituye la validación profesional de la información nutricional.

### 6.4. Responsable del tratamiento de datos personales

Rol organizacional responsable de atender las obligaciones de privacidad, las autorizaciones y las solicitudes de los titulares. Debe distinguirse de la administración técnica del catálogo y de la revisión nutricional.

## 7. Alcance funcional del MVP

### 7.1. Gestión de cuentas

- Registro de usuarios.
- Verificación de correo electrónico.
- Inicio y cierre de sesión.
- Consulta y edición de los datos permitidos del perfil.
- Cambio de contraseña.
- Control de sesiones, autenticación y autorización.

### 7.2. Gestión de mediciones de glucosa

- Registrar valores en mg/dL o mmol/L.
- Registrar fecha y hora de la medición.
- Registrar contexto opcional y observaciones.
- Consultar el historial propio.
- Editar mediciones existentes conforme a las reglas del sistema.
- Eliminar mediciones mediante eliminación lógica y aplicar la política de retención definida.

### 7.3. Estadísticas descriptivas

- Contar las mediciones del período consultado.
- Calcular promedio, mínimo y máximo.
- Filtrar por intervalo de fechas y contexto de la medición.
- Elegir la unidad de presentación cuando corresponda.
- Convertir unidades para presentar los resultados sin modificar los valores originales.
- Informar cuando no existan suficientes datos para realizar la consulta.

Estas funciones describen los registros existentes. No determinan diagnósticos, tratamientos, causas de cambios en la glucosa ni relaciones con alimentos.

### 7.4. Visualización de evolución

- Mostrar las mediciones en una gráfica cronológica.
- Permitir consultar períodos de 7, 30 y 90 días, además de un intervalo personalizado.
- Permitir seleccionar la unidad de presentación.
- Facilitar la exploración de gráficas densas sin eliminar registros de la consulta.
- Representar únicamente las mediciones registradas, sin predicciones ni valores clínicos inferidos.

Las líneas que conecten los puntos de la gráfica serán una ayuda visual para ordenar las mediciones en el tiempo. No deberán interpretarse como mediciones intermedias reales ni como una predicción.

### 7.5. Catálogo informativo de alimentos

- Permitir buscar alimentos por nombre completo o parcial.
- Permitir filtrar por categoría.
- Ordenar los resultados alfabéticamente.
- Limitar el catálogo inicial a entre 50 y 100 alimentos.
- Consultar composición nutricional por 100 gramos y por porción cuando existan datos suficientes.
- Mostrar fuentes y fechas de actualización cuando estén registradas.
- Permitir consultar cantidades personalizadas mediante cálculos informativos, cuando los datos disponibles lo permitan.
- Presentar una categoría general de impacto glucémico solo cuando exista metodología documentada y validación profesional.
- Habilitar un mecanismo de reporte de discrepancias en los datos nutricionales.

El catálogo no registra alimentos consumidos por un usuario. La búsqueda, visualización o cálculo de nutrientes de un alimento no se asociará con sus mediciones personales.

### 7.6. Contenido educativo

- Proporcionar información general sobre glucosa y composición nutricional.
- Utilizar fuentes científicas o institucionales confiables.
- Someter los contenidos a revisión profesional antes de publicarlos.
- Mostrar un aviso educativo claro en los módulos y artículos correspondientes.

## 8. Catálogo inicial y categorías

El catálogo inicial estará limitado a entre 50 y 100 alimentos frecuentes en el contexto colombiano.

Categorías previstas:

1. Cereales, tubérculos, raíces y plátanos.
2. Frutas y jugos naturales.
3. Verduras y hortalizas.
4. Proteínas y carnes.
5. Lácteos y derivados.
6. Bebidas, infusiones y edulcorantes.

Los alimentos deberán estandarizarse por cada 100 gramos o por porciones caseras claramente documentadas. Los alimentos ultraprocesados y los productos de marcas comerciales específicas se excluyen de la primera versión.

La selección de alimentos, sus datos nutricionales y su clasificación informativa estarán sujetos al proceso de revisión y mantenimiento del catálogo.

## 9. Clasificación general del impacto glucémico

GlucoVida podrá presentar categorías informativas de impacto glucémico bajo, moderado o alto únicamente cuando exista una metodología documentada, apropiada para el objetivo informativo y validada por un profesional competente.

Estas categorías:

- Describirán una clasificación general del alimento bajo los criterios definidos.
- No predecirán la variación individual de la glucosa de un usuario.
- No afirmarán que un alimento es universalmente seguro o peligroso.
- No se utilizarán para generar dietas, menús ni recomendaciones personalizadas.
- No reemplazarán la información nutricional detallada.
- No se mostrarán si no existe una clasificación validada para el alimento.

El contenido de carbohidratos o azúcares deberá mostrarse como un dato nutricional separado. No se deberá asignar automáticamente una categoría de impacto usando únicamente una cantidad de carbohidratos, salvo que el método validado establezca expresamente esa regla.

## 10. Exclusiones explícitas

La versión 1 no incluirá:

1. Elaboración de dietas ni planes alimenticios personalizados.
2. Generación de menús diarios, semanales o mensuales.
3. Recomendaciones de qué comer en cada comida.
4. Prescripción de porciones con finalidad terapéutica.
5. Recomendaciones de medicamentos o ajustes de dosis.
6. Diagnóstico de diabetes, hipoglucemia u otras condiciones.
7. Predicción individual del efecto de un alimento sobre la glucosa.
8. Correlación entre alimentos consultados y mediciones individuales.
9. Registro de alimentos consumidos.
10. Análisis de consumo alimentario contra mediciones de glucosa.
11. Alertas clínicas o interpretación médica automatizada.
12. Integración con dispositivos médicos o servicios de monitorización continua.
13. Seguimiento clínico individual desde la plataforma.

No se creará un caso de uso para registrar consumo ni para correlacionar consultas de alimentos con mediciones. Una posible funcionalidad futura requeriría una modificación formal del alcance y no forma parte de esta versión.

## 11. Reglas generales de negocio

- **RN-GEN-01.** Cada usuario solo podrá consultar y gestionar sus propias mediciones de glucosa, conforme a los permisos definidos.
- **RN-GEN-02.** Las estadísticas y gráficas describirán exclusivamente mediciones registradas.
- **RN-GEN-03.** Una consulta nutricional no producirá diagnósticos ni recomendaciones clínicas individualizadas.
- **RN-GEN-04.** Las conversiones de unidades deberán ser explícitas y no modificarán los valores originales almacenados.
- **RN-GEN-05.** El catálogo de alimentos será independiente del historial personal de glucosa.
- **RN-GEN-06.** El sistema no vinculará búsquedas, consultas o cálculos nutricionales con mediciones personales.
- **RN-GEN-07.** La consulta de un alimento no se considerará una prueba de que el usuario lo consumió.
- **RN-GEN-08.** Los datos nutricionales deberán contar con fuente y referencia de cantidad documentadas.
- **RN-GEN-09.** Las categorías de impacto glucémico solo podrán mostrarse con una metodología documentada y validada.
- **RN-GEN-10.** Los datos nutricionales faltantes se identificarán como no disponibles y no se inventarán.
- **RN-GEN-11.** Las correcciones del catálogo conservarán la trazabilidad de los cambios.
- **RN-GEN-12.** El contenido educativo deberá someterse a revisión antes de su publicación.
- **RN-GEN-13.** No se generarán dietas, menús, prescripciones ni tratamientos personalizados.
- **RN-GEN-14.** El acceso y tratamiento de datos sensibles estarán sujetos a las autorizaciones y garantías aplicables.
- **RN-GEN-15.** Los datos personales no se utilizarán para fines comerciales incompatibles con los informados al titular.

## 12. Requisitos funcionales generales

- **RF-GEN-01.** El sistema debe autenticar a los usuarios y controlar el acceso a los recursos protegidos.
- **RF-GEN-02.** El sistema debe permitir al usuario gestionar únicamente sus propias mediciones.
- **RF-GEN-03.** El sistema debe conservar la unidad y el valor originales de cada medición.
- **RF-GEN-04.** El sistema debe presentar estadísticas descriptivas de las mediciones registradas.
- **RF-GEN-05.** El sistema debe presentar las mediciones en gráficas cronológicas.
- **RF-GEN-06.** El sistema debe permitir buscar alimentos por nombre y filtrar por categoría.
- **RF-GEN-07.** El sistema debe presentar información nutricional disponible, con unidades y cantidades de referencia.
- **RF-GEN-08.** El sistema debe mostrar la procedencia de los datos nutricionales cuando esté registrada.
- **RF-GEN-09.** El sistema solo debe presentar una categoría de impacto glucémico si está validada.
- **RF-GEN-10.** El sistema debe permitir reportar discrepancias en la información nutricional.
- **RF-GEN-11.** El sistema debe distinguir los valores originales de los valores calculados para otras cantidades.
- **RF-GEN-12.** El sistema no debe generar correlaciones entre consultas de alimentos y mediciones personales.
- **RF-GEN-13.** El sistema no debe registrar consultas de alimentos como consumos.
- **RF-GEN-14.** El sistema no debe generar dietas, menús ni recomendaciones clínicas personalizadas.

## 13. Requisitos no funcionales y de seguridad

- **RNF-GEN-01. Seguridad de autenticación:** las contraseñas deben almacenarse mediante hash seguro, y las sesiones deben contar con controles de expiración y protección.
- **RNF-GEN-02. Autorización:** los controles de acceso deben aplicarse en el backend y no depender únicamente de la interfaz.
- **RNF-GEN-03. Protección de datos:** las mediciones y demás datos sensibles deben protegerse durante la transmisión y el almacenamiento mediante controles apropiados.
- **RNF-GEN-04. Integridad:** los cambios en las mediciones y en el catálogo deben mantener la consistencia de los datos.
- **RNF-GEN-05. Auditoría:** los cambios del catálogo deberán registrar quién modificó la información, cuándo y por qué.
- **RNF-GEN-06. Usabilidad:** la aplicación debe presentar valores, unidades, mensajes de error y estados vacíos de forma comprensible.
- **RNF-GEN-07. Confiabilidad informativa:** el sistema no presentará valores nutricionales faltantes o datos no verificados como hechos confirmados.
- **RNF-GEN-08. Mantenibilidad:** los datos nutricionales, las fuentes y las categorías de clasificación deberán poder revisarse sin modificar la lógica de gestión de las mediciones personales.
- **RNF-GEN-09. Privacidad:** el sistema no unirá el historial de glucosa con consultas del catálogo ni utilizará esta información para fines incompatibles con los comunicados al usuario.
- **RNF-GEN-10. Manejo de errores:** los mensajes al usuario no expondrán consultas internas, credenciales ni detalles sensibles de la infraestructura.

## 14. Validación y mantenimiento del catálogo

La información nutricional será revisada por un nutricionista o dietista clínico cualificado antes de incorporarse al catálogo maestro. El administrador técnico gestionará la estructura de los registros y las modificaciones aprobadas.

Se dispondrá de un canal de reporte de discrepancias. Cada corrección deberá generar una auditoría con el responsable, la fecha y la justificación del cambio.

Se realizarán revisiones trimestrales contra fuentes nutricionales oficiales, institucionales o reconocidas. El contenido educativo deberá contar con revisión profesional y referencias verificables.

## 15. Contenido educativo y aviso de responsabilidad

Los textos educativos deberán fundamentarse en fuentes científicas e institucionales confiables y pasar por una revisión profesional antes de su publicación.

El siguiente aviso deberá presentarse de forma clara en los módulos y artículos educativos:

“Esta información es exclusivamente de carácter educativo e informativo y no constituye un diagnóstico médico, prescripción ni reemplaza la valoración de un profesional de la salud competente”.

El aviso no sustituye la obligación de presentar información correcta ni convierte en aceptable una clasificación que carezca de respaldo.

## 16. Privacidad y protección de datos

Las mediciones de glucosa y los datos de salud vinculados a una cuenta serán tratados como datos sensibles. La aplicación deberá limitar el tratamiento a finalidades informadas, proteger los accesos y recoger la autorización correspondiente conforme a los requisitos legales aplicables.

Las consultas nutricionales no deberán cruzarse con mediciones personales ni utilizarse para marketing o perfilamiento comercial. Los proveedores técnicos que eventualmente procesen información deberán gestionarse conforme a las garantías y condiciones jurídicas aplicables.

Las funciones que requieran tratamiento de datos sensibles estarán sujetas a las autorizaciones correspondientes. El acceso al catálogo no debe utilizarse como justificación para recolectar datos de salud innecesarios.

## 17. Criterios generales de aceptación del MVP

1. Los usuarios pueden registrarse y acceder mediante un mecanismo seguro.
2. Los usuarios pueden gestionar exclusivamente sus propias mediciones.
3. Las estadísticas corresponden a los registros reales y respetan los filtros definidos.
4. Las gráficas presentan mediciones cronológicas sin interpolar predicciones.
5. El catálogo permite buscar alimentos por nombre y categoría.
6. La información nutricional presenta unidades, referencias de cantidad y fuentes cuando estén disponibles.
7. Las categorías de impacto glucémico no se muestran sin validación documentada.
8. Las consultas de alimentos no se convierten en registros de consumo.
9. No existe una función que correlacione alimentos consultados y mediciones de glucosa.
10. El sistema no genera dietas ni recomendaciones clínicas personalizadas.
11. Las correcciones del catálogo mantienen su trazabilidad.
12. Los controles de seguridad y privacidad se verifican mediante pruebas.

## 18. Declaración de alcance

GlucoVida es una aplicación web para la gestión y visualización de mediciones personales de glucosa, acompañada de un catálogo independiente con información nutricional general y, cuando proceda, una clasificación validada del posible impacto glucémico de los alimentos.

La aplicación organiza información y facilita su consulta, sin realizar diagnósticos, tratamientos, planes de alimentación personalizados ni asociaciones entre alimentos consultados y mediciones personales.