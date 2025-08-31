from fastapi import APIRouter, Depends
from app.schemas.auth_schema import UserRegister, UserLogin, UserResponse
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.core.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

def get_auth_service(db=Depends(get_db)):
    user_repo = UserRepository(db)
    return AuthService(user_repo)

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister, service: AuthService = Depends(get_auth_service)):
    return await service.register(user_data)

@router.post("/login")
async def login(user_data: UserLogin, service: AuthService = Depends(get_auth_service)):
    token = await service.login(user_data.email, user_data.password)
    return {"access_token": token, "token_type": "bearer"}