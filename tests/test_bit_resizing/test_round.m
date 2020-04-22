% Fixed point rounding stimulus generator
% Copyright 2020, Schweitzer Engineering Laboratories, Inc
% SEL Confidential

% Random seed
rng(str2num(getenv('FIXEDPOINTRANDOMSEED')));

% Number of stimulus items to generate
NUM_ITERATIONS = str2num(getenv('FIXEDPOINTNUMITERATIONS'));

roundingmethods = {'Nearest', 'Ceiling', 'Convergent', 'Zero', 'Floor', 'Round'};

% Call the generic stimulus generator
test_rounding(@(k) roundingmethods{randi([1, 6])}, 'test_round', NUM_ITERATIONS);
