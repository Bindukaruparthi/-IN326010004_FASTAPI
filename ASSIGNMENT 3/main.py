from fastapi import FastAPI, Query, Response, status
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

# ---------------- DATA ----------------
products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
]

feedback_list = []
orders = []

# ---------------- MODELS ----------------
class NewProduct(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool = True

class Feedback(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int
    rating: int = Field(..., ge=1, le=5)

class Order(BaseModel):
    product_id: int
    quantity: int

# ---------------- HELPER ----------------
def find_product(product_id: int):
    for p in products:
        if p["id"] == product_id:
            return p
    return None

# ---------------- BASIC ----------------
@app.get("/")
def home():
    return {"message": "Welcome"}

@app.get("/products")
def get_products():
    return {"products": products, "total": len(products)}

@app.get("/products/{product_id}")
def get_product(product_id: int, response: Response):
    product = find_product(product_id)
    if not product:
        response.status_code = 404
        return {"error": "Product not found"}
    return {"product": product}

# ---------------- ADD PRODUCT ----------------
@app.post("/products", status_code=201)
def add_product(product: NewProduct, response: Response):
    for p in products:
        if p["name"].lower() == product.name.lower():
            response.status_code = 400
            return {"error": "Product with this name already exists"}

    new_id = max(p["id"] for p in products) + 1
    new_product = product.dict()
    new_product["id"] = new_id
    products.append(new_product)

    return {"message": "Product added", "product": new_product}

# ---------------- UPDATE ----------------
@app.put("/products/{product_id}")
def update_product(product_id: int, price: Optional[int] = None, in_stock: Optional[bool] = None, response: Response = None):
    product = find_product(product_id)
    if not product:
        response.status_code = 404
        return {"error": "Product not found"}

    if price is not None:
        product["price"] = price

    if in_stock is not None:
        product["in_stock"] = in_stock

    return {"message": "Product updated", "product": product}

# ---------------- DELETE ----------------
@app.delete("/products/{product_id}")
def delete_product(product_id: int, response: Response):
    product = find_product(product_id)
    if not product:
        response.status_code = 404
        return {"error": "Product not found"}

    products.remove(product)
    return {"message": f"Product '{product['name']}' deleted"}

# ---------------- AUDIT ----------------
@app.get("/products/audit")
def product_audit():
    in_stock = [p for p in products if p["in_stock"]]
    out_stock = [p for p in products if not p["in_stock"]]

    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock),
        "out_of_stock_names": [p["name"] for p in out_stock],
        "total_stock_value": sum(p["price"] * 10 for p in in_stock),
        "most_expensive": max(products, key=lambda p: p["price"])
    }

# ---------------- BONUS ----------------
@app.put("/products/discount")
def discount(category: str = Query(...), discount_percent: int = Query(..., ge=1, le=99)):
    updated = []

    for p in products:
        if p["category"] == category:
            p["price"] = int(p["price"] * (1 - discount_percent / 100))
            updated.append(p)

    if not updated:
        return {"message": "No products found"}

    return {"updated_count": len(updated), "products": updated}

# ---------------- ORDERS ----------------
@app.post("/orders")
def create_order(order: Order):
    order_id = len(orders) + 1
    new_order = order.dict()
    new_order["order_id"] = order_id
    new_order["status"] = "pending"
    orders.append(new_order)
    return new_order

@app.get("/orders/{order_id}")
def get_order(order_id: int, response: Response):
    for o in orders:
        if o["order_id"] == order_id:
            return o
    response.status_code = 404
    return {"error": "Order not found"}

@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int, response: Response):
    for o in orders:
        if o["order_id"] == order_id:
            o["status"] = "confirmed"
            return o
    response.status_code = 404
    return {"error": "Order not found"}
