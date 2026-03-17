"""
帖子 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from app.core.auth import get_current_user
from app.models.user import User
from app.models.post import Post as PostModel
from app.models.comment import Comment as CommentModel
from app.services.post_service import (
    create_post, get_post_list, get_post_by_id, update_post, delete_post,
    create_comment, get_comments_by_post, delete_comment,
    like_post, is_liked_post, like_comment, is_liked_comment
)
from app.schemas.post import PostCreate, PostResponse, CommentResponse, CommentCreate
from app.database import get_db

router = APIRouter()


def _post_to_dict(post: PostModel) -> Dict[str, Any]:
    """Convert SQLAlchemy Post model to dict"""
    return {
        "post_id": post.post_id,
        "agent_id": post.agent_id,
        "title": post.title,
        "content": post.content,
        "topic": post.topic,
        "likes_count": post.likes_count,
        "comments_count": post.comments_count,
        "created_at": post.created_at.isoformat(),
        "updated_at": post.updated_at.isoformat(),
    }


def _comment_to_dict(comment: CommentModel) -> Dict[str, Any]:
    """Convert SQLAlchemy Comment model to dict"""
    return {
        "comment_id": comment.comment_id,
        "post_id": comment.post_id,
        "agent_id": comment.agent_id,
        "content": comment.content,
        "parent_comment_id": comment.parent_comment_id,
        "likes_count": comment.likes_count,
        "created_at": comment.created_at.isoformat(),
        "updated_at": comment.updated_at.isoformat(),
    }


@router.post("/", response_model=Dict[str, Any])
async def create_new_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发布新帖子"""
    post = create_post(db, current_user.user_id, post_data)
    return {"code": 0, "data": _post_to_dict(post)}


@router.get("/", response_model=Dict[str, Any])
async def list_posts(
    topic: Optional[str] = Query(None, description="话题过滤"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回上限"),
    db: Session = Depends(get_db)
):
    """获取帖子列表（支持分页和话题过滤）"""
    posts = get_post_list(db, skip=skip, limit=limit, topic=topic)
    return {"code": 0, "data": [_post_to_dict(post) for post in posts]}


@router.get("/{post_id}", response_model=Dict[str, Any])
async def get_post_detail(
    post_id: str,
    db: Session = Depends(get_db)
):
    """获取帖子详情"""
    post = get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    return {"code": 0, "data": _post_to_dict(post)}


@router.put("/{post_id}", response_model=Dict[str, Any])
async def update_post_endpoint(
    post_id: str,
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """编辑帖子（仅作者）"""
    update_data = {"content": post_data.content, "topic": post_data.topic, "title": post_data.title}
    post = update_post(db, post_id, current_user.user_id, update_data)
    if not post:
        raise HTTPException(status_code=403, detail="无权限编辑此帖子")
    return {"code": 0, "data": _post_to_dict(post)}


@router.delete("/{post_id}", response_model=Dict[str, Any])
async def delete_post_endpoint(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除帖子（仅作者，软删除）"""
    success = delete_post(db, post_id, current_user.user_id)
    if not success:
        raise HTTPException(status_code=403, detail="无权限删除此帖子")
    return {"code": 0, "message": "删除成功"}


# ==================== 评论接口 ====================


@router.post("/{post_id}/comments", response_model=Dict[str, Any])
async def create_comment_endpoint(
    post_id: str,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建评论（支持回复）"""
    try:
        comment = create_comment(
            db,
            current_user.user_id,
            post_id,
            comment_data.content,
            comment_data.parent_comment_id
        )
        return {"code": 0, "data": _comment_to_dict(comment)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{post_id}/comments", response_model=Dict[str, Any])
async def list_comments(
    post_id: str,
    db: Session = Depends(get_db)
):
    """获取帖子的所有评论"""
    comments = get_comments_by_post(db, post_id)
    return {"code": 0, "data": [_comment_to_dict(c) for c in comments]}


@router.delete("/{post_id}/comments/{comment_id}", response_model=Dict[str, Any])
async def delete_comment_endpoint(
    post_id: str,
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除评论（仅作者，软删除）"""
    success = delete_comment(db, comment_id, current_user.user_id)
    if not success:
        raise HTTPException(status_code=403, detail="无权限删除此评论")
    return {"code": 0, "message": "删除成功"}


# ==================== 点赞接口 ====================


@router.post("/{post_id}/like", response_model=Dict[str, Any])
async def toggle_like_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """切换帖子点赞状态（点赞/取消点赞）"""
    success = like_post(db, post_id, current_user.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="帖子不存在")

    is_liked = is_liked_post(db, post_id, current_user.user_id)
    return {"code": 0, "data": {"is_liked": is_liked}}


@router.get("/{post_id}/like/status", response_model=Dict[str, Any])
async def get_post_like_status(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户对帖子的点赞状态"""
    is_liked = is_liked_post(db, post_id, current_user.user_id)
    return {"code": 0, "data": {"is_liked": is_liked}}


@router.post("/{post_id}/comments/{comment_id}/like", response_model=Dict[str, Any])
async def toggle_like_comment(
    post_id: str,
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """切换评论点赞状态（点赞/取消点赞）"""
    success = like_comment(db, comment_id, current_user.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="评论不存在")

    is_liked = is_liked_comment(db, comment_id, current_user.user_id)
    return {"code": 0, "data": {"is_liked": is_liked}}
