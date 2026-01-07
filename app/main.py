# Compatibility shim for Python 3.13's typing.ForwardRef API
# Tolerate either positional or keyword recursive_guard by wrapping _evaluate
try:
    import typing
    import inspect
    def _patch_forwardref():
        for name in ("ForwardRef", "_ForwardRef"):
            cls = getattr(typing, name, None)
            if cls is None:
                continue
            orig = getattr(cls, "_evaluate", None)
            if orig is None:
                continue
            sig = inspect.signature(orig)
            # If recursive_guard is already an ordinary parameter (not keyword-only), skip
            param = sig.parameters.get('recursive_guard')
            if param is None or param.kind != inspect.Parameter.KEYWORD_ONLY:
                continue
            # wrap so positional third arg (set()) is accepted and forwarded as keyword
            def make_wrapper(orig):
                def wrapper(self, globalns, localns=None, *args, **kwargs):
                    if args:
                        rg = args[0]
                        if not isinstance(rg, set):
                            try:
                                rg = set(rg)
                            except Exception:
                                rg = set()
                        kwargs['recursive_guard'] = rg
                    return orig(self, globalns, localns, **kwargs)
                return wrapper
            cls._evaluate = make_wrapper(orig)
    _patch_forwardref()
except Exception:
    # best-effort: if typing API changed we skip shim
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.jd_routes import router as jd_router

app = FastAPI(
    title="Agentic Recruitment Backend",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],  # Allow frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jd_router)

@app.get("/")
def health():
    return {"status": "ok"}
