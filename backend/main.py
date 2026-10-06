from fastapi import  FastAPI,Depends,HTTPException,Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from models import User, Message
from database import  get_db
from auth import generate_account,hash_password,verify_password
from datetime import datetime,timezone
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key="62556770a6d75771efb38cb5ad1b67702f39c47d9f35925b0e9cc4482abc37e6"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://127.0.0.1:5500"],
    allow_credentials= True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class Item(BaseModel):
    name: str
    price: float
    is_offer: bool | None = None
@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}

@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}

class RegisterRequest(BaseModel):
    username: str
    password: str
#注册接口

@app.post("/register",status_code = 201)
def register(user: RegisterRequest, db: Session = Depends(get_db)):
    for _ in range(30):
        account = generate_account()
        # select先创建一个查询对象，然后连续调用此对象中的where方法，添加查询条件，statement保存查询说明，而不是bool值。
        statement = select(User).where(User.account == account)
        existing_user = db.scalar(statement)
        if existing_user is None:
            break
    else:
        raise HTTPException( 
            status_code = 503,
            detail="账号注册失败，请稍后再试"
        )
    new_user = User(
        account = account,
        username = user.username,
        password_hash = hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return{
        "id": new_user.id,
        "message": "注册成功",
        "account": new_user.account,
        "username": new_user.username,
    }

class LoginRequest(BaseModel):
    account: str
    password: str

@app.post("/login",status_code=200)
def login(user: LoginRequest,request: Request, db: Session = Depends(get_db)):
    statement = select(User).where(User.account == user.account)
    existing_user = db.scalar(statement)
    if existing_user is None:
        raise HTTPException(
            status_code = 404,
            detail = "用户不存在",
        )
    if not verify_password(user.password,existing_user.password_hash):
        raise HTTPException(
                status_code = 401,
                detail = "账户或密码错误",
            )
    #将用户id保存到浏览器的cookie，便于验证登录态
    request.session["user_id"] = existing_user.id
    existing_user.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    return{
        "id": existing_user.id,
        "account": existing_user.account,
        "username": existing_user.username,
        "last_seen_at": existing_user.last_seen_at
    }

class SendMessageRequest(BaseModel):
    receiver_account: str
    content: str

@app.post("/messages",status_code = 201)
def sendmessage(send_message: SendMessageRequest, request: Request,db: Session = Depends(get_db)):
    sender_id = request.session.get("user_id")
    if sender_id is None:
        raise HTTPException(
            status_code = 401,
            detail = "您已离线"
        )
    statement = select(User).where(User.account == send_message.receiver_account)
    receiver = db.scalar(statement=statement)
    if receiver is None:
        raise HTTPException(
            status_code = 404,
            detail = "发送的目标用户不存在"
        )
    new_message = Message(
        sender_id = sender_id,
        receiver_id = receiver.id,
        content = send_message.content,
        created_at = datetime.now(timezone.utc)
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return{
        "id": new_message.id,
        "sender_id": new_message.sender_id,
        "receiver_id": new_message.receiver_id,
        "content": new_message.content,
        "created_at": new_message.created_at,
        "message": "消息发送成功"
    }

@app.get("/messages")
def get_messages(peer_account: str,request: Request,after_id: int = 0, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code = 401,
            detail = "您已离线"
        )
    statement = select(User).where(User.account == peer_account)
    peer = db.scalar(statement=statement)
    if peer is None:
        raise HTTPException(
            status_code = 404,
            detail = "发送的目标用户不存在"
        )
    # 创建查询对话方法
    conversation_condition = or_(
    and_(
        Message.sender_id == user_id,
        Message.receiver_id == peer.id
    ),
    and_(
        Message.sender_id == peer.id,
        Message.receiver_id == user_id
    )
    )
    message_statement = select(Message).where(Message.id > after_id,conversation_condition).order_by(Message.id)
    # 查询所有信息
    messages = db.scalars(message_statement).all()
    result = []
    for message in messages:
        # 创建字典
        message_data = {
            "id": message.id,
            "content": message.content,
            "sender_id": message.sender_id,
            "receiver_id": message.receiver_id,
            "created_at": message.created_at,
            "is_mine": message.sender_id == user_id,
        }
        result.append(message_data)
    return result