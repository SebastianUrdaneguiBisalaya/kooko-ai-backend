import os
from pathlib import Path
from dotenv import load_dotenv
import json
from google import genai

dotenv_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)
gemini_api_key = os.getenv("GEMINI_API_KEY")


def invoice_processing(path_file):
    prompt = (
        """
        instrucciones: Extrae la información relevante de la imagen de la boleta o factura
        y retorna solo el objeto JSON con la siguiente estructura:
        formato_de_salida: {
            "tipo": "JSON",
            "data": {
                "id_invoice": string -> Identificación de la factura como número de serie,
                "date": date -> Formato YYYY-MM-DD de la fecha de Emisión de la boleta y/o factura,
                "time": time -> Formato HH:MM:SS de la fecha de Emisión de la boleta y/o factura,
                "payment_date": string -> Formato YYYY-MM-DD de la fecha de pago de la boleta y/o factura,
                "currency_type": string -> Tipo de moneda utilizada en la boleta y/o factura,
                "payment_method": string -> Formato de pago utilizado en la boleta y/o factura,
                "seller": {
                    "id_seller": string -> Identificación del vendedor como RUC o DNI,
                    "name_seller": string -> Nombre de la empresa vendedora,
                },
                "client": {
                    "id_client":string -> Identificación del cliente como RUC o DNI,
                    "name_client": string -> Nombre del cliente o empresa que compra el producto y/o servicio también conocida como Razón Social,
                    "address": string -> Dirección del cliente o empresa que compra el producto y/o servicio
                },
                "products": [
                    {
                        "product_name": string -> Nombre del producto,
                        "unit_price": number -> Precio unitario del producto sin aplicar impuestos,
                        "quantity": number -> Cantidad que el comprador está comprando del producto,
                    }
                    // Pueden haber más objetos de productos
                ],
                "taxes": {
                    "recorded_operation": number -> Monto total de la Operación Gravada de la compra ,
                    "igv": number -> Monto total de Impuesto General a las Ventas,
                    "isc" : number -> Monto total del Impuesto Selectivo al Consumo,
                    "unaffected": number -> Monto total de las Operaciones Inafectas,
                    "exonerated": number -> Monto total de las Operaciones Exoneradas,
                    "export": number -> Monto total de las Operaciones de exportación,
                    "free": number -> Monto total de las Operaciones gratuitas,
                    "discount": number -> Monto total del descuento,
                    "others_charge": number -> Monto total de Otros cargos,
                    "others_taxes": number -> Monto total de Otros Impuestos
                }
            }
        }
        consideraciones_adicionales: En caso un dato esté perdido o no se puede encontrar
        para asignarlo al formato_de_salida debe colocarse 'null' en el value de la key a la
        cual pertenezca. Asegúrate que los valores numéricos como el precio, cantidades,
        subtotales, impuestos, totales, operaciones grabadas, operaciones inafectas,
        operaciones exoneradas, operaciones de exportación, operación gratuita, total de
        descuento, Impuesto Selectivo al Consumo o I.S.C., Impuesto General a la Ventas o I.G.V.,
        otros cargos, otros tributos y el importe total. Recuerdad que usualmente el primer nombre e identificación
        que aparecen en las boletas y/o facturas pertenecen a la empresa o persona vendedora.
        Con respecto a la construcción del array de objetos de productos, asegúrate que no se generen
        duplicados en cuanto a los productos, dado que hay veces el nombre es muy largo y ocupa más de una fila.
        """
    )
    client = genai.Client(api_key=gemini_api_key)
    my_file = client.files.upload(file=path_file)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[my_file, prompt]
    )
    metadata = {
        "input": {
            "token_text": response.usage_metadata.prompt_tokens_details[0].token_count,
            "token_image": response.usage_metadata.prompt_tokens_details[1].token_count,
        },
        "output": {
            "token_text": response.usage_metadata.candidates_tokens_details[0].token_count,
        }
    }
    try:
        response_text = response.text
        cleaned_str = response_text.strip('`json\n').strip('`')
        result = json.loads(cleaned_str)
        result.update(metadata)
        return result
    except json.JSONDecodeError as e:
        print(f"Error al decodificar la cadena JSON: {e}")
    return response
