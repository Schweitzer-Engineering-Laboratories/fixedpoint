% Fixed point multiplication stimulus generator
% Copyright 2020, Schweitzer Engineering Laboratories, Inc
% SEL Confidential

% Random seed
rng(str2num(getenv('FIXEDPOINTRANDOMSEED')));

% Number of stimulus items to generate
NUM_ITERATIONS = str2num(getenv('FIXEDPOINTNUMITERATIONS'));

% Call the generic stimulus generator
test_operators(@(a,b) a * b, 'test_multiplication', NUM_ITERATIONS);
