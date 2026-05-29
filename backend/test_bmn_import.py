import sys, types, os

# 在一切导入之前 mock pwd 模块
_pwd = types.ModuleType("pwd")
class _FakePw:
    pw_name = "user"
_pwd.getpwuid = lambda uid: _FakePw()
_pwd.getpwnam = lambda name: _FakePw()
sys.modules["pwd"] = _pwd

os.environ.setdefault("USERNAME", "user")
os.environ.setdefault("USER", "user")

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

print("Testing main.py import...")
try:
    from app.main import app
    print("IMPORT OK")
    print("\nBMN routes:")
    for route in app.routes:
        path = getattr(route, "path", "")
        if "bmn" in path or "workflow" in path:
            methods = list(getattr(route, "methods", set()))
            print(f"  {methods} {path}")
    print("\nAll routes count:", len(app.routes))
except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()
