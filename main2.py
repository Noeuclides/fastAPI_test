import os
import urllib
import databases
import sqlalchemy
import uuid
import datetime as dt
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# configure database
host_server = os.environ.get('host_server', 'localhost')
db_server_port = urllib.parse.quote_plus(
    str(os.environ.get('db_server_port', '5432')))
database_name = os.environ.get('database_name', 'dbtest')
db_username = urllib.parse.quote_plus(
    str(os.environ.get('db_username', 'postgres')))
print(db_username)
db_password = urllib.parse.quote_plus(
    str(os.environ.get('db_password', 'secret')))
ssl_mode = urllib.parse.quote_plus(str(os.environ.get('ssl_mode', 'prefer')))
DATABASE_URL = 'postgresql://{}:{}@{}:{}/{}?sslmode={}'.format(
    db_username,
    db_password,
    host_server,
    db_server_port,
    database_name,
    ssl_mode
)
print(DATABASE_URL)

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

users = sqlalchemy.Table(
    "py_users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("username", sqlalchemy.String),
    sqlalchemy.Column("password", sqlalchemy.String),
    sqlalchemy.Column("first_name", sqlalchemy.String),
    sqlalchemy.Column("last_name", sqlalchemy.String),
    sqlalchemy.Column("gender", sqlalchemy.CHAR),
    sqlalchemy.Column("created_at", sqlalchemy.String),
    sqlalchemy.Column("status", sqlalchemy.CHAR),
)

engine = sqlalchemy.create_engine(
    DATABASE_URL
)
metadata.create_all(engine)

# Models


class UserList(BaseModel):
    id: str
    username: str
    password: str
    first_name: str
    last_name: str
    gender: str
    created_at: str
    status: str


class UserEntry(BaseModel):
    username: str = Field(..., example="holaexam")
    password: str = Field(..., example="holaexam")
    first_name: str = Field(..., example="Hola")
    last_name: str = Field(..., example="Example")
    gender: str = Field(..., example="M")


class UserUpdate(BaseModel):
    id: str = Field(..., example="Enter your id")
    first_name: str = Field(..., example="Hola")
    last_name: str = Field(..., example="Example")
    gender: str = Field(..., example="M")
    status: str = Field(..., example="1")

class UserDelete(BaseModel):
    id: str = Field(..., example="Enter your id")

app = FastAPI()


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get('/users', response_model=List[UserList])
async def find_all_users():
    query = users.select()
    return await database.fetch_all(query)


@app.post('/users', response_model=UserList)
async def register_user(user: UserEntry):
    gID = str(uuid.uuid1())
    gDate = str(dt.datetime.now())
    query = users.insert().values(
        id=gID,
        username=user.username,
        password=pwd_context.hash(user.password),
        first_name=user.first_name,
        last_name=user.last_name,
        gender=user.gender,
        created_at=gDate,
        status="1"
    )
    await database.execute(query)
    return {
        "id": gID,
        **user.dict(),
        "created_at": gDate,
        "status": "1"
    }


@app.get("/users/{userId}", response_model=UserList)
async def find_user_by_id(userId: str):
    query = users.select().where(users.c.id == userId)
    return await database.fetch_one(query)


@app.put("/users", response_model=UserList)
async def update_user(user: UserUpdate):
    gDate = str(dt.datetime.now())
    query = users.update().where(users.c.id == user.id).values(
        first_name=user.first_name,
        last_name=user.last_name,
        gender=user.gender,
        status=user.status,
        created_at=gDate
    )
    await database.execute(query)

    return await find_user_by_id(user.id)

@app.delete("/users/{userId}")
async def delete_user(user:UserDelete):
    query = users.delete().where(users.c.id == user.id)
    await database.execute(query)

    return {
        "status": True,
        "message": "This user has been deleted successfully"
    }