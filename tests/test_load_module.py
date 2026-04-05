from zbxtemplar.modules import Context
from zbxtemplar.main import load_module
from tests.paths import STUB_MODULES_DIR

_LOADER_PARAMS = STUB_MODULES_DIR / "loader_params.py"


def _assert_param_module(m):
    assert m.label == "hi"
    assert m.n == 7
    assert m.x == 2.5
    assert m.active is True


def test_load_module_params_coercion_and_context():
    ctx = Context()
    params = {"label": "hi", "n": "7", "x": "2.5", "active": "yes"}
    modules = load_module(str(_LOADER_PARAMS), params=params, context=ctx)

    for name in ("ParamTemplar", "ParamDecree"):
        m = modules[name]
        _assert_param_module(m)
        assert m.context is ctx
