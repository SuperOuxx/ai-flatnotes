import json
import asyncio
from typing import List, Literal
import uuid

from fastapi import APIRouter, Depends, FastAPI, HTTPException, UploadFile, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from sse_starlette import EventSourceResponse, ServerSentEvent
from fastapi.middleware.cors import CORSMiddleware

import redis.asyncio as redis

import api_messages
from attachments.base import BaseAttachments
from attachments.models import AttachmentCreateResponse
from auth.base import BaseAuth
from auth.models import Login, Token
from global_config import AuthType, GlobalConfig, GlobalConfigResponseModel
from helpers import replace_base_href
from notes.base import BaseNotes
from notes.models import Note, NoteCreate, NoteUpdate, SearchResult
from tasks.models import TaskCreate
from tasks.llm_chat import Chat

global_config = GlobalConfig()
auth: BaseAuth = global_config.load_auth()
note_storage: BaseNotes = global_config.load_note_storage()
attachment_storage: BaseAttachments = global_config.load_attachment_storage()
auth_deps = [Depends(auth.authenticate)] if auth else []
router = APIRouter()
app = FastAPI(
    docs_url=global_config.path_prefix + "/docs",
    openapi_url=global_config.path_prefix + "/openapi.json",
)

# 添加CORS支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8080"],  # 允许的前端地址
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有HTTP头
)

replace_base_href("client/dist/index.html", global_config.path_prefix)


red = redis.Redis(host='192.168.7.183', db=13)


user_id = auth.get_user_hash()
chat_func: Chat = None

async def get_chat():
    return Chat(user_id=auth.get_user_hash())
    # global chat_func
    # if chat_func is None:
    #     chat_func = Chat(user_id=auth.get_user_hash())
    # return chat_func

# region UI
@router.get("/", include_in_schema=False)
@router.get("/login", include_in_schema=False)
@router.get("/search", include_in_schema=False)
@router.get("/new", include_in_schema=False)
@router.get("/note/{title}", include_in_schema=False)
@router.get("/chat", include_in_schema=False)
def root(title: str = ""):
    with open("client/dist/index.html", "r", encoding="utf-8") as f:
        html = f.read()
        # user_id = auth.get_user_hash()
    return HTMLResponse(content=html)


# endregion


# region Login
if global_config.auth_type not in [AuthType.NONE, AuthType.READ_ONLY]:

    @router.post("/api/token", response_model=Token)
    def token(data: Login):
        try:
            # user_id = auth.get_user_hash()
            return auth.login(data)
        except ValueError:
            raise HTTPException(
                status_code=401, detail=api_messages.login_failed
            )


# endregion


# region Notes
# Get Note
@router.get(
    "/api/notes/{title}",
    dependencies=auth_deps,
    response_model=Note,
)
def get_note(title: str):
    """Get a specific note."""
    try:
        return note_storage.get(title)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=api_messages.invalid_note_title
        )
    except FileNotFoundError:
        raise HTTPException(404, api_messages.note_not_found)


if global_config.auth_type != AuthType.READ_ONLY:

    # Create Note
    @router.post(
        "/api/notes",
        dependencies=auth_deps,
        response_model=Note,
    )
    def post_note(note: NoteCreate):
        """Create a new note."""
        try:
            return note_storage.create(note)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=api_messages.invalid_note_title,
            )
        except FileExistsError:
            raise HTTPException(
                status_code=409, detail=api_messages.note_exists
            )

    # Update Note
    @router.patch(
        "/api/notes/{title}",
        dependencies=auth_deps,
        response_model=Note,
    )
    def patch_note(title: str, data: NoteUpdate):
        try:
            return note_storage.update(title, data)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=api_messages.invalid_note_title,
            )
        except FileExistsError:
            raise HTTPException(
                status_code=409, detail=api_messages.note_exists
            )
        except FileNotFoundError:
            raise HTTPException(404, api_messages.note_not_found)

    # Delete Note
    @router.delete(
        "/api/notes/{title}",
        dependencies=auth_deps,
        response_model=None,
    )
    def delete_note(title: str):
        try:
            note_storage.delete(title)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=api_messages.invalid_note_title,
            )
        except FileNotFoundError:
            raise HTTPException(404, api_messages.note_not_found)


