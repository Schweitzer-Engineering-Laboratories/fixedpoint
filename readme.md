# Fixed Point Python Package

The fixedpoint package is a fixed point arithmetic library for python, released
under the [BSD license](LICENSE).

Install fixedpoint with `pip install fixedpoint`.

Package documentation can be found at [readthedocs](https://fixedpoint.readthedocs.io/), or
build your own local documentation:

1. From the root directory, run `pip install .[docs]` (setup.cfg tells pip
   all the necessary dependencies).
2. From the `./docs` directory, run `make html` (tells sphinx to build
   the documentation in html format).
3. View the documentation at `./docs/build/html/index.html`.

## Versioning API

The only direct compatibility between
[Semantic Versioning](https://semver.org/spec/v2.0.0.html) (SemVer) and
[PEP 440](https://www.python.org/dev/peps/pep-0440/) (Python's recommended
approach to identifying versions, supported by PyPI) is a MAJOR.MINOR.PATCH
scheme. However, through trial and error, the SemVer pre-release syntax
`X.Y.Z-aN` is accepted by PyPI (indeed, PEP 440
[Appendix B](https://www.python.org/dev/peps/pep-0440/#appendix-b-parsing-version-strings-with-regular-expressions)
includes a regex as defined by the [packaging](https://github.com/pypa/packaging/tree/master/packaging)
project). That is, the PEP 440-compatible `X.Y.ZaN` syntax can be converted to
the SemVer-compatible `X.Y.Z-aN` syntax (note the extra dash) without penalty,
and PyPI will still recognize the version. To that end, the following
versioning identification is used:

**MAJOR**.**MINOR**.**PATCH**\[**-**{**a**|**b**|**rc**}**N**\]\[**+META**\]

* **MAJOR**, **MINOR**, and **PATCH** comply with
  [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html#semantic-versioning-specification-semver)
  and are required for *every* release.
* Pre-releases are optional. If included, it is specified immediately after
  the PATCH version. A pre-release is prefixed with a `-`, identified as
  one of the following types, and suffixed with a non-negative version number
  **N**:
    * *alpha* (**a**), indicating content unverified through test. There is no
      commitment that this will escalate to a beta release, release candidate,
      or final release.
    * *beta* (**b**), indicating that code is complete and testing is underway.
    * *release candidate* (**rc**), indicating that code and testing is complete
      and final preparations are being made for release.
* Meta data or build data (**META**) is optional. If included, it is specified
  immediately after the pre-release identifier (if present) or the PATCH version
  (if no pre-release is specified). Meta data is prefixed with a `+` and
  complies with both
  [PEP 440](https://www.python.org/dev/peps/pep-0440/#local-version-identifiers)
  and [SymVer 2.0.0](https://semver.org/spec/v2.0.0.html#spec-item-10).

Post- and development-releases are not supported. Instead, increment the
appropriate MAJOR, MINOR, or PATCH version with an alpha release.

## FixedPoint Development and Testing

The `./tests` folder contains the infrastructure for testing this library.

The source code and tests are intended for Python 3.8. Both code and tests are
organized into the following sections:

* Initialization methods
* Property accessors and mutators
* Operators
    * Arithmetic operators
    * Unary operators
    * Comparisons
* Context management
* Built-in functions and type conversion
* Bit resizing
    * Rounding
    * Overflow handling
* Alerts and error handling
* Functions
* Property resolution

The test modules are titled the more or less the same way the code sections are.
There is some overlap between tests, but organizing it in such a way guarantees
that the functionality is tested in the intended manner.

### Running Tests

The following modules are required for testing

* nose (main test runner)
* coverage (measures code coverage)
* mypy (verifies typing)
* tqdm (progress bar)
* sphinx (doctests for documentation)

Run `py ./setup.py nosetests` from the root directory, which installs all
necessary testing dependencies (except MATLAB), and then runs the entire suite
of tests.

If you already have all the test dependencies, you can run `./test.bat` in the
root directory to run the entire test suite. `./setup.cfg` has options that are
used to run nose tests, but you can also supplement `./test.bat` with other
[nose options](https://nose.readthedocs.io/en/latest/usage.html#options).

The coverage report can be found at `./tests/COVERAGE/index.html` after the
tests are run.

#### Common `test.bat` Options

To run individual tests, the syntax is
`./test.bat tests/<test_folder_name>:test_function_name`. For example, to run
the `test_resize` function from `./tests/test_bit_resizing/__init__.py`, the
command would be `./test.bat ./tests/test_bit_resizing:test_resize`.

Alternatively, when tests are run, nose will number them on the printout. Once
they're numbered (which is recorded in `./tests/.noseids`), you can simply
run `./test.bat <test_number>`. To make nose simply number (but not execute)
tests, run `./test.bat --collect-only`.

Run only previously failed tests with `./test.bat --failed`.

#### MATLAB Stimulus

MATLAB is used to generate stimulus for some tests. Versions __R2018a__ and
__R2019a__ were used during development; no other versions are guaranteed to
work.

`./tests/tools.py` includes a MATLAB class that is used to generate MATLAB
stimulus. It requires that MATLAB be in your system path. If this is not the
case, those tests will be skipped. It does not account for unavailability of
licenses.

The `tools.MATLAB` class will not regenerate stimulus if it already exists. You
can either delete the stimulus file to force regeneration, call the script
itself, or call `./tests/gen_data.m` from MATLAB, which loops through all test
directories and generates all data at once. Stimulus generated by MATLAB are
binary files and have a `.stim` extension.

## Deployment Checklist

* Make sure unit tests pass and coverage is sufficient.
* Update copyright dates.
* Update version in `./fixedpoint/__init__.py` per the
  [Versioning API](#versioning-api) with the help of
  [regex101](https://regex101.com/r/Ly7O1x/322).
* Update `./setup.cfg`; specifically:
    * [Classifiers](https://pypi.org/classifiers/), specifically:
        * Development Status
        * Programming Language
    * python_requires
    * tests_requires
    * setup_requires
    * extras_require
    * nosetests
* Make sure documentation builds and is up to date
* Create/update the changelog and add
  [versionadded](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-versionadded),
  [versionchanged](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-versionchanged),
  [deprecated](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-versionchanged), or
  [seealso](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-seealso)
  directives in the documentation where appropriate.
* Create a wheel: `py setup.py dist`
* Deploy to PyPI:
  `py -m twine upload --repository-url https://upload.pypi.org/legacy/ dist/*`
    * Populate your `%HOMEPATH%\\.pypirc` as described
      [here](https://docs.python.org/3.3/distutils/packageindex.html#pypirc)
      and you can instead use `py -m twine upload <REPO> dist/*` with `<REPO>`
      being one of the index-servers.
