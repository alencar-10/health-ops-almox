import pytest
import uuid
import io
from app.models.manufacturer import Manufacturer
from app.models.active_ingredient import ActiveIngredient
from app.models.product import Product
from app.models.inventory_movement import MovementType
from sqlalchemy import select

@pytest.mark.asyncio
async def test_full_ingestion_smoke_flow(client, db):
    """
    Smoke Test: O fluxo completo de ponta a ponta.
    1. Create Manufacturer & Ingredient (Fixtures)
    2. Upload CSV
    3. Validate
    4. Preview
    5. Confirm
    6. Verify Product & Stock
    """
    # 1. Setup Fixtures
    manuf = Manufacturer(corporate_name="Test Corp", trade_name="Test Corp", document="123")
    ingred = ActiveIngredient(name="Test Ingredient")
    db.add_all([manuf, ingred])
    await db.commit()
    await db.refresh(manuf)
    await db.refresh(ingred)

    # 2. Upload
    csv_content = (
        "sku,name,unit_of_measure,manufacturer,active_ingredient,initial_stock,minimum_stock\n"
        f"SMOKE-{uuid.uuid4().hex[:6]},Smoke Product,UNIT,Test Corp,Test Ingredient,100,10"
    )
    files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
    data = {"created_by": "SmokeTester"}
    
    response = await client.post("/almox/v1/ingestion/upload", files=files, data=data)
    assert response.status_code == 200
    session_id = response.json()["data"]["id"]

    # 3. Validate
    response = await client.post(f"/almox/v1/ingestion/validate/{session_id}")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "VALIDATED"

    # 4. Preview
    response = await client.get(f"/almox/v1/ingestion/preview/{session_id}")
    assert response.status_code == 200
    assert len(response.json()["data"]["rows"]) == 1
    assert response.json()["data"]["rows"][0]["is_valid"] is True

    # 5. Confirm
    response = await client.post(f"/almox/v1/ingestion/confirm/{session_id}", data={"created_by": "SmokeTester"})
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "COMPLETED"
    assert response.json()["data"]["processed_rows"] == 1

    # 6. Verify Production Data
    sku = csv_content.split("\n")[1].split(",")[0]
    prod_query = select(Product).where(Product.sku == sku)
    product = (await db.execute(prod_query)).scalar_one_or_none()
    
    assert product is not None
    assert product.stock_current == 100.0
    
    # 7. Check Idempotence (Double Confirm)
    response = await client.post(f"/almox/v1/ingestion/confirm/{session_id}", data={"created_by": "SmokeTester"})
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "COMPLETED"
    # Processed rows should not increase or re-run
