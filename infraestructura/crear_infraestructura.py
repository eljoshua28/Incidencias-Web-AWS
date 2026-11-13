import boto3
import json
import zipfile
import time
from pathlib import Path
from botocore.exceptions import ClientError

REGION = "us-east-1"
NOMBRE_TABLA = "IncidenciasWeb"
NOMBRE_LAMBDA = "GestionarIncidencias"
NOMBRE_API = "API-IncidenciasWeb"
NOMBRE_BUCKET = "incidencias-web-060599493870-2026"

sesion = boto3.Session(region_name=REGION)

dynamodb = sesion.client("dynamodb")
lambda_client = sesion.client("lambda")
apigateway = sesion.client("apigatewayv2")
s3 = sesion.client("s3")
sts = sesion.client("sts")

CUENTA = sts.get_caller_identity()["Account"]
ROL_LAMBDA = f"arn:aws:iam::{CUENTA}:role/LabRole"

BASE = Path(__file__).resolve().parent.parent


def crear_tabla():
    print("\nRevisando DynamoDB...")

    try:
        dynamodb.describe_table(TableName=NOMBRE_TABLA)
        print("La tabla ya existe.")
    except dynamodb.exceptions.ResourceNotFoundException:
        dynamodb.create_table(
            TableName=NOMBRE_TABLA,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST"
        )

        dynamodb.get_waiter("table_exists").wait(
            TableName=NOMBRE_TABLA
        )
        print("Tabla creada correctamente.")


