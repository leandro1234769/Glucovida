# Documentos legales y evidencias de GlucoVida

Los documentos de desarrollo son borradores sujetos a revision juridica.
El repositorio contiene un ejemplar de cada version, su estado y su SHA-256
en `backend/app/legal/documents/`. El hash se calcula sobre UTF-8 con saltos
LF. Conserva las entradas y archivos anteriores. Si cambia el texto, asigna
una nueva version y registra su hash. Los archivos de prueba son exclusivos
del entorno test.

| Documento | Version provisional | Decision |
|---|---|---|
| Terminos y condiciones | terms-v1.0.0 | Aceptacion afirmativa obligatoria |
| Politica de privacidad | privacy-v1.0.0 | Constancia afirmativa de lectura |
| Autorizacion expresa de datos de salud | health-data-v1.0.0 | Decision separada y opcional |

## Aprobacion y despliegue

1. Adjunta la revision juridica del texto final. Registra en el manifiesto
   el estado `approved`, la fecha `approved_at` y la referencia interna
   `approval_reference` del documento exacto aprobado. El cambio debe
   revisarse junto con el hash del texto.
2. Configura el entorno production con las tres versiones aprobadas.
   Verifica el dominio, HTTPS, la cuenta Brevo, el remitente y el envio
   transaccional antes de marcar la aprobacion operativa.
3. Solo entonces activa `GLUCOVIDA_PRODUCTION_RELEASE_APPROVED=true` y
   `GLUCOVIDA_PUBLIC_REGISTRATION_ENABLED=true` en el despliegue. La puerta
   de produccion rechaza borradores, documentos de prueba y una
   configuracion Brevo incompleta.

## Evidencia

PostgreSQL conserva una fila por decision con el usuario, el documento,
la version, el estado, el SHA-256 y la fecha UTC. Los cambios de decision
agregan nuevas filas. Un trigger impide actualizar o borrar evidencia
directamente. La eliminacion de una cuenta aplica su politica de borrado
en cascada. La politica definitiva de conservacion, supresion, acceso y
revision juridica debe quedar aprobada antes de operar con datos reales.

Las filas de la anterior tabla `registration_consents` se conservan como
historial legado. Los usuarios de ese esquema deben actualizar sus
decisiones para disponer de una evidencia completa. La migracion no
atribuye retrospectivamente una lectura de la politica de privacidad.

Como referentes para la revision, consulta los articulos 5, 6, 9 y 12 de la
[Ley 1581 de 2012](https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=49981).
