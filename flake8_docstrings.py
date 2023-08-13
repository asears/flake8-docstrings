"""Implementation of pydocstyle integration with Flake8.

The pydocstyle docstring convention requires an error code and a class parser to be
included as a module in flake8. This integration allows flake8 to check for compliance
with the specified docstring convention.

This module contains several classes and methods to integrate pydocstyle with Flake8.

The module starts by importing necessary libraries and setting up some variables. It then
defines several classes, including `_ContainsAll`, `EnvironError`, `AllError`, and `pep257Checker`.

The `_ContainsAll` class is a simple class that always returns True for any `__contains__` check.

The `EnvironError` and `AllError` classes are custom error classes that inherit from `pep257.Error`.
They override the `line` property to return 0, and provide custom error messages.

The `pep257Checker` class is the main class of this module. It is responsible for checking a Python
file against the specified docstring convention. It has several methods to initialize the checker,
add and parse options, and run the check.

The `add_options` method adds plugin configuration options to flake8. The `parse_options` method
parses these options. The `_call_check_source` and `_check_source` methods are helper methods for
the `run` method, which uses the `check()` API from pydocstyle to perform the check.

The module ends with some error handling and message formatting.
"""
import re

supports_ignore_inline_noqa = False
supports_property_decorators = False
supports_ignore_self_only_init = False
try:
    # Here we are trying to import the pydocstyle module as pep257.
    # If the import is successful, we set the module_name to "pydocstyle" and parse the version number.
    # We also set several support flags based on the version number.
    # For example, if the version is 6.0.0 or higher, we set supports_ignore_inline_noqa to True.
    # If the import fails, we fall back to importing pep257 and set the module_name to "pep257".

    import pydocstyle as pep257

    module_name = "pydocstyle"

    pydocstyle_version = tuple(int(num) for num in pep257.__version__.split("."))
    supports_ignore_inline_noqa = pydocstyle_version >= (6, 0, 0)
    supports_property_decorators = pydocstyle_version >= (6, 2, 0)
    supports_ignore_self_only_init = pydocstyle_version >= (6, 3, 0)
except ImportError:
    import pep257

    module_name = "pep257"

__version__ = "1.7.0"
__all__ = ("pep257Checker",)


class _ContainsAll:
    """A class that always returns True for any `__contains__` check."""

    def __contains__(self, code: str) -> bool:
        return True


class EnvironError(pep257.Error):
    """Custom error class for environment errors.

    This class inherits from pep257.Error and overrides the line property to return 0.
    It provides a custom error message that includes the original environment error.
    """

    def __init__(self, err):
        super().__init__(
            code="D998",
            short_desc="EnvironmentError: " + str(err),
            context=None,
        )

    @property
    def line(self):
        """Return 0 as line number for EnvironmentError."""
        return 0


class AllError(pep257.Error):
    """Custom error class for all errors.

    This class inherits from pep257.Error and overrides the line property to return 0.
    It provides a custom error message that includes the original error.
    """

    def __init__(self, err):
        super().__init__(
            code="D999",
            short_desc=str(err).partition("\n")[0],
            context=None,
        )

    @property
    def line(self):
        """pep257.AllError does not contain line number. Return 0 instead."""
        return 0


class pep257Checker:
    """Flake8 needs a class to check python file."""

    name = "flake8-docstrings"
    version = f"{__version__}, {module_name}: {pep257.__version__}"

    def __init__(self, tree, filename, lines):
        """Initialize the checker."""
        self.tree = tree
        self.filename = filename
        self.checker = pep257.ConventionChecker()
        self.source = "".join(lines)

    @classmethod
    def add_options(cls, parser):
        """Add plugin configuration option to flake8."""
        parser.add_option(
            "--docstring-convention",
            action="store",
            parse_from_config=True,
            default="pep257",
            choices=sorted(pep257.conventions) + ["all"],
            help=(
                "pydocstyle docstring convention, default 'pep257'. "
                "Use the special value 'all' to enable all codes (note: "
                "some codes are conflicting so you'll need to then exclude "
                "those)."
            ),
        )
        parser.add_option(
            "--ignore-decorators",
            action="store",
            parse_from_config=True,
            default=None,
            help=(
                "pydocstyle ignore-decorators regular expression, "
                "default None. "
                "Ignore any functions or methods that are decorated by "
                "a function with a name fitting this regular expression. "
                "The default is not ignore any decorated functions. "
            ),
        )

        if supports_property_decorators:
            from pydocstyle.config import ConfigurationParser

            default_property_decorators = (
                ConfigurationParser.DEFAULT_PROPERTY_DECORATORS
            )
            parser.add_option(
                "--property-decorators",
                action="store",
                parse_from_config=True,
                default=default_property_decorators,
                help=(
                    "consider any method decorated with one of these "
                    "decorators as a property, and consequently allow "
                    "a docstring which is not in imperative mood; default "
                    f"is --property-decorators='{default_property_decorators}'"
                ),
            )

        if supports_ignore_self_only_init:
            parser.add_option(
                "--ignore-self-only-init",
                action="store_true",
                parse_from_config=True,
                help="ignore __init__ methods which only have a self param.",
            )

    @classmethod
    def parse_options(cls, options):
        """Parse the configuration options given to flake8.

        This method parses the configuration options given to flake8 and sets the class variables accordingly.

        Args:
            options (OptionManager): The configuration options given to flake8.
        """
        cls.convention = options.docstring_convention
        cls.ignore_decorators = (
            re.compile(options.ignore_decorators) if options.ignore_decorators else None
        )
        if supports_property_decorators:
            cls.property_decorators = options.property_decorators
        if supports_ignore_self_only_init:
            cls.ignore_self_only_init = options.ignore_self_only_init

    def _call_check_source(self):
        check_source_kwargs = {}
        if supports_ignore_inline_noqa:
            check_source_kwargs["ignore_inline_noqa"] = True
        if supports_property_decorators:
            check_source_kwargs["property_decorators"] = (
                set(self.property_decorators.split(","))
                if self.property_decorators
                else None
            )
        if supports_ignore_self_only_init:
            check_source_kwargs["ignore_self_only_init"] = self.ignore_self_only_init

        ignore_decorators = None
        if hasattr(self, "ignore_decorators"):
            ignore_decorators = self.ignore_decorators
        return self.checker.check_source(
            self.source,
            self.filename,
            ignore_decorators=ignore_decorators,
            **check_source_kwargs,
        )

    def _check_source(self):
        try:
            for err in self._call_check_source():
                yield err
        except pep257.AllError as err:
            yield AllError(err)
        except OSError as err:
            yield EnvironError(err)

    def run(self):
        """Use directly check() api from pydocstyle."""
        if hasattr(self, "convention"):
            if self.convention == "all":
                checked_codes = _ContainsAll()
            else:
                checked_codes = pep257.conventions[self.convention] | {
                    "D998",
                    "D999",
                }
        else:
            checked_codes = {
                "D998",
                "D999",
            }
        for error in self._check_source():
            if isinstance(error, pep257.Error) and error.code in checked_codes:
                # NOTE(sigmavirus24): Fixes GitLab#3
                message = f"{error.code} {error.short_desc}"
                yield (error.line, 0, message, type(self))
