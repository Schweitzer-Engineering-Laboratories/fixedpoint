% Fixed point bit resize stimulus generator
% Copyright 2020, Schweitzer Engineering Laboratories, Inc
% SEL Confidential

% Random seed
rng(str2num(getenv('FIXEDPOINTRANDOMSEED')));

% Number of stimulus items to generate
NUM_ITERATIONS = str2num(getenv('FIXEDPOINTNUMITERATIONS'));

f = fopen('test_resize.stim', 'w');

rmethods = {'Nearest', 'Ceiling', 'Convergent', 'Zero', 'Floor', 'Round'};
oactions = {'Saturate', 'Wrap'};
RoundingMethod = @() rmethods{randi([1,6])};
OverflowAction = @() oactions{randi([1,2])};

Lmax = 254; % 256-length string with 0b prefix
for it = 1 : NUM_ITERATIONS

    binstr = repmat('0', 1, Lmax);
    [s, m, n, L] = deal(0);
    while L <= 2
        s = randi([0, 1]);
        m = randi([2, Lmax-2]);
        n = randi([2, Lmax-m]);
        L = m + n;
    end
    array = int2str(randi([0, 1], 1, L));
    binstr(end - L + 1:end) = array(array ~= ' ');

    % Generate fixed point numbers.
    x = fi(0, s, L, n);
    x.bin = binstr;

    % Write stimulus and expected output to file.
    fwrite(f, ['0b' binstr], 'char');
    fwrite(f, s, 'uint32');
    fwrite(f, m, 'uint32');
    fwrite(f, n, 'uint32');
    fwrite(f, 0, 'uint32');

    for it = 1 : 4 %#ok<*FXSET>
        % Iteration 1: shrink both integer and fractional. New rounding/overflow
        % Iteration 2: shrink only fractional. New rounding
        % Iteration 3: shrink only integer. New overflow
        % Iteration 4:
        if it == 2
            nint = m;
        else
            nint = randi([s == 1, m - 1]);
            oaction = OverflowAction();
        end
        if it == 3
            nfrac = n;
        else
            nfrac = randi([min(n-1, max(2-nint, 0)), n-1]);
            rmethod = RoundingMethod();
        end

        % Create a new value from the original x
        z = fi(x, s, nint + nfrac, nfrac, ...
            'OverflowAction', oaction, ...
            'RoundingMethod', rmethod ...
        );

        % Write to file
        fwrite(f, pad(rmethod, 16, 'right', char(0)), 'char');
        fwrite(f, pad(oaction, 16, 'right', char(0)), 'char');
        fwrite(f, nint, 'uint64');
        fwrite(f, nfrac, 'uint64');
        fwrite(f, pad(z.hex, 64, 'left', '0'), 'char');
    end
end

fclose('all');
