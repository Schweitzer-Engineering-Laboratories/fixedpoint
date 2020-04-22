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
project that supports this format). That is, the PEP 440-compatible `X.Y.ZaN`
syntax can be converted to the SemVer-compatible `X.Y.Z-aN` syntax (note the
extra dash) without penalty, and PyPI will still recognize the version. To that
end, the following versioning identification is used:

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

### Installing test dependencies

`./setup.cfg` shows the test dependencies. There are two ways to install them
(except for MATLAB, which must be installed separately):

#### Install test dependencies locally

Run `python ./setup.py nosetests`, which will install the dependencies in the
`./.eggs` directory, and then execute the tests using the local dependencies.
Using this method means

* You don't have to muck up your library with packages you won't ever use again
* You must run all the tests; you can't pick one or just a few to run

This method is recommended for quick test verification.

#### Install test dependencies permanently

Run `pip install .[test_dependencies]` which will install all
test dependencies on your machine for use later. Using this method means

* You can run individual tests, a handful of tests, or all tests easily

This method is recommended if you need to dig in to tests in more detail.

### Running tests

The following commands will run all tests (commands are run from the root
directory):

* `python ./setup.py nosetests` (see description
  [above](#install-test-dependencies-locally))
* `test.bat`
* `python -m tests`

You can run a specific test with one of the following commands (run from the
root directory):

* `test.bat tests:test_subtraction` or `python -m tests tests:test_subtraction`
* `test.bat --collect-only`, followed by the test number to run like
  `test.bat 42`

Run multiple tests in the same way, placing a space between each test identifier
(like `tests:test_subtraction` or `42` in the examples above).

You can also append other
[nose options](https://nose.readthedocs.io/en/latest/usage.html#options) to
either `test.bat` or `python -m tests` (as shown in the `--collect-only`
example above)

Run only previously-failed tests with the `--failed` switch.

View the coverage report at `./tests/COVERAGE/index.html` after the tests run
note that the `cover-erase` option in `./setup.cfg` will erase all coverage data
between test invocations.

Each test generates a log in the directory it's located in for further analysis.

#### MATLAB Stimulus

MATLAB is used to generate stimulus for some tests. Versions __R2018a__ and
__R2019a__ were used during development; no other versions are guaranteed to
work.

`./tests/tools.py` includes a MATLAB class that is used to generate MATLAB
stimulus. It requires that MATLAB be in your system path. If this is not the
case, those tests will be skipped. It does not account for unavailability of
licenses, nor does it verify the version.

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
        * test_dependencies
        * docs
    * nosetests
* Make sure documentation builds and is up to date
* Create/update the changelog and add
  [versionadded](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-versionadded),
  [versionchanged](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-versionchanged),
  [deprecated](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-versionchanged), or
  [seealso](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-seealso)
  directives in the documentation where appropriate.
* Create a wheel: `py setup.py dist` (an alias for `bdist_wheel sdist`)
* Deploy to PyPI:
  `py -m twine upload --repository-url https://upload.pypi.org/legacy/ dist/*`
    * Populate your `%HOMEPATH%\\.pypirc` as described
      [here](https://docs.python.org/3.3/distutils/packageindex.html#pypirc)
      and you can instead use `py -m twine upload -r <REPO> dist/*` with
      `<REPO>` being one of the index-servers.
