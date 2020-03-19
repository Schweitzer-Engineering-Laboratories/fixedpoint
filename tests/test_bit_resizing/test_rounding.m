function test_rounding(RoundingMethod, stimfile, iterations, roundto0)
% Fixed point rounding stimulus generator
% Copyright 2020, Schweitzer Engineering Laboratories, Inc
% SEL Confidential

f = fopen([stimfile, '.stim'], 'w');
% fascii = fopen([stimfile, '.txt'], 'w');
% fprintf(fascii, 'bin_term signed nint nfrac nfracs(x16) result(x16)\n');

% Support always rounding to 0 fractional bits
if nargin == 3
    roundto0 = 0;
end

Lmax = 254; % 256-length string with 0b prefix
for it = 1 : iterations

    binstr = repmat('0', 1, Lmax);
    [s, m, n, L] = deal(0);
    while L <= 2
        s = randi([0, 1]);
        m = randi([max(s == 1, roundto0 * 2), Lmax-1]);
        n = randi([min(1, max(2-m, 2)), Lmax-m]);
        L = m + n;
    end
    array = int2str(randi([0, 1], 1, L));
    binstr(end - L + 1:end) = array(array ~= ' ');

    % Generate fixed point numbers. Products and sums always have
    % full precision. Set overflow to wrap for unsigned subtraction
    % where subtrahend > minuend.
    rmethod = RoundingMethod(it);
    x = fi(0, s, L, n, ...
        'SumMode', 'SpecifyPrecision', ...
        'SumWordLength', L, ...
        'SumFractionLength', n, ...
        'RoundingMethod', rmethod ...
    );
    x.bin = binstr;
    y = fi(0, s, L, n, ...
        'SumMode', 'SpecifyPrecision', ...
        'SumWordLength', L, ...
        'SumFractionLength', n, ...
        'RoundingMethod', rmethod ...
    );

    % Write stimulus and expected output to file.
    fwrite(f, ['0b' binstr], 'char');
    fwrite(f, s, 'uint16');
    fwrite(f, m, 'uint16');
    fwrite(f, n, 'uint16');
    fwrite(f, pad(rmethod, 10, 'right', char(0)), 'char');

    nbits = randi([min(2, max(0, 2-m)), n-1], 1, 16) * ~double(roundto0);
    fwrite(f, nbits, 'uint8');

    for nfrac = nbits
        x.SumFractionLength = nfrac;
        x.SumWordLength = m + nfrac;
        y.SumFractionLength = nfrac;
        y.SumWordLength = m + nfrac;
        % Create a new value from the original x
        z = x + y;
        fwrite(f, pad(z.hex, 64, 'left', '0'), 'char');
        % fprintf(fascii, ['0x' pad(z.hex, 62, 'left', '0') '\n']);
    end
end

fclose('all');