# endregion


# region Search
@router.get(
    "/api/search",
    dependencies=auth_deps,
    response_model=List[SearchResult],
)
def search(
    term: str,
    sort: Literal["score", "title", "lastModified"] = "score",
    order: Literal["asc", "desc"] = "desc",
    limit: int = None,
):
    """Perform a full text search on all notes."""
    if sort == "lastModified":
        sort = "last_modified"
    return note_storage.search(term, sort=sort, order=order, limit=limit)

from fastapi.responses import StreamingResponse
import time


def sse_event_generator():
    while True:
        # SSE 格式，每条数据必须以 "\n\n" 结尾
        yield f"data: 通知来了 - {time.strftime('%X')}\n\n"
        time.sleep(3)

async def run_background_task(task_id: str, user_id: str, query: str):
    resp = await chat.astream_chat(query)
    await red.publish(
        f"user:{user_id}",
        json.dumps({"status": "completed", "task_id": task_id, "resp": resp})
    )
    red.close()
    
@router.post(
        "/api/task",
        dependencies=auth_deps,
    )
def create_task(
    task: TaskCreate,
    background_tasks: BackgroundTasks
    ):
    task_id = f"task_{auth.get_user_hash()}_{uuid.uuid4()}"
    background_tasks.add_task(run_background_task, task_id, auth.get_user_hash())
    return {"task_id": task_id, "user_id": auth.get_user_hash()}
    # return StreamingResponse(sse_event_generator(), media_type="text/event-stream")



@app.get(
    "/api/chat/ai/stream",
    # dependencies=auth_deps,
)
async def chat_stream(message: str, session_id):
    # user_id = auth.get_user_hash()
    chat = await get_chat()

    resp = await chat.stream_chat_session(session_id, query=message)

    chunks = []

    async def generate():
        async for chunk in resp:
            chunks.append(chunk)
            yield ServerSentEvent(data=chunk)
        
        full_response = "".join(chunks)
        chat.save_this_round_msg(
            query=message, 
            ai_resp=full_response, 
            session_id=chat.get_curr_session_id()
        )
        
        yield ServerSentEvent(
                event="reloadTitle",
                data=chat.get_curr_session_title(),
                id=chat.get_curr_session_id()
            )

    return EventSourceResponse(generate())

@app.get(
    "/api/chat/ai/sessions",
    # dependencies=auth_deps,
)
async def get_sessions():
    # user_id = auth.get_user_hash()
    chat = await get_chat()
    sessions = chat.get_all_sessions()
    return [{"id": s.id, "title": s.title} for s in sessions]


@app.get(
    "/api/chat/ai/messages",
    # dependencies=auth_deps,
)
async def get_messages(sessionId):
    # user_id = auth.get_user_hash()
    chat = await get_chat()
    messages = chat.get_all_chat_history(session_id=sessionId)
    if messages:
        return [{'role': msg.role, 'content': msg.content} for msg in messages]
    return []

@app.post(
    "/api/chat/ai/sessions/{session_id}",
    # dependencies=auth_deps,  # Uncomment if authentication is needed
)
async def update_session_title(session_id: str, data: dict):
    """Update a chat session's title"""
    chat = await get_chat()
    new_title = data.get('title')
    if not new_title:
        raise HTTPException(status_code=400, detail="Title is required")

    # Update the session title
    if chat.update_session_title(session_id, new_title):
        return {"status": "success", "new_title": new_title}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

