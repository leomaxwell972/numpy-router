# numpy_router/__init__.py
import os

if os.environ.get("NUMPY_ROUTER_OFF") == "1":
    # Disable router completely, behave like native numpy
    import importlib, sys
    real_numpy = importlib.import_module("numpy")
    sys.modules["numpy"] = real_numpy
    sys.modules[__name__] = real_numpy
    import numpy
else:
    
    import sys
    import importlib
    from .core import resolve_numpy_version_for_caller, ensure_numpy_version_path
    
    def cache():
        from .core import CACHE_DIR
        if not CACHE_DIR.exists():
            return []
        return sorted([p.name for p in CACHE_DIR.iterdir() if p.is_dir() and p.name != "_downloads"])
        # Usage:
        # import numpy_router
        # print(numpy_router.cache())
        # returns list of cached numpy versions
    
    def _is_shim(mod):
        return getattr(mod, "__numpy_router_shim__", False) is True
    
    
    def _bootstrap():
        from .core import resolve_numpy_version_for_caller, ensure_numpy_version_path
        import sys as _sys
        import importlib as _importlib
    
        version = resolve_numpy_version_for_caller()
        base_path = ensure_numpy_version_path(version)
    
        if base_path not in _sys.path:
            _sys.path.insert(0, base_path)
    
        # Kill the shim/proxy so importlib doesn't route back through us
        _sys.modules.pop("numpy", None)
    
        real_numpy = _importlib.import_module("numpy")
    
        _sys.modules["numpy"] = real_numpy
        _sys.modules[__name__] = real_numpy
        return real_numpy
    
    
    
    def _wrap_shim():
        mod = sys.modules.get("numpy")
        if not mod or not _is_shim(mod):
            return
    
        class _ShimProxy:
            def __getattr__(self, name):
                real = _bootstrap()
                return getattr(real, name)
    
            def __dir__(self):
                real = _bootstrap()
                return dir(real)
    
        sys.modules["numpy"] = _ShimProxy()
    
    
    _wrap_shim()
