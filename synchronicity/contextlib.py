from .utils import filter_traceback

class AsyncGeneratorContextManager:
    """ This is basically copied (but slightly modified) from contextlib.py

    We could have just synchronized the built-in class, but it was added in Python 3.7, so
    we're including most of the logic here, in order to make it work with Python 3.6 as well.
    """
    def __init__(self, synchronizer, func, args, kwargs):
        self.synchronizer = synchronizer
        # Run it in the correct thread
        self.gen = synchronizer._run_generator_async(func(*args, **kwargs))

    async def _enter(self):
        try:
            return await self.gen.__anext__()
        except StopAsyncIteration:
            raise RuntimeError("generator didn't yield") from None
        
    async def _exit(self, typ, value, traceback):
        if typ is None:
            try:
                await self.gen.__anext__()
            except StopAsyncIteration:
                return False
            else:
                raise RuntimeError("generator didn't stop")
        else:
            if value is None:
                value = typ()
            try:
                ret = self.gen.athrow(typ, value, traceback)
                await ret
            except StopAsyncIteration as exc:
                return exc is not value
            except RuntimeError as exc:
                if exc is value:
                    return False
                if isinstance(value, (StopIteration, StopAsyncIteration)) and exc.__cause__ is value:
                    return False
                raise
            except BaseException as exc:
                if exc is not value:
                    raise
                return False
            raise RuntimeError("generator didn't stop after athrow()")

    # Actual methods

    @filter_traceback
    async def __aenter__(self):
        return await self.synchronizer._run_function_async(self._enter())
                    
    @filter_traceback
    def __enter__(self):
        return self.synchronizer._run_function_sync(self._enter(), False)

    @filter_traceback
    async def __aexit__(self, typ, value, traceback):
        ret =  await self.synchronizer._run_function_async(self._exit(typ, value, traceback))
        return ret

    @filter_traceback
    def __exit__(self, typ, value, traceback):
        return self.synchronizer._run_function_sync(self._exit(typ, value, traceback), False)
