
import json
import os
import uuid
import boto3
from datetime import datetime

dynamodb = boto3.resource("dynamodb")
tabla = dynamodb.Table(os.environ["TABLE_NAME"])

def respuesta(status, data):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,POST,PATCH,DELETE,OPTIONS"
        },
        "body": json.dumps(data, ensure_ascii=False)
    }

def lambda_handler(event, context):
    try:
        metodo = event.get("requestContext", {}).get("http", {}).get("method", "")
        ruta = event.get("rawPath", "")

        if metodo == "OPTIONS":
            return respuesta(200, {"mensaje": "OK"})

        if metodo == "GET":
            resultado = tabla.scan()
            return respuesta(200, resultado.get("Items", []))

        if metodo == "POST":
            datos = json.loads(event.get("body") or "{}")

            if not datos.get("titulo") or not datos.get("descripcion"):
                return respuesta(400, {"error": "Faltan datos"})

            incidencia = {
                "id": str(uuid.uuid4()),
                "titulo": datos["titulo"],
                "descripcion": datos["descripcion"],
                "estado": "Pendiente",
                "fecha": datetime.now().isoformat()
            }

            tabla.put_item(Item=incidencia)
            return respuesta(201, incidencia)

        parametros = event.get("pathParameters") or {}
        identificador = parametros.get("id")

        if not identificador:
            return respuesta(400, {"error": "ID no proporcionado"})

        if metodo == "PATCH":
            datos = json.loads(event.get("body") or "{}")
            estado = datos.get("estado")

            if estado not in ["Pendiente", "En proceso", "Completada"]:
                return respuesta(400, {"error": "Estado no válido"})

            resultado = tabla.update_item(
                Key={"id": identificador},
                UpdateExpression="SET #e = :estado",
                ExpressionAttributeNames={"#e": "estado"},
                ExpressionAttributeValues={":estado": estado},
                ConditionExpression="attribute_exists(id)",
                ReturnValues="ALL_NEW"
            )

            return respuesta(200, resultado["Attributes"])

        if metodo == "DELETE":
            tabla.delete_item(
                Key={"id": identificador},
                ConditionExpression="attribute_exists(id)"
            )
            return respuesta(200, {"mensaje": "Incidencia eliminada"})

        return respuesta(404, {"error": "Ruta no encontrada"})

    except Exception as error:
        print("Error:", str(error))
        return respuesta(500, {"error": "Error interno del servidor"})

