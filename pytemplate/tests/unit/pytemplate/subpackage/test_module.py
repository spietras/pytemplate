"""

Notice that unit tests follow the package structure.
That's a nice way to organize test modules.

There are many ways to organize tests inside a module.
One test class per method is OK.

"""

from pytemplate.subpackage.module import identity


# class per method is ok
class TestIdentity:

    # notice the use of asserts - that's the pytest way
    def test_identity_returns_same_input_value_equality(self):
        assert 1 == identity(1)

    def test_identity_returns_same_input_reference_equality(self):
        x = "test"
        assert x is identity(x)
