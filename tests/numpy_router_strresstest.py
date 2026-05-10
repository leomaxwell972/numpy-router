import importlib
import traceback

modules_to_test = [
    "pandas",
    "scipy",
    "sklearn",
    "matplotlib",
    "seaborn",
    "numexpr",
    "xarray",
    "dask.array",
    "torch",
    "torchvision",
    "torchaudio",
    "transformers",
    "accelerate",
    "tqdm",
    "statsmodels",
    "sympy",
    "jax",
    "jax.numpy",
    "cv2",
    "imageio",
]

print("\n=== NUMPY ROUTER STRESS TEST ===\n")

for mod in modules_to_test:
    print(f"--- Testing import: {mod}")
    try:
        imported = importlib.import_module(mod)
        print(f"OK: {mod} imported successfully")
    except Exception as e:
        print(f"FAIL: {mod} threw an exception:")
        traceback.print_exc()
    print()

print("=== TEST COMPLETE ===")
