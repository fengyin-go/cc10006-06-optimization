"""原始层管理接口：维护原始表，覆盖登记、修改、版本查询与提交校验、启用同步、停用同步等动作。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.schemas import ActionResult, EntryPayload, PageResult
from app.services.bronze import BronzeService

router = APIRouter(prefix="/api/bronze", tags=["原始层管理"])

service = BronzeService()


@router.get("", response_model=PageResult[dict])
def list_entries(
    keyword: str | None = Query(default=None, description="按表编号检索"),
    status: str | None = Query(default=None, description="草稿、待校验、已启用、已停用"),
    page: int = 1,
    size: int = 20,
) -> PageResult[dict]:
    """按表编号与状态过滤原始层管理列表；没有数据时返回空页，不报错。"""
    if size > 200:
        raise HTTPException(status_code=400, detail="每页最多 200 条，请缩小分页范围")
    items, total = service.list_entries(keyword=keyword, status=status, page=page, size=size)
    return PageResult(items=items, total=total, page=page, size=size)


@router.get("/export")
def export_entries() -> dict[str, Any]:
    """导出原始层管理清单：返回当前过滤条件下的全量数据。"""
    items, total = service.list_entries(page=1, size=10000)
    return {"module": "bronze", "total": total, "items": items}


@router.get("/{entry_id}", response_model=dict)
def get_entry(entry_id: int) -> dict:
    """读取单条原始表明细；不存在时给出可读的错误说明。"""
    entry = service.get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"原始表 {entry_id} 不存在或已归档")
    return entry


@router.get("/{entry_id}/versions", response_model=dict)
def list_versions(entry_id: int) -> dict[str, Any]:
    """同一表编号的全部版本：现网只跟随最新版本，历史版本退出同步但依然可查。"""
    versions = service.versions_of(entry_id)
    if versions is None:
        raise HTTPException(status_code=404, detail=f"原始表 {entry_id} 不存在或已归档")
    return {"items": versions, "total": len(versions)}


@router.get("/{entry_id}/sync", response_model=dict)
def get_sync_state(entry_id: int) -> dict[str, Any]:
    """该表编号在数据目录与血缘图谱里的同步结果，用于核对各处采集记录。"""
    state = service.sync_state(entry_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"原始表 {entry_id} 不存在或已归档")
    return state


@router.post("", response_model=ActionResult)
def create_entry(payload: EntryPayload) -> ActionResult:
    """登记一条原始表：完整持久化业务字段；同表编号再次录入时历史版本退出当前同步。"""
    entry, errors, message = service.create_entry(payload.values)
    if errors:
        return ActionResult(ok=False, message="；".join(errors))
    return ActionResult(ok=True, message=message, entry=entry)


@router.put("/{entry_id}", response_model=ActionResult)
def update_entry(entry_id: int, payload: EntryPayload) -> ActionResult:
    """修改当前版本：携带期望版本做乐观并发校验，冲突时退回并说明现网采用的版本。"""
    entry, message, outcome = service.update_entry(entry_id, payload.values, payload.expected_version)
    if outcome == "not_found":
        raise HTTPException(status_code=404, detail=message)
    if outcome == "conflict":
        raise HTTPException(status_code=409, detail={"message": message, "adopted": entry})
    if outcome == "invalid":
        return ActionResult(ok=False, message=message)
    return ActionResult(ok=True, message=message, entry=entry)


@router.post("/{entry_id}/actions", response_model=ActionResult)
def run_action(entry_id: int, payload: EntryPayload) -> ActionResult:
    """对单条原始表执行提交校验、启用同步、停用同步；不允许的动作会被拦下并说明原因。"""
    action = str(payload.values.get("action") or "").strip()
    entry, message = service.run_action(entry_id, action)
    if entry is None:
        return ActionResult(ok=False, message=message)
    return ActionResult(ok=True, message=message, entry=entry)
