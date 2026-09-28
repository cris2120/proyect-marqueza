from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pwdlib import PasswordHash
from sqlalchemy import DateTime, Integer, JSON, String, URL, create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False)

    database_url: str = ""
    db_host: str = ""
    db_port: int = 5432
    db_name: str = "marqueza"
    db_user: str = "marqueza"
    db_password: str = ""
    jwt_secret: str = "local-development-secret-change-this"
    jwt_expire_minutes: int = 720
    admin_username: str = "admin"
    admin_password: str = "admin1234"
    admin_email: str = "admin@marqueza.local"
    cors_origins: str = ""


settings = Settings()
database_url = settings.database_url or (
    URL.create(
        "postgresql+psycopg",
        username=settings.db_user,
        password=settings.db_password,
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
    ).render_as_string(hide_password=False)
    if settings.db_host
    else "sqlite:///./marqueza.db"
)
engine = create_engine(
    database_url,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)
RESOURCES = {"clientes", "proveedores", "productos", "insumos", "ventas", "cotizaciones"}
ROLES = {"Administrador", "Empleado", "Usuario"}


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="Empleado")
    is_active: Mapped[bool] = mapped_column(default=True)
    is_system_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Collection(Base):
    __tablename__ = "collections"

    resource: Mapped[str] = mapped_column(String(40), primary_key=True)
    records: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    version: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PasswordResetRequest(Base):
    __tablename__ = "password_reset_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(254), index=True)
    status: Mapped[str] = mapped_column(String(20), default="pendiente")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class LoginPayload(BaseModel):
    usuario: str = Field(min_length=1, max_length=40)
    contrasena: str = Field(min_length=1, max_length=256)


class RegisterPayload(BaseModel):
    nombre: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9]+$")
    correo: str = Field(min_length=3, max_length=254)
    contrasena: str = Field(min_length=8, max_length=256)


class CollectionPayload(BaseModel):
    records: list[dict[str, Any]] = Field(max_length=50000)
    version: int | None = Field(default=None, ge=0)


def get_db():
    with SessionLocal() as db:
        yield db


def public_user(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "nombre": user.username,
        "correo": user.email,
        "rol": user.role,
        "protegido": user.is_system_admin,
        "activo": user.is_active,
    }


def make_token(user: User) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode({"sub": str(user.id), "exp": expires}, settings.jwt_secret, algorithm="HS256")


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inicia sesión para continuar.")
    try:
        claims = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        user_id = int(claims["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="La sesión no es válida o expiró.") from None
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="La cuenta está inactiva o no existe.")
    return user


def require_admin(user: User = Depends(current_user)) -> User:
    if not user.is_system_admin and user.role != "Administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Esta acción requiere permisos de administrador.")
    return user


def initialize_database() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        username = settings.admin_username.strip().lower()
        admin = db.scalar(select(User).where(User.username == username))
        if admin is None:
            db.add(User(
                username=username,
                email=settings.admin_email.strip().lower(),
                password_hash=password_hash.hash(settings.admin_password),
                role="Administrador",
                is_active=True,
                is_system_admin=True,
            ))
        else:
            admin.email = settings.admin_email.strip().lower()
            admin.password_hash = password_hash.hash(settings.admin_password)
            admin.role = "Administrador"
            admin.is_active = True
            admin.is_system_admin = True
        db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="MARQUEZA API", version="1.0.0", lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json")
origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/login")
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    username = payload.usuario.strip().lower()
    user = db.scalar(select(User).where(User.username == username))
    if user is None or not user.is_active or not password_hash.verify(payload.contrasena, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario o contraseña incorrectos.")
    token = make_token(user)
    return {"access_token": token, "token": token, "token_type": "bearer", "usuario": public_user(user)}


@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return public_user(user)


@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterPayload, db: Session = Depends(get_db)):
    username = payload.nombre.strip().lower()
    email = payload.correo.strip().lower()
    if username == settings.admin_username.strip().lower():
        raise HTTPException(status_code=409, detail="Ese nombre de usuario está reservado.")
    if db.scalar(select(User).where((User.username == username) | (User.email == email))):
        raise HTTPException(status_code=409, detail="El usuario o correo ya está registrado.")
    user = User(username=username, email=email, password_hash=password_hash.hash(payload.contrasena), role="Empleado", is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return public_user(user)


@app.post("/api/auth/password-reset-requests", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(payload: dict[str, str], db: Session = Depends(get_db)):
    email = str(payload.get("correo", "")).strip().lower()
    if email:
        user = db.scalar(select(User).where(User.email == email, User.is_active.is_(True)))
        if user is not None:
            db.add(PasswordResetRequest(email=email))
            db.commit()
    return {"message": "Si existe una cuenta con ese correo, la solicitud quedó registrada para revisión."}


@app.get("/api/auth/password-reset-requests")
def list_password_reset_requests(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rows = db.scalars(select(PasswordResetRequest).order_by(PasswordResetRequest.created_at.desc())).all()
    return [{"id": row.id, "correo": row.email, "estado": row.status, "creadoEn": row.created_at.isoformat()} for row in rows]


@app.get("/api/users")
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.created_at)).all()
    return [public_user(user) for user in users]


@app.put("/api/users/sync")
def sync_users(
    payload: dict[str, list[dict[str, Any]]],
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    incoming = payload.get("users", [])
    existing = db.scalars(select(User)).all()
    by_id = {user.id: user for user in existing}
    by_name = {user.username.lower(): user for user in existing}
    retained_ids = {user.id for user in existing if user.is_system_admin}
    seen_names: set[str] = set()
    seen_emails: set[str] = set()

    for data in incoming:
        username = str(data.get("nombre", "")).strip().lower()
        email = str(data.get("correo", "")).strip().lower()
        if not username or not email:
            raise HTTPException(status_code=422, detail="Cada cuenta necesita nombre y correo.")
        if username in seen_names or email in seen_emails:
            raise HTTPException(status_code=409, detail="Hay nombres o correos duplicados.")
        seen_names.add(username)
        seen_emails.add(email)
        user_id = data.get("id")
        user = by_id.get(user_id) if isinstance(user_id, int) else by_name.get(username)
        if user is not None and user.is_system_admin:
            retained_ids.add(user.id)
            continue
        if user is None:
            if username == settings.admin_username.strip().lower():
                raise HTTPException(status_code=409, detail="Ese nombre está reservado para el administrador del sistema.")
            if db.scalar(select(User).where(User.email == email)):
                raise HTTPException(status_code=409, detail="Ese correo ya pertenece a otra cuenta.")
            raw_password = str(data.get("contrasena", ""))
            if len(raw_password) < 8:
                raise HTTPException(status_code=422, detail=f"La contraseña de {username} debe tener al menos 8 caracteres.")
            user = User(username=username, email=email, password_hash=password_hash.hash(raw_password))
            db.add(user)
            db.flush()
        else:
            other_username = db.scalar(select(User).where(User.username == username, User.id != user.id))
            if other_username:
                raise HTTPException(status_code=409, detail="Ese nombre de usuario ya pertenece a otra cuenta.")
            other_user = db.scalar(select(User).where(User.email == email, User.id != user.id))
            if other_user:
                raise HTTPException(status_code=409, detail="Ese correo ya pertenece a otra cuenta.")
            user.username = username
            user.email = email
            if data.get("contrasena"):
                new_password = str(data["contrasena"])
                if len(new_password) < 8:
                    raise HTTPException(status_code=422, detail="La contraseña debe tener al menos 8 caracteres.")
                user.password_hash = password_hash.hash(new_password)
        role = str(data.get("rol", "Empleado"))
        if role not in ROLES:
            raise HTTPException(status_code=422, detail=f"Rol no permitido: {role}.")
        user.role = role
        user.is_active = bool(data.get("activo", True))
        retained_ids.add(user.id)

    for user in existing:
        if not user.is_system_admin and user.id not in retained_ids:
            db.delete(user)
    db.commit()
    users = db.scalars(select(User).order_by(User.created_at)).all()
    return [public_user(user) for user in users]


@app.get("/api/collections/{resource}")
def get_collection(resource: str, _: User = Depends(current_user), db: Session = Depends(get_db)):
    if resource not in RESOURCES:
        raise HTTPException(status_code=404, detail="Módulo desconocido.")
    collection = db.get(Collection, resource)
    return {"records": collection.records, "version": collection.version} if collection else {"records": [], "version": 0}


@app.put("/api/collections/{resource}")
def put_collection(
    resource: str,
    payload: CollectionPayload,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if resource not in RESOURCES:
        raise HTTPException(status_code=404, detail="Módulo desconocido.")
    collection = db.scalar(select(Collection).where(Collection.resource == resource).with_for_update())
    if collection is None:
        if payload.version not in (None, 0):
            raise HTTPException(status_code=409, detail="Los datos cambiaron en otro dispositivo. Sincroniza y vuelve a intentarlo.")
        collection = Collection(resource=resource, records=payload.records, version=1)
        db.add(collection)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Los datos cambiaron en otro dispositivo. Sincroniza y vuelve a intentarlo.") from None
    else:
        if payload.version is not None and payload.version != collection.version:
            raise HTTPException(status_code=409, detail="Los datos cambiaron en otro dispositivo. Sincroniza y vuelve a intentarlo.")
        collection.records = payload.records
        collection.version += 1
        collection.updated_at = datetime.now(timezone.utc)
        db.commit()
    return {"records": collection.records, "version": collection.version, "actualizadoPor": user.username}


@app.get("/api/audit")
def get_audit(_: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(AuditEvent).order_by(AuditEvent.id.desc()).limit(500)).all()
    return [row.payload for row in rows]


@app.post("/api/audit", status_code=status.HTTP_201_CREATED)
def add_audit(payload: dict[str, Any], user: User = Depends(current_user), db: Session = Depends(get_db)):
    payload.setdefault("actor", user.username)
    payload.setdefault("role", user.role)
    db.add(AuditEvent(payload=payload))
    db.commit()
    return {"status": "ok"}


@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="La cuenta no existe.")
    if user.is_system_admin:
        raise HTTPException(status_code=403, detail="El administrador del sistema no se puede eliminar.")
    db.delete(user)
    db.commit()