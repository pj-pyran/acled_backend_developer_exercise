from app.logging_config import configure_logging
configure_logging()

from fastapi import FastAPI
from fastapi.security import HTTPBearer

from app.routes import auth, conflict_data

app = FastAPI(title='ACLED Conflict API', version='1.0.0')

security = HTTPBearer()
# Include necessary routers and version number
router_prefix = '/v1'
app.include_router(auth.router, prefix=router_prefix)
app.include_router(conflict_data.router, prefix=router_prefix)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)

