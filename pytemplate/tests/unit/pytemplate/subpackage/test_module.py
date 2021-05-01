from pytemplate.subpackage.module import identity


class TestIdentity:
    def test_identity_returns_same_input_value_equality(self):
        assert 1 == identity(1)

    def test_identity_returns_same_input_reference_equality(self):
        x = "test"
        assert x is identity(x)
