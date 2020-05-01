# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog][], and this project adheres to
[Semantic Versioning][] and [PEP 440][].

## 1.0.1

* Added changelog.
* Added py.typed into release files per [PEP 561][] so
  [mypy](https://mypy.readthedocs.io/en/stable/installed_packages.html#making-pep-561-compatible-packages)
  will recognize fixedpoint as a typed package.
    * Added py.typed into [fixedpoint](/fixedpoint/) directory
    * Added py.typed as package_data in [setup.cfg](/setup.cfg).

## 1.0.0

* Initial release.

[Keep a Changelog]: https://keepachangelog.com/en/1.0.0/
[Semantic Versioning]: https://semver.org/spec/v2.0.0.html
[PEP 440]: https://www.python.org/dev/peps/pep-0440/
[PEP 561]: https://www.python.org/dev/peps/pep-0561/
