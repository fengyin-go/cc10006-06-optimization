"""业务模块路由汇总。

这里统一按别名导入再暴露 ROUTERS：模块名有可能和内置名撞车（某个业务模块就叫 dict、list
这种名字时），按名字直接 import 会把内置类型覆盖掉，函数注解在运行时求值就会报
'module' object is not subscriptable。
"""
from __future__ import annotations

from app.routers import catalog as router_catalog
from app.routers import ingest as router_ingest
from app.routers import bronze as router_bronze
from app.routers import silver as router_silver
from app.routers import gold as router_gold
from app.routers import lakezone as router_lakezone
from app.routers import stream as router_stream
from app.routers import batch as router_batch
from app.routers import snapshot as router_snapshot
from app.routers import govern as router_govern
from app.routers import meta as router_meta
from app.routers import lineage as router_lineage
from app.routers import quality as router_quality
from app.routers import schedule as router_schedule
from app.routers import backfill as router_backfill
from app.routers import search as router_search
from app.routers import resource as router_resource
from app.routers import audit as router_audit

ROUTERS = [router_catalog, router_ingest, router_bronze, router_silver, router_gold, router_lakezone, router_stream, router_batch, router_snapshot, router_govern, router_meta, router_lineage, router_quality, router_schedule, router_backfill, router_search, router_resource, router_audit]
