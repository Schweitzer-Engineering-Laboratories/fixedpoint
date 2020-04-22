function test_rounding(scheme, stimfile, iterations)
% Floating point rounding stimulus generator
% Copyright 2020, Schweitzer Engineering Laboratories, Inc
% SEL Confidential

f = fopen([stimfile, '.stim'], 'w');
% fascii = fopen([stimfile, '.text'], 'w');

for it = 1 : iterations

    a = 1; b = 0;
    while a >= b
        % Random bit sizes
        s = randi([0, 1]);
        n = randi([0, 50]);
        m = randi([~n || s, 51 - n]);

        % Bounds of randomly generated number. Do not allow overflow after round.
        b = 2^(m-s) - 2;
        a = -s * (b + 1) + 1;
    end

    % Random number: https://www.mathworks.com/help/matlab/math/floating-point-numbers-within-specific-range.html
    value = (b - a) * rand + a;

    % Create stimulus
    fixedpoint = fi(value, s, m + n, n, 'RoundingMethod', scheme);

    % Write stimulus and expected output to file.
    fwrite(f, value, 'double');
    fwrite(f, s, 'uchar');
    fwrite(f, m, 'uchar');
    fwrite(f, n, 'uchar');
    fwrite(f, zeros(1, 5), 'char'); % Padding for byte alignment
    fwrite(f, pad(fixedpoint.hex, 16), 'char');
    fwrite(f, fixedpoint.double, 'double');
    % fprintf(fascii, '%.52f %d %d %d %s %.52f\n', ...
    %     value, s, m, n, fixedpoint.hex, fixedpoint.double)
end

fclose('all');

