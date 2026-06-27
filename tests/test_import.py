import worldsim

def test_version_exists():
    assert hasattr(worldsim, '__version__')