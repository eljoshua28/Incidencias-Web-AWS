# Incidencias Web

## Descripción del proyecto

Incidencias Web es una aplicación web que permite registrar, consultar, actualizar y eliminar incidencias. Está desarrollada utilizando servicios de AWS bajo una arquitectura serverless, evitando la necesidad de administrar servidores físicos.

## Arquitectura del sistema

El proyecto utiliza los siguientes servicios:

- **Amazon S3:** aloja la página web estática.
- **Amazon API Gateway:** recibe y administra las solicitudes HTTP.
- **AWS Lambda:** ejecuta la lógica del sistema mediante Python.
- **Amazon DynamoDB:** almacena la información de las incidencias.
- **Amazon CloudWatch:** registra la actividad y los eventos de la función Lambda.

### Flujo de funcionamiento

1. El usuario accede a la página web alojada en S3.
2. La aplicación envía solicitudes a API Gateway.
3. API Gateway ejecuta la función Lambda correspondiente.
4. Lambda consulta o modifica los registros almacenados en DynamoDB.
5. La respuesta se devuelve a la aplicación web.
6. CloudWatch almacena los registros de ejecución.

## Tecnologías utilizadas

- Python 3.13
- Boto3
- HTML
- CSS
- JavaScript
- Amazon S3
- Amazon API Gateway
- AWS Lambda
- Amazon DynamoDB
- Amazon CloudWatch

## Direcciones del proyecto

**Página web:**

http://incidencias-web-060599493870-2026.s3-website-us-east-1.amazonaws.com

**API:**

https://mpufe9cgw5.execute-api.us-east-1.amazonaws.com

## Rutas de la API

| Método | Ruta | Función |
|---|---|---|
| GET | /incidencias | Consultar incidencias |
| POST | /incidencias | Registrar una incidencia |
| PATCH | /incidencias/{id} | Actualizar su estado |
| DELETE | /incidencias/{id} | Eliminar una incidencia |

## Estructura del proyecto

```text
proyecto-incidencias/
│
├── backend/
│   └── lambda_function.py
│
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
│
├── infraestructura/
│   ├── crear_infraestructura.py
│   └── lambda.zip
│
├── politica-s3.json
├── README.md
├── respuesta.json
└── verificar_aws.py
```

## Despliegue de infraestructura

El proyecto incluye un script desarrollado con Boto3 que permite crear o actualizar los recursos necesarios en AWS.

Para ejecutar el despliegue:

```bash
python3 infraestructura/crear_infraestructura.py
```

## Verificación del sistema

El archivo `verificar_aws.py` permite comprobar la conexión con AWS y el estado de los servicios utilizados.

Para ejecutarlo:

```bash
python3 verificar_aws.py
```

El programa verifica:

- Conexión con AWS.
- Estado de la tabla DynamoDB.
- Estado de la función Lambda.
- Existencia de API Gateway.
- Archivos publicados en S3.
- Grupo de registros de CloudWatch.
- Respuesta de la API.

## Consideraciones

La aplicación utiliza una arquitectura serverless, por lo que no requiere administrar servidores para procesar las solicitudes.

La página web utiliza el endpoint HTTP de alojamiento estático de S3. La API tiene CORS habilitado y actualmente no implementa autenticación de usuarios. Estas características pueden mejorarse en futuras versiones.

## Región de AWS

Todos los recursos del proyecto se encuentran desplegados en:

`us-east-1` (Norte de Virginia).

## Estado del proyecto

La aplicación se encuentra desplegada y sus operaciones principales han sido probadas. La verificación de infraestructura confirmó la disponibilidad de los servicios utilizados.
