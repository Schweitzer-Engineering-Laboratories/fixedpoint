% Fixed point rounding stimulus generator, keeping msbs
% Copyright 2020, Schweitzer Engineering Laboratories, Inc
% SEL Confidential

% Random seed
rng(str2num(getenv('FIXEDPOINTRANDOMSEED')));

% Number of stimulus items to generate
NUM_ITERATIONS = str2num(getenv('FIXEDPOINTNUMITERATIONS'));

f = fopen('test_keep_msbs.stim', 'w');
f2 = fopen('test_keep_msbs.txt.', 'w');

tosign = @(x) 1 - 2*x;

rmethods = {'Nearest', 'Ceiling', 'Convergent', 'Zero', 'Floor', 'Round'};
oactions = {'Saturate', 'Wrap'};
RoundingMethod = @() rmethods{randi([1,6])};
OverflowAction = @() oactions{randi([1,2])};

Lmax = 254; % 256-length string with 0b prefix
for it = 1 : NUM_ITERATIONS

    binstr = repmat('0', 1, Lmax);
    [s, m, n, L] = deal(0);
    while L < 4
        s = randi([0, 1]);
        n = randi([2, Lmax-1]);
        m = randi([1, Lmax-n]);
        L = m + n;
    end
    array = int2str(randi([0, 1], 1, L));
    binstr(end - L + 1:end) = array(array ~= ' ');
    
    % Length of result
    LL = randi([2, L-1]);

    % Generate fixed point numbers. Products and sums always have
    % full precision. Set overflow to wrap for unsigned subtraction
    % where subtrahend > minuend.
    rmethod = RoundingMethod();
    omethod = OverflowAction();
    x = fi(0, s, L, L-LL, ...
        'RoundingMethod', rmethod, ...
        'OverflowAction', omethod ...
    );
    x.bin = binstr;
    
    switch rmethod
        case 'Nearest'
            z = nearest(x);
        case 'Ceiling'
            z = ceil(x);
        case 'Convergent'
            z = convergent(x);
        case 'Zero'
            z = fix(x);
        case 'Floor'
            z = floor(x);
        case 'Round'
            z = round(x);
        otherwise
            assert(0);
    end
    
    % From the 'doc round': 
    %   When the fraction length of a is positive, the fraction length of
    %   y is 0, its sign is the same as that of a, and its word length is 
    %   the difference between the word length and the fraction length of 
    %   a, plus one bit. If a is signed, then the minimum word length of y 
    %   is 2. If a is unsigned, then the minimum word length of y is 1.
    % Thus, this will set the word length of the result to the inteded
    % size.
    z = fi(z, s, LL, 0);
    
    
    % Write stimulus and expected output to file.
    fwrite(f, ['0b' binstr], 'char');
    fwrite(f, L * tosign(s), 'int32');
    fwrite(f, LL, 'uint32');
    fwrite(f, pad(rmethod, 16, 'right', char(0)), 'char');
    fwrite(f, pad(omethod, 16, 'right', char(0)), 'char');
    fwrite(f, pad(z.hex, 64, 'left', '0'), 'char');
    fprintf(f2, '% 256s %d %-3d %-3d %-8s %-10s % 256s\n', ...
        x.bin, s, L, LL, omethod, rmethod, z.bin);
end

fclose('all');

