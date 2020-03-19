@echo off

:: Add the directory above fixedpoint to the PYTHONPATH so imports can be
:: absolute and not relative
py -m nose ^
    --nologcapture ^
    --no-byte-compile ^
    --detailed-errors ^
    --with-coverage ^
    --cover-erase ^
    --cover-branches ^
    --cover-package=fixedpoint ^
    --cover-html ^
    --cover-html-dir=tests\COVERAGE ^
    --verbose ^
    --with-id ^
    --id-file=tests\.noseids ^
    %*
