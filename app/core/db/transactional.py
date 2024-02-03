from functools import wraps
from contextvars import ContextVar
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_sync_session, get_async_session, session

# Context variable for async session
async_session_context: ContextVar[AsyncSession] = ContextVar("async_session_context")

class AsyncTransactional:
    def __call__(self, func):
        @wraps(func)
        async def _transactional(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e

            return result

        return _transactional


 

# from functools import wraps

# from app.core.db import session

# # This part makes sure that tasks involving changing data are done completely and correctly
# class Transactional:
#     def __call__(self, func):
#         @wraps(func)
#         async def _transactional(*args, **kwargs):
#             try:
#                 result = await func(*args, **kwargs)
#                 await session.commit()
#             except Exception as e:
#                 await session.rollback()
#                 raise e

#             return result

#         return _transactional
