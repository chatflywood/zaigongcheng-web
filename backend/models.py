# -*- coding: utf-8 -*-
"""
数据库模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, create_engine, UniqueConstraint, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "analysis.db")

# 确保 data 目录存在
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# 创建引擎
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

# 创建会话
SessionLocal = sessionmaker(bind=engine)

# 基础类
Base = declarative_base()


class ZaigongRecord(Base):
    """在建工程分析记录"""
    __tablename__ = "zaigong_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uploaded_at = Column(DateTime, default=datetime.now, index=True)
    source_filename = Column(String(255))
    file_date = Column(String(20))  # 从文件名提取的日期，如 "0320"
    summary_data = Column(Text)  # JSON 存储汇总数据
    metrics_data = Column(Text)  # JSON 存储指标数据
    detail_data = Column(Text)  # JSON 存储明细数据（工程维度）
    four_class_warnings = Column(Text)  # JSON 存储四类工程预警数据
    target_value = Column(Float, default=503.0)  # 当期目标

    def __repr__(self):
        return f"<ZaigongRecord {self.id} - {self.uploaded_at}>"


class BudgetRecord(Base):
    """预算分析记录"""
    __tablename__ = "budget_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uploaded_at = Column(DateTime, default=datetime.now, index=True)
    source_filename = Column(String(255))
    budget_data = Column(Text)  # JSON 存储预算数据

    def __repr__(self):
        return f"<BudgetRecord {self.id} - {self.uploaded_at}>"


class AppConfig(Base):
    """应用配置（键值对）"""
    __tablename__ = "app_config"

    key = Column(String(100), primary_key=True)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.now)


class ArchiveRecord(Base):
    """数据档案记录"""
    __tablename__ = "archive_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uploaded_at = Column(DateTime, default=datetime.now, index=True)
    category = Column(String(50), index=True)   # 年度建设情况 / 多年趋势汇总 / 投资预算报告
    year = Column(String(10))                    # 如 "2025"
    original_filename = Column(String(255))
    stored_filename = Column(String(255))        # 磁盘上的实际文件名
    file_size = Column(Integer)                  # 字节数
    note = Column(Text, default='')

    def __repr__(self):
        return f"<ArchiveRecord {self.id} {self.category} {self.year}>"


class BatchSpecialty(Base):
    """投资预算批次专业列表（可配置）"""
    __tablename__ = "batch_specialties"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)


class BudgetBatch(Base):
    """投资预算批次下达记录"""
    __tablename__ = "budget_batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_date = Column(String(20), nullable=False)   # "2026-01-08"
    note = Column(Text, default='')                    # 用途说明
    amounts = Column(Text, default='{}')               # JSON: {专业名: 金额}
    notes = Column(Text, default='{}')                # JSON: {专业名: "批注文字"}
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<BudgetBatch {self.id} {self.batch_date}>"


DEFAULT_SPECIALTIES = [
    "5G无线网及配套", "STN", "综合业务接入区", "有线接入网", "组网专线",
    "ICT、私有云", "5G定制网", "IDC", "传输光缆", "传输设备", "数据网",
    "局房及管道", "电源（DC）", "双碳", "其他", "云", "能力平台",
    "网信安全", "运营系统", "核心网", "科创", "置换料堪用料等增加", "上年预借还原等清算",
]


def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)
    # 为已有数据库补充 notes 列（幂等）
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE budget_batches ADD COLUMN notes TEXT DEFAULT '{}'"))
            conn.commit()
        except Exception:
            pass
    # 写入默认专业列表（仅首次，幂等）
    db = SessionLocal()
    try:
        if db.query(BatchSpecialty).count() == 0:
            for i, name in enumerate(DEFAULT_SPECIALTIES):
                db.add(BatchSpecialty(name=name, sort_order=i))
            db.commit()
    finally:
        db.close()


def get_db():
    """获取数据库会话"""
    return SessionLocal()
