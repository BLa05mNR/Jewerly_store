import uvicorn
from fastapi import FastAPI
from routers import roles, users, auth, products, images, orders, inventory, returns, individual_orders

app = FastAPI()

app.include_router(auth.router)
app.include_router(roles.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(images.router)
app.include_router(orders.router)
app.include_router(inventory.router)
app.include_router(returns.router)
app.include_router(individual_orders.router)


if __name__ == "__main__":
    uvicorn.run(app, port=8000)

