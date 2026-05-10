# numpy-router

A lightweight runtime NumPy version router.  
It allows Python applications to use different NumPy versions without reinstalling or modifying the environment.

The router intercepts the first real use of `numpy` and loads the appropriate version from a local cache.  
It works with embedded Python distributions, machine‑learning frameworks, and environments where NumPy cannot be freely installed or upgraded.

---

## Features

- Lazy bootstrap: NumPy loads only when actually used.
- Version selection:
  - `requirements.txt` next to the main script
  - package `dist-info` metadata
  - user‑forced version via environment variable
  - fallback heuristic
- Router bypass switch.
- Cache inspection API.
- Compatible with native NumPy installations.

---

## Installation

`pip install numpy-router`


Then place the provided `numpy_router.pth` file into your Python `site-packages` directory.

---

## Environment Variables

### `NUMPY_ROUTER_VERSION=X.Y.Z`
Force a specific NumPy version.

### `NUMPY_ROUTER_OFF=1`
Disable the router entirely and use native NumPy.

### `NUMPY_ROUTER_CACHE=PATH`
Override the cache directory.

---

## Cache Inspection
---

```
python
import numpy_router
print(numpy_router.cache())
```

---

## How It Works
---

┌──────────────────────────┐
│ Python starts            │
│ site-packages loads .pth │
└───────────────┬──────────┘
                │
                ▼
      shim module installed
      as sys.modules["numpy"]
                │
                ▼
      numpy_router wraps shim
      with a lightweight proxy
                │
                ▼
   first attribute access on numpy
   (e.g., np.ndarray, np.array)
                │
                ▼
         bootstrap runs
   - resolve version
   - download if needed
   - extract to cache
   - load real NumPy
   - replace shim with real module
                │
                ▼
      all further imports use
          real NumPy


