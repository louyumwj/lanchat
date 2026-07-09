from __future__ import annotations

from storage.sqlite_backend import SQLiteBackend


class MySQLBackend(SQLiteBackend):
    """MySQL 后端占位实现。

    当前代码保留完整工厂入口和配置结构。实际生产连接 MySQL 时，可把本类中的
    sqlite3 调用替换为 aiomysql 连接池；业务层不需要修改。
    """

    def __init__(self, config: dict) -> None:
        database = config.get("database") or "langchain_chat"
        super().__init__(f"data/mysql-sim/{database}.db")
        self.config = config
