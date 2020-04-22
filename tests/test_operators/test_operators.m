function test_operators(func, stimfile, iterations)
% Floating point rounding stimulus generator
% Copyright 2020, Schweitzer Engineering Laboratories, Inc
% SEL Confidential

f = fopen([stimfile, '.stim'], 'w');
fascii = fopen([stimfile, '.txt'], 'w');
fprintf(fascii, [...
    'bin_term1 signed1 nint1 nfrac1 ' ...
    'bin_term2 signed2 nint2 nfrac2 ' ...
    'hex(func(term1, term2)) hex(func(term2, term1))\n']);

Lmax = 509; % 512-length string with 0b0 prefix
hexpad = 2 * ceil(Lmax / 4);
for it = 1 : iterations

    binstr = repmat('0', 2, Lmax);
    for k = 1 : 2
        s(k) = 0; m(k) = 0; n(k) = 0; L(k) = 0; %#ok<AGROW>
        while L(k) == 0
            s(k) = randi([0, 1]);
            m(k) = randi([s(k), Lmax]);
            n(k) = randi([m(k) == 0, Lmax-m(k)]);
            L(k) = m(k) + n(k);
        end
        array = int2str(randi([0, 1], 1, L(k)));
        binstr(k, Lmax - L(k) + 1:end) = array(array ~= ' ');
    end

        % Generate fixed point numbers. Products and sums always have
        % full precision. Set overflow to wrap for unsigned subraction
        % where subtrahend > minuend.
        a = fi(0, s(1), L(1), n(1), ...
            'ProductMode', 'FullPrecision', ...
            'SumMode', 'FullPrecision', ...
            'OverflowAction', 'Wrap' ...
        );
        b = fi(0, s(2), L(2), n(2), ...
            'ProductMode', 'FullPrecision', ...
            'SumMode', 'FullPrecision', ...
            'OverflowAction', 'Wrap' ...
        );
        a.bin = binstr(1,:);
        b.bin = binstr(2,:);

        % Do the thing
        x = func(a, b);
        y = func(b, a);

    % Write stimulus and expected output to file.
    fwrite(f, ['0b0' binstr(1,:)], 'char');
    fwrite(f, s(1), 'uint32');
    fwrite(f, m(1), 'uint32');
    fwrite(f, n(1), 'uint32');
    fwrite(f, 0, 'uint32'); % padding
    fwrite(f, ['0b0' binstr(2,:)], 'char');
    fwrite(f, s(2), 'uint32');
    fwrite(f, m(2), 'uint32');
    fwrite(f, n(2), 'uint32');
    fwrite(f, 0, 'uint32'); % padding
    fwrite(f, pad(x.hex, hexpad, 'left', '0'), 'char');
    fwrite(f, pad(y.hex, hexpad, 'left', '0'), 'char');
    fprintf(fascii, '0b0%s %d %3d %3d 0b0%s %d %3d %3d 0x%s 0x%s\n', ...
        pad(a.bin, Lmax, 'left', '0'), s(1), m(1), n(1), ...
        pad(b.bin, Lmax, 'left', '0'), s(2), m(2), n(2), ...
        pad(x.hex, hexpad, 'left', '0'), ...
        pad(y.hex, hexpad, 'left', '0'));
end

fclose('all');

