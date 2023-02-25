from sqlalchemy.orm.query import Select
from sqlalchemy.ext.asyncio.session import AsyncSession
from asyncio import iscoroutinefunction
from sqlalchemy import func


class StatementExecutor:
    """
        Shortcut for working with data
    """
    base_statement: Select

    def __init__(self, select_instance):
        self.base_statement = select_instance

    def __call__(self, *args, **kwargs):
        return self.base_statement

    async def a_perform_selection(self, session: AsyncSession, **query_params):
        """
        Paginates query
        :param session: ses to extract data
        :param query_params: limit, offset
        :return:
        """
        new_select = self.base_statement
        if isinstance(self.base_statement, Select):
            if isinstance(limit := query_params.get('limit'), int):
                new_select = self.base_statement.limit(limit)
            if isinstance(off := query_params.get('offset'), int):
                new_select = self.base_statement.offset(off)
        return await session.scalars(self.base_statement)

    async def aget_count(self, session: AsyncSession):
        query = self.base_statement.with_only_columns(func.count())
        return await session.scalar(query)


def exec_statement(make_statement_func):
    async def wrapper(*args, **kwargs):
        if iscoroutinefunction(make_statement_func):
            stmt: Select = await make_statement_func(*args, **kwargs)
        else:
            stmt: Select = make_statement_func(*args, **kwargs)
        return StatementExecutor(stmt)

    return wrapper
