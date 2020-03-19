% Fixed point rounding stimulus generator
% Copyright 2020, Schweitzer Engineering Laboratories, Inc
% SEL Confidential

% Random seed
rng(str2num(getenv('FIXEDPOINTRANDOMSEED')));

% Number of stimulus items to generate
NUM_ITERATIONS = str2num(getenv('FIXEDPOINTNUMITERATIONS'));

% Call the generic stimulus generator
test_rounding(@(k) 'Ceiling', 'test_ceil', NUM_ITERATIONS, 1);
