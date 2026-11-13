
import boto3
import urllib.request

REGION = "us-east-1"
TABLA = "IncidenciasWeb"
LAMBDA = "GestionarIncidencias"
API_ID = "mpufe9cgw5"
BUCKET = "incidencias-web-060599493870-2026"
API_URL = "https://mpufe9cgw5.execute-api.us-east-1.amazonaws.com/incidencias"

sesion = boto3.Session(region_name=REGION)

sts = sesion.client("sts")
dynamodb = sesion.client("dynamodb")
lambda_client = sesion.client("lambda")
apigateway = sesion.client("apigatewayv2")
s3 = sesion.client("s3")
logs = sesion.client("logs")

print("\n===== VERIFICACIÓN DE INCIDENCIAS WEB =====")

identidad = sts.get_caller_identity()
print("\nCONEXIÓN AWS: CORRECTA")
print("Cuenta:", identidad["Account"])
print("Región:", REGION)

try:
    tabla = dynamodb.describe_table(TableName=TABLA)["Table"]
    print("\nDYNAMODB: CORRECTO")
    print("Tabla:", tabla["TableName"])
    print("Estado:", tabla["TableStatus"])
except Exception as error:
    print("\nDYNAMODB: ERROR")
    print(error)

try:
    funcion = lambda_client.get_function_configuration(FunctionName=LAMBDA)
    print("\nLAMBDA: CORRECTO")
    print("Función:", funcion["FunctionName"])
    print("Runtime:", funcion["Runtime"])
    print("Estado:", funcion["State"])
except Exception as error:
    print("\nLAMBDA: ERROR")
    print(error)

try:
    api = apigateway.get_api(ApiId=API_ID)
    print("\nAPI GATEWAY: CORRECTO")
    print("Nombre:", api["Name"])
    print("Protocolo:", api["ProtocolType"])
except Exception as error:
    print("\nAPI GATEWAY: ERROR")
    print(error)

try:
    objetos = s3.list_objects_v2(Bucket=BUCKET)
    print("\nS3: CORRECTO")
    print("Bucket:", BUCKET)
    print("Archivos publicados:")
    for objeto in objetos.get("Contents", []):
        print("-", objeto["Key"])
except Exception as error:
    print("\nS3: ERROR")
    print(error)

try:
    grupos = logs.describe_log_groups(
        logGroupNamePrefix="/aws/lambda/" + LAMBDA
    )
    encontrado = any(
        grupo["logGroupName"] == "/aws/lambda/" + LAMBDA
        for grupo in grupos.get("logGroups", [])
    )
    print("\nCLOUDWATCH:", "CORRECTO" if encontrado else "NO ENCONTRADO")
except Exception as error:
    print("\nCLOUDWATCH: ERROR")
    print(error)

try:
    solicitud = urllib.request.urlopen(API_URL, timeout=15)
    print("\nPRUEBA DE API: CORRECTA")
    print("Código HTTP:", solicitud.status)
    print("Respuesta:", solicitud.read().decode("utf-8"))
except Exception as error:
    print("\nPRUEBA DE API: ERROR")
    print(error)

print("\n===== VERIFICACIÓN FINALIZADA =====")