def crear_lambda():
    print("\nRevisando función Lambda...")

    archivo = BASE / "backend" / "lambda_function.py"
    comprimido = BASE / "infraestructura" / "lambda.zip"

    with zipfile.ZipFile(comprimido, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(archivo, "backend/lambda_function.py")

    with open(comprimido, "rb") as f:
        codigo = f.read()

    try:
        lambda_client.get_function(FunctionName=NOMBRE_LAMBDA)

        lambda_client.update_function_code(
            FunctionName=NOMBRE_LAMBDA,
            ZipFile=codigo
        )

        lambda_client.get_waiter("function_updated").wait(
            FunctionName=NOMBRE_LAMBDA
        )

        lambda_client.update_function_configuration(
            FunctionName=NOMBRE_LAMBDA,
            Runtime="python3.13",
            Role=ROL_LAMBDA,
            Handler="backend/lambda_function.lambda_handler",
            Timeout=15,
            MemorySize=128,
            Environment={
                "Variables": {"TABLE_NAME": NOMBRE_TABLA}
            }
        )

        lambda_client.get_waiter("function_updated").wait(
            FunctionName=NOMBRE_LAMBDA
        )

        print("Función Lambda actualizada.")

    except lambda_client.exceptions.ResourceNotFoundException:
        lambda_client.create_function(
            FunctionName=NOMBRE_LAMBDA,
            Runtime="python3.13",
            Role=ROL_LAMBDA,
            Handler="backend/lambda_function.lambda_handler",
            Code={"ZipFile": codigo},
            Timeout=15,
            MemorySize=128,
            Environment={
                "Variables": {"TABLE_NAME": NOMBRE_TABLA}
            }
        )

        lambda_client.get_waiter("function_active").wait(
            FunctionName=NOMBRE_LAMBDA
        )

        print("Función Lambda creada.")

    return lambda_client.get_function(
        FunctionName=NOMBRE_LAMBDA
    )["Configuration"]["FunctionArn"]


def crear_api(lambda_arn):
    print("\nRevisando API Gateway...")

    apis = apigateway.get_apis()["Items"]
    api = next(
        (a for a in apis if a["Name"] == NOMBRE_API),
        None
    )

    cors = {
        "AllowOrigins": ["*"],
        "AllowMethods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        "AllowHeaders": ["content-type"]
    }

    if api:
        api_id = api["ApiId"]
        apigateway.update_api(
            ApiId=api_id,
            CorsConfiguration=cors
        )
        print("Se reutilizará la API existente:", api_id)
    else:
        api = apigateway.create_api(
            Name=NOMBRE_API,
            ProtocolType="HTTP",
            CorsConfiguration=cors
        )
        api_id = api["ApiId"]
        print("API creada:", api_id)

    integraciones = apigateway.get_integrations(
        ApiId=api_id
    )["Items"]

    integracion = next(
        (
            i for i in integraciones
            if i.get("IntegrationUri") == lambda_arn
            and i.get("IntegrationType") == "AWS_PROXY"
        ),
        None
    )

    if integracion:
        integration_id = integracion["IntegrationId"]
        print("Integración existente reutilizada.")
    else:
        integracion = apigateway.create_integration(
            ApiId=api_id,
            IntegrationType="AWS_PROXY",
            IntegrationUri=lambda_arn,
            PayloadFormatVersion="2.0",
            TimeoutInMillis=30000
        )
        integration_id = integracion["IntegrationId"]
        print("Integración creada.")

    rutas = [
        "GET /incidencias",
        "POST /incidencias",
        "PATCH /incidencias/{id}",
        "DELETE /incidencias/{id}"
    ]

    rutas_existentes = apigateway.get_routes(
        ApiId=api_id
    )["Items"]

    for ruta in rutas:
        existente = next(
            (r for r in rutas_existentes if r["RouteKey"] == ruta),
            None
        )

        destino = "integrations/" + integration_id

        if existente:
            if existente.get("Target") != destino:
                apigateway.update_route(
                    ApiId=api_id,
                    RouteId=existente["RouteId"],
                    Target=destino
                )
            print("Ruta existente:", ruta)
        else:
            apigateway.create_route(
                ApiId=api_id,
                RouteKey=ruta,
                Target=destino
            )
            print("Ruta creada:", ruta)

    etapas = apigateway.get_stages(ApiId=api_id)["Items"]

    if not any(e["StageName"] == "$default" for e in etapas):
        apigateway.create_stage(
            ApiId=api_id,
            StageName="$default",
            AutoDeploy=True
        )
        print("Etapa $default creada.")
    else:
        print("Etapa $default existente.")

    try:
        lambda_client.add_permission(
            FunctionName=NOMBRE_LAMBDA,
            StatementId="PermisoAPI" + api_id,
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=(
                f"arn:aws:execute-api:{REGION}:"
                f"{CUENTA}:{api_id}/*/*/*"
            )
        )
        print("Permiso de API Gateway agregado.")
    except lambda_client.exceptions.ResourceConflictException:
        print("El permiso de API Gateway ya existe.")

    return apigateway.get_api(
        ApiId=api_id
    )["ApiEndpoint"]


def publicar_s3():
    print("\nRevisando bucket S3...")

    try:
        s3.head_bucket(Bucket=NOMBRE_BUCKET)
        print("El bucket ya existe.")
    except ClientError as error:
        codigo = error.response["Error"]["Code"]
        if codigo not in ["404", "NoSuchBucket", "NotFound"]:
            raise

        s3.create_bucket(Bucket=NOMBRE_BUCKET)
        print("Bucket creado.")

    s3.put_public_access_block(
        Bucket=NOMBRE_BUCKET,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": False,
            "IgnorePublicAcls": False,
            "BlockPublicPolicy": False,
            "RestrictPublicBuckets": False
        }
    )

    s3.put_bucket_website(
        Bucket=NOMBRE_BUCKET,
        WebsiteConfiguration={
            "IndexDocument": {"Suffix": "index.html"},
            "ErrorDocument": {"Key": "index.html"}
        }
    )

    politica = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::{NOMBRE_BUCKET}/*"
        }]
    }

    s3.put_bucket_policy(
        Bucket=NOMBRE_BUCKET,
        Policy=json.dumps(politica)
    )

    frontend = BASE / "frontend"

    tipos = {
        ".html": "text/html",
        ".css": "text/css",
        ".js": "application/javascript"
    }

    for archivo in frontend.iterdir():
        if archivo.is_file():
            s3.upload_file(
                str(archivo),
                NOMBRE_BUCKET,
                archivo.name,
                ExtraArgs={
                    "ContentType": tipos.get(
                        archivo.suffix,
                        "application/octet-stream"
                    )
                }
            )
            print("Archivo publicado:", archivo.name)

    print("Frontend publicado correctamente.")


def main():
    print("================================")
    print(" DESPLIEGUE DE INCIDENCIAS WEB")
    print("================================")

    crear_tabla()

    lambda_arn = crear_lambda()

    time.sleep(3)

    url_api = crear_api(lambda_arn)

    publicar_s3()

    url_web = (
        f"http://{NOMBRE_BUCKET}.s3-website-{REGION}.amazonaws.com"
    )

    print("\n================================")
    print(" DESPLIEGUE FINALIZADO")
    print("================================")
    print("Tabla:", NOMBRE_TABLA)
    print("Lambda:", NOMBRE_LAMBDA)
    print("API:", url_api)
    print("Página web:", url_web)


if __name__ == "__main__":
    main()
