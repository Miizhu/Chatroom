from fastapi import  FastAPI,Depends,HTTPException,Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, delete
from models import User, Message
from database import  get_db
from auth import generate_account,hash_password,verify_password
from datetime import datetime,timezone
from starlette.middleware.sessions import SessionMiddleware
import secrets

app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key="62556770a6d75771efb38cb5ad1b67702f39c47d9f35925b0e9cc4482abc37e6"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:5173"],
    allow_credentials= True,
    allow_methods=["*"],
    allow_headers=["*"]
)


class RegisterRequest(BaseModel):
    username: str
    password: str
#注册接口

@app.post("/register",status_code = 201)
def register(user: RegisterRequest, db: Session = Depends(get_db)):
    user.username = user.username.strip()
    user.password = user.password.strip()
    if not user.username or not user.password:
        raise HTTPException(
            status_code=400,
            detail = "用户名及密码不能为空"
        )
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
    if receiver.account.startswith("deleted_"):
        raise HTTPException(
            status_code=410,
            detail="该用户已注销"
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

@app.get("/conversations")
def get_conversations(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code = 401,
            detail = "您已离线"
        )
    statement = select(Message).where(or_(Message.sender_id == user_id,Message.receiver_id == user_id)).order_by(Message.id.desc())
    conversations = db.scalars(statement).all()
    result = []
    seen_peer_ids = set()
    # 拉取联系人
    for conversation in conversations:
        # 去除重复联系人
        if conversation.sender_id == user_id:
            peer_id = conversation.receiver_id
        else:
            peer_id = conversation.sender_id
        if peer_id == user_id or peer_id in seen_peer_ids:
            continue
        seen_peer_ids.add(peer_id)
        peer = db.scalar(select(User).where(User.id == peer_id))
        conversation_data = {
            "account": peer.account,
            "username": peer.username,
            "last_message": conversation.content,
            "last_seen_at": peer.last_seen_at,
            "last_message_at": conversation.created_at  
        }
        result.append(conversation_data)
    return result

@app.get("/admin/users")
def admin(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(
                status_code=401,
                detail = "你还没有登录"
            )
    if user_id != 1:
        raise HTTPException(
            status_code=403,
            detail = "您没有权限登入后台"
        )
    users = db.scalars(select(User)).all()
    result = []
    for user in users:
        user_data = {
            "id": user.id,
            "account": user.account,
            "username": user.username,
            "last_seen_at": user.last_seen_at,
            "created_at":user.created_at
        }
        result.append(user_data)
    return result

@app.delete("/users/{user_id}")
def delete_user(user_id: int,request: Request, db: Session = Depends(get_db)):
    current_user_id = request.session.get("user_id")
    if current_user_id is None:
        raise HTTPException(
            status_code= 401,
            detail="您还未登录"
        )
    if current_user_id != user_id and current_user_id != 1:
        raise HTTPException(
            status_code=403,
            detail="您没有权限执行此操作"
        )
    target_user = db.get(User,user_id)
    if target_user is None:
        raise HTTPException(
            status_code=404,
            detail = "您要删除的用户不存在"
        )
    if target_user.account.startswith("deleted_"):
        raise HTTPException(
            status_code=410,
            detail="该用户已注销"
        )
    target_user.account = f"deleted_{target_user.id}"
    target_user.username = "已注销用户"
    target_user.password_hash = hash_password(secrets.token_urlsafe(32))
    db.commit()
    if target_user.id == current_user_id:
        request.session.clear()
    return {"message": "账户已注销"}

class UpdateUserRequest(BaseModel):
    username: str | None = None
    password: str | None = None

@app.patch("/users/{user_id}")
def update(user_id: int,update_user: UpdateUserRequest, request: Request, db:Session = Depends(get_db)):
    current_user_id = request.session.get("user_id")
    if current_user_id is None:
        raise HTTPException(
            status_code= 401,
            detail="您还未登录"
        )
    if current_user_id != user_id and current_user_id != 1:
        raise HTTPException(
            status_code=403,
            detail="您没有权限执行此操作"
        )
    target_user = db.get(User,user_id)
    if target_user is None:
        raise HTTPException(
            status_code=404,
            detail = "您要修改的用户不存在"
        )
    if target_user.account.startswith("deleted_"):
        raise HTTPException(
            status_code=410,
            detail="该用户已注销"
        )
    if update_user.username is not None:
        update_user.username = update_user.username.strip()
        if update_user.username:
            target_user.username = update_user.username
        else:
            raise HTTPException(
                status_code=400,
                detail = "修改值不能是空格"
            )
    if update_user.password  is not None:
        update_user.password = update_user.password.strip()
        if update_user.password:
            target_user.password_hash = hash_password(update_user.password)
        else:
            raise HTTPException(
                status_code=400,
                detail = "修改值不能是空格"
            )
    if update_user.username is None and update_user.password is None:
        raise HTTPException(
            status_code=400,
            detail="没有需要修改的内容"
        )
    db.commit()
    db.refresh(target_user)
    return{
        "id": target_user.id,
        "account": target_user.account,
        "username": target_user.username,
        "message": "修改成功"
    }

@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "退出成功"}