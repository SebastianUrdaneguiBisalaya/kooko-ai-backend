import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
from supabase.client import ClientOptions
from datetime import datetime
import pytz
from functions.invoice import generate_datetime

dotenv_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)
supabase_url = os.getenv("SUPABASE_URL")
supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")


tz = pytz.timezone('America/Lima')
local_time = datetime.now(tz)


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
    date, time = generate_datetime()
    data = {
        "user_id": user_id,
        "id_invoice": invoice_data["id_invoice"] or "",
        "payment_date": invoice_data["payment_date"] or date,
        "date": invoice_data["date"] or date,
        "time": invoice_data["time"] or time,
        "payment_method": invoice_data["payment_method"] or "",
        "currency_type": invoice_data["currency_type"] or "",
        "category_type": invoice_data["category_type"] or "",
        "id_seller": invoice_data["seller"]["id_seller"] or "",
        "name_seller": invoice_data["seller"]["name_seller"] or "",
        "id_client": invoice_data["client"]["id_client"] or "",
        "name_client": invoice_data["client"]["name_client"] or "",
        "address": invoice_data["client"]["address"] or "",
        "total": total or 0,
        "recorded_operation": invoice_data["taxes"]["recorded_operation"] or 0,
        "igv": invoice_data["taxes"]["igv"] or 0,
        "isc": invoice_data["taxes"]["isc"] or 0,
        "unaffected": invoice_data["taxes"]["unaffected"] or 0,
        "exonerated": invoice_data["taxes"]["exonerated"] or 0,
        "export": invoice_data["taxes"]["export"] or 0,
        "free": invoice_data["taxes"]["free"] or 0,
        "discount": invoice_data["taxes"]["discount"] or 0,
        "others_charge": invoice_data["taxes"]["others_charge"] or 0,
        "others_taxes": invoice_data["taxes"]["others_taxes"] or 0,
        "path_file": f"{supabase_url}/storage/v1/object/{path_file}" or "",
    }
    supabase = create_supabase_client()
    response = (
        supabase.table("invoices")
        .insert(data)
        .execute()
    )
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
    if response.data:
        return response.data
    else:
        return None


def upload_file(file_path: str, user_id: str) -> None:
    supabase = create_supabase_client()
    with open(file_path, "rb") as file:
        response = (
            supabase.storage
            .from_("invoices")
            .upload(
                file=file,
                path=f"public/{user_id}-{local_time.strftime("%Y%m%d%H%M%S%f")}.jpg",
                file_options={"cache-control": "3600",
                              "upsert": "false", "content-type": "image/jpg"}
            )
        )
        if response.fullPath:
            return response.fullPath
        else:
            return None
