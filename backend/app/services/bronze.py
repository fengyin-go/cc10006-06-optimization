"""原始层管理业务规则：登记、修改、版本流转与目录血缘联动都收在这里。

核心约定：
- 登记与修改都完整持久化 8 个业务字段，非法保留天数直接拒绝；
- 同一表编号再次录入时生成新版本，历史版本退出当前同步但保留可查；
- 每次有效写入都把分区规则、保留策略、压缩类型、数据校验同步到数据目录，
  保留策略变更同时把血缘节点的采集状态置为待校验（待重新采集）；
- 修改走乐观并发：提交时带期望版本，版本不一致即退回并说明现网采用的版本。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from app.store import store

MODULE = "bronze"
REQUIRED_FIELDS = ["表编号", "来源通道", "目标路径", "保留策略", "分区规则", "文件格式", "压缩类型", "数据校验"]
STATUS_ORDER = ["草稿", "待校验", "已启用", "已停用"]
ACTION_RULES = {"提交校验": "待校验", "启用同步": "已启用", "停用同步": "已停用"}
NEGATIVE_ACTIONS = ["停用同步"]

SYNC_CURRENT = "当前同步"
SYNC_RETIRED = "已退出同步"

PARTITION_RULES = {"dt", "hour", "dt,hour", "none"}
FILE_FORMATS = {"parquet", "orc", "avro", "json", "csv"}
COMPRESSION_TYPES = {"zstd", "snappy", "gzip", "lz4", "none"}
MAX_RETENTION_DAYS = 3650


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _next_id(rows: list[dict[str, Any]]) -> int:
    return max((int(row.get("id", 0)) for row in rows), default=0) + 1


def _clean(values: dict[str, Any]) -> dict[str, str]:
    return {field: str(values.get(field) or "").strip() for field in REQUIRED_FIELDS}


def _check_retention(raw: str) -> str | None:
    text = raw[:-1] if raw.endswith("天") else raw
    if not text.isdigit():
        return f"保留策略「{raw}」非法：保留天数需为 1-{MAX_RETENTION_DAYS} 的整数"
    if not 1 <= int(text) <= MAX_RETENTION_DAYS:
        return f"保留策略「{raw}」非法：保留天数需在 1-{MAX_RETENTION_DAYS} 之间"
    return None


def _validate(clean: dict[str, str]) -> list[str]:
    errors: list[str] = []
    missing = [field for field in REQUIRED_FIELDS if not clean[field]]
    if missing:
        errors.append(f"缺少必填字段：{'、'.join(missing)}")
    if clean["保留策略"]:
        retention_error = _check_retention(clean["保留策略"])
        if retention_error:
            errors.append(retention_error)
    choices = (
        ("分区规则", PARTITION_RULES),
        ("文件格式", FILE_FORMATS),
        ("压缩类型", COMPRESSION_TYPES),
    )
    for field, allowed in choices:
        value = clean[field]
        if value and value.lower() not in allowed:
            errors.append(f"{field}「{value}」非法：仅支持 {'、'.join(sorted(allowed))}")
    return errors


class BronzeService:
    def list_entries(
        self,
        *,
        keyword: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        rows = store.rows(MODULE)
        if keyword:
            rows = [row for row in rows if keyword in str(row.get("表编号", ""))]
        if status:
            rows = [row for row in rows if row.get("status") == status]
        total = len(rows)
        start = max(page - 1, 0) * size
        return rows[start:start + size], total

    def get_entry(self, entry_id: int) -> dict[str, Any] | None:
        return store.find(MODULE, entry_id)

    def versions_of(self, entry_id: int) -> list[dict[str, Any]] | None:
        """同一表编号的全部版本，新的在前；旧配置退出同步后依然可查。"""
        entry = store.find(MODULE, entry_id)
        if entry is None:
            return None
        code = entry.get("表编号")
        versions = [row for row in store.rows(MODULE) if row.get("表编号") == code]
        return sorted(versions, key=lambda row: int(row.get("版本", 1)), reverse=True)

    def sync_state(self, entry_id: int) -> dict[str, Any] | None:
        """该表编号在目录与血缘里的同步结果，用来核对各处采集记录是否对得上。"""
        entry = store.find(MODULE, entry_id)
        if entry is None:
            return None
        code = entry.get("表编号")
        catalog = next((row for row in store.rows("catalog") if row.get("来源表编号") == code), None)
        lineage = next((row for row in store.rows("lineage") if row.get("来源表编号") == code), None)
        return {"catalog": catalog, "lineage": lineage}

    def create_entry(self, values: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str], str]:
        """登记原始表：完整持久化业务字段；同表编号再次录入时历史版本退出当前同步。"""
        clean = _clean(values)
        errors = _validate(clean)
        if errors:
            return None, errors, ""
        rows = store.rows(MODULE)
        code = clean["表编号"]
        history = [row for row in rows if row.get("表编号") == code]
        previous = max(history, key=lambda row: int(row.get("版本", 1)), default=None)
        version = int(previous.get("版本", 1)) + 1 if previous is not None else 1
        for old in history:
            old["status"] = STATUS_ORDER[-1]
            old["pending"] = False
            old["同步状态"] = SYNC_RETIRED
        entry: dict[str, Any] = {"id": _next_id(rows)}
        entry.update(clean)
        entry["status"] = STATUS_ORDER[0]
        entry["pending"] = True
        entry["abnormal"] = False
        entry["版本"] = version
        entry["同步状态"] = SYNC_CURRENT
        entry["登记时间"] = _now()
        entry["变更历史"] = []
        rows.append(entry)
        retention_changed = previous is not None and str(previous.get("保留策略", "")).strip() != clean["保留策略"]
        self._sync_catalog(entry)
        self._sync_lineage(entry, retention_changed=retention_changed)
        if previous is not None:
            message = f"原始表 {code} 已登记为 v{version}：历史版本已退出当前同步，现网只跟随最新分区版本"
        else:
            message = f"原始表 {code} 已登记为 v1，目录与血缘采集已同步"
        return entry, [], message

    def update_entry(
        self,
        entry_id: int,
        values: dict[str, Any],
        expected_version: int | None,
    ) -> tuple[dict[str, Any] | None, str, str]:
        """修改当前版本：乐观并发控制，冲突时退回并给出现网采用的版本。

        返回 (记录, 提示语, 结果)，结果取 ok / not_found / conflict / invalid。
        """
        entry = store.find(MODULE, entry_id)
        if entry is None:
            return None, f"原始表 {entry_id} 不存在或已归档", "not_found"
        code = str(entry.get("表编号", ""))
        current = self._current_of(code)
        if entry.get("同步状态", SYNC_CURRENT) == SYNC_RETIRED:
            adopted = int((current or entry).get("版本", 1))
            return current, f"该版本（v{entry.get('版本', 1)}）已退出当前同步，现网采用 v{adopted}，请基于最新版本修改", "conflict"
        current_version = int(entry.get("版本", 1))
        if expected_version is None:
            return entry, "缺少期望版本：请刷新后重新打开编辑再保存", "conflict"
        if int(expected_version) != current_version:
            message = (
                f"保存冲突：现网已采用 v{current_version}"
                f"（分区规则 {entry.get('分区规则')}、保留策略 {entry.get('保留策略')}、压缩类型 {entry.get('压缩类型')}）；"
                f"本次提交基于 v{expected_version}，已退回。请刷新后基于最新版本重新编辑"
            )
            return entry, message, "conflict"
        clean = _clean(values)
        clean["表编号"] = code  # 表编号是身份标识，修改链路不允许改写
        errors = _validate(clean)
        if errors:
            return None, "；".join(errors), "invalid"
        retention_changed = clean["保留策略"] != str(entry.get("保留策略", "")).strip()
        snapshot = {field: entry.get(field) for field in REQUIRED_FIELDS}
        snapshot["版本"] = current_version
        history = entry.setdefault("变更历史", [])
        history.append({"版本": current_version, "时间": _now(), "操作": "修改配置", "快照": snapshot})
        entry.update(clean)
        entry["版本"] = current_version + 1
        entry["更新时间"] = _now()
        self._sync_catalog(entry)
        self._sync_lineage(entry, retention_changed=retention_changed)
        return entry, f"原始表 {code} 已保存为 v{entry['版本']}，现网配置已采用本版", "ok"

    def run_action(self, entry_id: int, action: str) -> tuple[dict[str, Any] | None, str]:
        entry = store.find(MODULE, entry_id)
        if entry is None:
            return None, f"原始表 {entry_id} 不存在或已归档"
        if action not in ACTION_RULES:
            return None, f"动作「{action}」不属于原始层管理可执行范围"
        if entry.get("同步状态", SYNC_CURRENT) == SYNC_RETIRED:
            return None, f"原始表 {entry.get('表编号')} 的 v{entry.get('版本', 1)} 已退出当前同步，历史版本不再执行动作"
        target = ACTION_RULES[action]
        if target not in STATUS_ORDER:
            return None, f"目标状态「{target}」不在允许的状态序列里"
        entry["status"] = target
        entry["pending"] = target != STATUS_ORDER[-1]
        entry["abnormal"] = action in NEGATIVE_ACTIONS
        return entry, f"原始表已{action}"

    def _current_of(self, code: str) -> dict[str, Any] | None:
        history = [row for row in store.rows(MODULE) if row.get("表编号") == code]
        if not history:
            return None
        return max(history, key=lambda row: int(row.get("版本", 1)))

    def _sync_catalog(self, entry: dict[str, Any]) -> None:
        """把最新版本的业务属性写进数据目录，目录页与原始表页读取同一份结果。"""
        rows = store.rows("catalog")
        code = entry["表编号"]
        target = next((row for row in rows if row.get("来源表编号") == code), None)
        if target is None:
            target = {
                "id": _next_id(rows),
                "编目编号": f"CATA-{code}",
                "数据集名称": code,
                "所属分层": "原始层",
                "负责人": "平台同步",
                "业务域标签": "原始层自动编目",
                "status": "已发布",
                "pending": False,
                "abnormal": False,
                "来源表编号": code,
            }
            rows.append(target)
        target.update({
            "存储路径": entry["目标路径"],
            "文件格式": entry["文件格式"],
            "保留策略": entry["保留策略"],
            "分区规则": entry["分区规则"],
            "压缩类型": entry["压缩类型"],
            "数据校验": entry["数据校验"],
            "编目版本": f"v{entry['版本']}",
            "同步时间": _now(),
        })

    def _sync_lineage(self, entry: dict[str, Any], *, retention_changed: bool) -> None:
        """同步血缘节点；保留策略变更时把采集状态置为待校验，等待重新采集。"""
        rows = store.rows("lineage")
        code = entry["表编号"]
        node = next((row for row in rows if row.get("来源表编号") == code), None)
        if node is None:
            node = {
                "id": _next_id(rows),
                "节点编号": f"LINE-{code}",
                "节点类型": "原始表",
                "节点名称": code,
                "上游节点列表": entry["来源通道"],
                "下游节点列表": "",
                "status": "已启用",
                "pending": False,
                "abnormal": False,
                "来源表编号": code,
            }
            rows.append(node)
        node.update({
            "转换说明": f"保留策略 {entry['保留策略']}；分区规则 {entry['分区规则']}；压缩类型 {entry['压缩类型']}",
            "采集时间": _now(),
            "图谱版本": f"v{entry['版本']}",
            "保留策略": entry["保留策略"],
            "分区规则": entry["分区规则"],
            "压缩类型": entry["压缩类型"],
            "数据校验": entry["数据校验"],
        })
        if retention_changed:
            node["status"] = "待校验"
            node["pending"] = True