# Create a websocket connection
# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     # user_id = auth.get_user_hash()
#     chat = await get_chat()
#     # if not chat_func:
#     #     # user_id = auth.get_user_hash()
#     #     chat = await get_chat()
#     try:
#         while True:
#             data = await websocket.receive_text()
#             message_data = json.loads(data)
#             if message_data['type'] == 'get_messages':
#                 messages = chat.get_all_chat_history()
#                 if messages:
#                     msg_arr = [{'role': msg.role, 'content': msg.content} for msg in messages]
#                     await websocket.send_text(json.dumps({'msg_arr': msg_arr}))

#             if message_data['type'] == 'new_message':
#                 new_message = message_data['content']
#                 resp = chat.astream_chat(query=new_message) # . test_chat(new_message)
#                 # await websocket.send_text(json.dumps({'type': 'message_update', 'content': resp, "role": "assistant"}))
#                 # async for chunk in resp:
#                 #     print(chunk)
                
#                 #     await websocket.send_text(json.dumps({'type': 'message_update', 'content': chunk, "role": "assistant"}))
                
#                 async for chunk in resp:
#                     await websocket.send_text(json.dumps({
#                         'type': 'message_part',
#                         'content': chunk,
#                         "role": "assistant"
#                     }))
#                 # 发送完成信号
#                 await websocket.send_text(json.dumps({
#                     'type': 'message_complete',
#                     "role": "assistant"
#                 }))
#                 # 保存完整响应（需在Chat类中实现获取最终内容的方法）
#                 full_response = "".join([chunk for chunk in resp])
#                 chat.save_this_round_msg(query=new_message, ai_resp=full_response)
#                 # chat.save_this_round_msg(query=new_message, ai_resp=resp.message.content)

#             # if message_data['type'] == 'clear_messages':
#             #     messages_collection.delete_many({})
#             #     messages_collection.insert_one({'role': 'system', 'content': 'You are a helpful assistant'})
#             #     messages = get_messages()
#             #     await websocket.send_text(json.dumps({'type': 'message_update', 'content': messages[1:]}))

#     except WebSocketDisconnect:
#         print("Client disconnected")

@router.get(
    "/api/tags",
    dependencies=auth_deps,
    response_model=List[str],
)
def get_tags():
    """Get a list of all indexed tags."""
    return note_storage.get_tags()


# endregion


# region Config
@router.get("/api/config", response_model=GlobalConfigResponseModel)
def get_config():
    """Retrieve server-side config required for the UI."""
    return GlobalConfigResponseModel(
        auth_type=global_config.auth_type,
        quick_access_hide=global_config.quick_access_hide,
        quick_access_title=global_config.quick_access_title,
        quick_access_term=global_config.quick_access_term,
        quick_access_sort=global_config.quick_access_sort,
        quick_access_limit=global_config.quick_access_limit,
    )


# endregion


# region Attachments
# Get Attachment
@router.get(
    "/api/attachments/{filename}",
    dependencies=auth_deps,
)
# Include a secondary route used to create relative URLs that can be used
# outside the context of flatnotes (e.g. "/attachments/image.jpg").
@router.get(
    "/attachments/{filename}",
    dependencies=auth_deps,
    include_in_schema=False,
)
def get_attachment(filename: str):
    """Download an attachment."""
    try:
        return attachment_storage.get(filename)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=api_messages.invalid_attachment_filename,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail=api_messages.attachment_not_found
        )


if global_config.auth_type != AuthType.READ_ONLY:

    # Create Attachment
    @router.post(
        "/api/attachments",
        dependencies=auth_deps,
        response_model=AttachmentCreateResponse,
    )
    def post_attachment(file: UploadFile):
        """Upload an attachment."""
        try:
            return attachment_storage.create(file)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=api_messages.invalid_attachment_filename,
            )
        except FileExistsError:
            raise HTTPException(409, api_messages.attachment_exists)


# endregion


# region Healthcheck
@router.get("/health")
def healthcheck() -> str:
    """A lightweight endpoint that simply returns 'OK' to indicate the server
    is running."""
    return "OK"


# endregion

app.include_router(router, prefix=global_config.path_prefix)
app.mount(
    global_config.path_prefix,
    StaticFiles(directory="client/dist"),
    name="dist",
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)