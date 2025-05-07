import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.client import ClientOptions

dotenv_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)
supabase_url = os.getenv("SUPABASE_URL")
supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")


def create_supabase_client() -> Client:
    return create_client(
        supabase_url,
        supabase_anon_key,
        options=ClientOptions(
            postgrest_client_timeout=10,
            storage_client_timeout=10,
            schema="public",
        )
    )


def verify_user(user_phone: str) -> str:
    supabase = create_supabase_client()
    response = (
        supabase.table("users")
        .select("user_id")
        .eq("user_phone", user_phone)
        .execute()
    )
    print("response user", response)
    print("response.user", response.data)
    if response.data:
        return response.data[0]["user_id"]
    else:
        return None


def insert_invoice_data(
    user_id: str,
        total: float,
    invoice_data: dict,
    path_file: str
) -> None:
    data = {
        "user_id": user_id,
        "id_invoice": invoice_data["id_invoice"],
        "payment_date": invoice_data["payment_date"],
        "date": invoice_data["date"],
        "time": invoice_data["time"],
        "payment_method": invoice_data["payment_method"],
        "currency_type": invoice_data["currency_type"],
        "category_type": invoice_data["category_type"],
        "id_seller": invoice_data["seller"]["id_seller"],
        "name_seller": invoice_data["seller"]["name_seller"],
        "id_client": invoice_data["client"]["id_client"],
        "name_client": invoice_data["client"]["name_client"],
        "address": invoice_data["client"]["address"],
        "total": total,
        "recorded_operation": invoice_data["taxes"]["recorded_operation"],
        "igv": invoice_data["taxes"]["igv"],
        "isc": invoice_data["taxes"]["isc"],
        "unaffected": invoice_data["taxes"]["unaffected"],
        "exonerated": invoice_data["taxes"]["exonerated"],
        "export": invoice_data["taxes"]["export"],
        "free": invoice_data["taxes"]["free"],
        "discount": invoice_data["taxes"]["discount"],
        "others_charge": invoice_data["taxes"]["others_charge"],
        "others_taxes": invoice_data["taxes"]["others_taxes"],
        "path_file": path_file,
    }
    supabase = create_supabase_client()
    response = (
        supabase.table("invoices")
        .insert(data)
        .execute()
    )
    print("response", response)
    print("response.data", response.data)
    if response.data:
        return response.data
    else:
        return None


def insert_invoice_detail_data(
    invoice_detail_data: dict,
) -> None:
    products = invoice_detail_data["products"]
    data = []
    for item in products:
        data.append({
            "id_invoice": invoice_detail_data["id_invoice"],
            "product_name": item["product_name"],
            "unit_price": item["unit_price"],
            "quantity": item["quantity"],
        })
    supabase = create_supabase_client()
    response = (
        supabase.table("invoices_detail")
        .insert(data)
        .execute()
    )
    print("response detail", response)
    print("response.detail", response.data)
    if response.data:
        return response.data
    else:
        return None


def insert_user_credits_data(
    user_id: str,
    credits: dict,
) -> None:
    data = {
        "user_id": user_id,
        "input_token_text": credits["input"]["token_text"],
        "input_token_image": credits["input"]["token_image"],
        "output_token_text": credits["output"]["token_text"],
    }
    supabase = create_supabase_client()
    response = (
        supabase.table("user_credits")
        .insert(data)
        .execute()
    )
    print("response credits", response)
    print("response.credits", response.data)
    if response.data:
        return response.data
    else:
        return None


def upload_file(file_path: str) -> None:
    supabase = create_supabase_client()
    with open(file_path, "rb") as file:
        response = (
            supabase.storage
            .from_("invoices")
            .upload(
                file=file,
                path=f"public/invoices/{file_path}",
                file_options={"cache-control": "3600", "upsert": "false"}
            )
        )
        print("response upload", response)
        print("response.upload", response.full_path)
        if response.fullPath:
            return response.fullPath
        else:
            return None
