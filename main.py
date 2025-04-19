from fastapi import FastAPI,APIRouter,Request
import uvicorn
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from tortoise.contrib.fastapi import register_tortoise
from settings import TORTOISE_ORM
from models import User
from starlette.websockets import WebSocket
from fastapi import WebSocketDisconnect
app = FastAPI()
#1 引入静态模版文件
register_tortoise(app,config=TORTOISE_ORM) #初始化数据库连接，生成模型与数据库之间的映射
user_list=[
    {'username':'justin','password':'123456','avatar':'/static/img/default.png','age':33},
    {'username':'zhangsan','password':'123456','avatar':'/static/img/default.png','age':33},
    {'username':'lisi','password':'123456','avatar':'/static/img/default.png','age':33},
           ]

templates = Jinja2Templates(directory='templates')
#2 引入模版文件
app.mount('/static',StaticFiles(directory='static'))
#app.mount(...)是fastapi中的一个方法，用来挂载子应用或中间件git
#3添加中间件用于Session的方法检测
app.add_middleware(SessionMiddleware,secret_key='afsgravzg$$$')

# 4 新建路由
router = APIRouter()

# @app.route('/register',methods=['get','post'])
@router.route('/register',methods=['get','post'])
# 使用router模块化划分可以使得结构更加清晰
    # 我的理解是：这虽然在一个文件夹下，是一个小项目，但是中大项目都是有多个模块的，目的都是为了保证结构清晰，增强可读性和维护性，所以最好每个项目都要结构化
async def register(request:Request):
    # 如果是get请求就返回一个注册页面模版
    if request.method == 'GET':
        return templates.TemplateResponse('register.html',context={"request":request})
    else:
        # 如果是POST请求，写入数据
        form_data = await request.form()
        username = form_data.get('username')
        password = form_data.get('password')
        age = form_data.get('age')
        avatar = form_data.get('avatar')# 这是 UploadFile 类型
        # starlette.datastructures.UploadFile类型
        if avatar:
            #需要读取avatar里面的内容
            avatar_data = await avatar.read()
            avatar_url = f'/static/img/{username}.png'
            # with open创建文件
            with open('.'+avatar_url,'wb') as f:
                f.write(avatar_data)
        else:
            avatar_url = './static/img/default.png'
        await User.create(username=username,password=password,age=age,avatar=avatar_url)
        #重新定向
        return RedirectResponse('/login',status_code=302)
        # 重新定向的地址(url,状态码)

@router.route('/login',methods=['get','post'])
async def login(request:Request):
    # 如果是get请求就返回一个注册页面模版
    if request.method == 'GET':
        return templates.TemplateResponse('login.html',context={"request":request})
    else:
        form_data = await request.form()
        username = form_data.get('username')
        password = form_data.get('password')
        # for user in user_list:
        #     if user['username'] == username and user['password'] == password:
        #         request.session['username'] = username
        #         return RedirectResponse('/', status_code=302)#跳转
        user = User.filter(username=username,password=password).first()
        if user:
            request.session['username'] = username
            return RedirectResponse('/', status_code=302)  # 跳转
        context = {
            'request':request,
            'errors':'用户名密码错误'
        }
        return templates.TemplateResponse('login.html',context=context) #重新加载页面

@router.get('/logout')
async def logout(request:Request):
    request.session.clear()
    return RedirectResponse('/login', status_code=302)

@router.get('/')
async def index(request:Request):
    if request.session.get('username'):
        context={
            'request':request,
            "username":request.session.get("username")
        }
        return templates.TemplateResponse('home.html', context=context)
    else:
        return RedirectResponse('/login')

@router.get('/chat')
async def chat(request:Request):
    if request.session.get('username'):
        return templates.TemplateResponse('chat.html',context={"request":request})
    else:
        return RedirectResponse('/login',status_code=302)

#写ws来处理用户聊天
@app.websocket('/ws')
async def websocket_endpoint(websocket:WebSocket):
    await websocket.accept() #等待用户连接
    while True:
        data = await websocket.receive_text() #接受用户信息
        await websocket.send_text(data+'_nb') #发送用户信息


# 多人聊天
@router.get('/chat01')
async def chat01(request:Request):
    if request.session.get('username'):
        return templates.TemplateResponse('chat01.html',context={"request":request,"username":request.session.get('username')})
    else:
        return RedirectResponse('/login',status_code=302)


# 处理多人聊天，只要有一个人发送所有人都能收到
class ConnectionManager:
    def __init__(self):
        #列表存放所有用户
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        # 发送广播消息
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()
@app.websocket('/ws/{client_id}')
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"{client_id} 说: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"{client_id} 离开了聊天室")
app.include_router(router,prefix='',tags=['总路由'])
#注意总路由要放在这里，不然无法识别
if __name__ == '__main__':
    uvicorn.run('main:app',reload=True)