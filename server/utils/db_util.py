
import sys
import os

from tasks.models import DATABASE_URL, Base

# 将项目根目录添加到 Python 路径中
# project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(project_root)

from typing import Dict, List
from sqlalchemy import create_engine, inspect, select, text, update
from sqlalchemy.orm import Session



# class DbUtils:
#     _instance = None
    
#     _engine = None


#     def __new__(cls):
#         if cls._instance is None:
#             # 初始化数据库连接
#             cls._engine = create_engine(DATABASE_URL)
            
#             with cls._engine.connect() as conn:
#                 # 检查 'chat_session' 表是否存在于数据库中, 如果不存在，创建表
#                 result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename = 'chat_session'"))
#                 if not result.fetchall():
#                     Base.metadata.create_all(cls._engine)
            
#             cls._instance = super(DbUtils, cls).__new__(cls)
#         return cls._instance
    
#     # @classmethod
#     def save_all(self, data_list: List[Base]):
#         if not data_list or len(data_list) == 0:
#             return
#         new_id_list = []
#         clz = data_list[0].__class__
#         with Session(self._engine) as session:
#             # 查找已经存在的记录ID
#             existing_ids = session.scalars(select(clz.id)).all()
#             # 过滤掉已经存在记录的数据
#             new_data_list = [item for item in data_list if item.id not in existing_ids]

#             new_id_list = [item.id for item in new_data_list]
            
#             # 添加并持久化新数据
#             session.add_all(new_data_list)
#             session.commit()
        
#         return new_id_list

    
#     # @classmethod
#     def save(self, data: Base):
#         if not data:
#             return
#         with Session(self._engine) as session:
#             session.add(data)
#             session.commit()
    
#     # @classmethod
#     def update_all(self, clz_update, data_list: List[Dict]):
        
#         with Session(self._engine) as session:
#             session.execute(update(clz_update), data_list)
#             # session.bulk_update_mappings(clz_update, data_list)
#             session.commit()

    
#     # @classmethod
#     def update(self, clz_update, data):
        
#         with Session(self._engine) as session:
#             session.execute(update(clz_update), data)
#             session.commit()

#     # @classmethod
#     def get_content_empty_ids(self, model_class):
#         with Session(self._engine) as session:
#             return session.scalars(select(model_class.id).where(model_class.content_md.__eq__(""))).all()  # .query(model_class).filter_by(content_md="")

#     # @classmethod
#     def get_by_id(self, model_class, id):
#         with Session(self._engine) as session:
#             return session.query(model_class).filter_by(id=id).first()
        
    
#     # @classmethod
#     def get_by(self, model_class, **kwargs):
#         with Session(self._engine) as session:
#             return session.query(model_class).filter_by(kwargs).all()
        
    
#     # @classmethod
#     def get_sorted(self, model_class: Base, **kwargs):
#         with Session(self._engine) as session:
#             return session.query(model_class).filter_by(**kwargs)\
#                 .order_by(model_class.updated_at.desc()).all()

class DbUtils:
    _instance = None
    
    _engine = None


    def __new__(cls):
        if cls._instance is None:
            # 初始化数据库连接
            cls._engine = create_engine(DATABASE_URL)
            
            with cls._engine.connect() as conn:
                # 检查 'chat_session' 表是否存在于数据库中, 如果不存在，创建表
                result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename = 'chat_session'"))
                if not result.fetchall():
                    Base.metadata.create_all(cls._engine)
            
            cls._instance = super(DbUtils, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def save_all(cls, data_list: List[Base]):
        if not data_list or len(data_list) == 0:
            return
        new_id_list = []
        clz = data_list[0].__class__
        with Session(cls._engine) as session:
            # 查找已经存在的记录ID
            existing_ids = session.scalars(select(clz.id)).all()
            # 过滤掉已经存在记录的数据
            new_data_list = [item for item in data_list if item.id not in existing_ids]

            new_id_list = [item.id for item in new_data_list]
            
            # 添加并持久化新数据
            session.add_all(new_data_list)
            session.commit()
        
        return new_id_list

    
    @classmethod
    def save(cls, data: Base):
        if not data:
            return
        with Session(cls._engine) as session:
            session.add(data)
            session.commit()
    
    @classmethod
    def update_all(cls, clz_update, data_list: List[Dict]):
        
        with Session(cls._engine) as session:
            session.execute(update(clz_update), data_list)
            # session.bulk_update_mappings(clz_update, data_list)
            session.commit()

    
    @classmethod
    def update(cls, clz_update, data):
        
        with Session(cls._engine) as session:
            session.execute(update(clz_update), data)
            session.commit()

    @classmethod
    def get_content_empty_ids(cls, model_class):
        with Session(cls._engine) as session:
            return session.scalars(select(model_class.id).where(model_class.content_md.__eq__(""))).all()  # .query(model_class).filter_by(content_md="")

    @classmethod
    def get_by_id(cls, model_class, id):
        with Session(cls._engine) as session:
            return session.query(model_class).filter_by(id=id).first()
        
    
    @classmethod
    def get_by(cls, model_class, **kwargs):
        with Session(cls._engine) as session:
            return session.query(model_class).filter_by(**kwargs).all()
        
    
    @classmethod
    def get_sorted(cls, model_class: Base, **kwargs):
        with Session(cls._engine) as session:
            return session.query(model_class).filter_by(**kwargs)\
                .order_by(model_class.updated_at.desc()).all()
        