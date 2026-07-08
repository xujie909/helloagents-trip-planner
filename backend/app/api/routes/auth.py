"""用户认证 API"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from ...services.auth_service import register_user, login_user, get_user_by_token, logout_user

router = APIRouter(prefix="/auth", tags=["用户认证"])


class AuthRequest(BaseModel):
    username: str = ""
    password: str = ""
    name: str = ""


def get_current_user(authorization: str = Header("")) -> dict:
    """从请求头获取当前登录用户"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization[7:]
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    return user


@router.post("/register")
async def register(req: AuthRequest):
    """注册（用户名+密码，系统自动生成昵称）"""
    if len(req.username) < 2:
        raise HTTPException(status_code=400, detail="用户名至少2位")
    if len(req.password) < 4:
        raise HTTPException(status_code=400, detail="密码至少4位")
    result = register_user(req.username, req.password)
    if result is None:
        raise HTTPException(status_code=409, detail="用户名已存在")
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "message": "注册成功", "user": result}


@router.post("/login")
async def login(req: AuthRequest):
    """用户登录"""
    # 检查是否被禁用
    from ...services.auth_service import _load_users
    users = _load_users()
    if users.get(req.username, {}).get("disabled"):
        raise HTTPException(status_code=403, detail="账号已被禁用")
    token = login_user(req.username, req.password)
    if token == "__disabled__":
        raise HTTPException(status_code=403, detail="账号已被禁用")
    if not token:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    user = get_user_by_token(token)
    # 标记管理员
    is_admin = (req.username == "admin")
    return {"success": True, "message": "登录成功", "token": token, "user": user, "is_admin": is_admin}


@router.get("/me")
async def me(authorization: str = Header("")):
    """获取当前用户信息"""
    user = get_current_user(authorization)
    return {"success": True, "user": user}


@router.put("/update-name")
async def update_name(req: AuthRequest, authorization: str = Header("")):
    """修改用户显示名"""
    from ...services.auth_service import update_user_name
    user = get_current_user(authorization)
    if not req.name:
        raise HTTPException(status_code=400, detail="名字不能为空")
    uname = user.get("username", "")
    if update_user_name(uname, req.name):
        # 同步更新 profiles.json
        try:
            from pathlib import Path
            import json as _json
            pf = Path(__file__).parent.parent.parent / "data" / "profiles.json"
            profiles = _json.load(open(pf, encoding="utf-8")) if pf.exists() else {}
            if uname in profiles:
                profiles[uname]["name"] = req.name
            else:
                profiles[uname] = {"name": req.name, "filled": True}
            _json.dump(profiles, open(pf, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        except: pass
        return {"success": True, "message": "名字已更新"}
    raise HTTPException(status_code=404, detail="用户不存在")


@router.post("/logout")
async def logout(authorization: str = Header("")):
    """退出登录"""
    if authorization.startswith("Bearer "):
        logout_user(authorization[7:])
    return {"success": True, "message": "已退出"}
