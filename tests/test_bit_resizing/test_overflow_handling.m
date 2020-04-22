function test_overflow_handling(OverflowAction, stimfile, iterations)
% Fixed point overflow handling stimulus generator
% Copyright 2020, Schweitzer Engineering Laboratories, Inc
% SEL Confidential

f = fopen([stimfile '.stim'], 'w');
f2 = fopen([stimfile '.txt'], 'w');

Lmax = 254; % 256-length string with 0b prefix
for it = 1 : iterations

    binstr = repmat('0', 1, Lmax);
    L = randi([3, Lmax]);
    s = randi([0, 1]);
    array = int2str(randi([0, 1], 1, L));
    binstr(end - L + 1:end) = array(array ~= ' ');

    % Length of result
    LL = randi([2, L-1]);

    % Write stimulus and expected output to file.
    fwrite(f, ['0b' binstr], 'char');
    fwrite(f, s, 'uint32');
    fwrite(f, L, 'uint32');
    fwrite(f, LL, 'uint32');
    fprintf(f2, '% 256s %d %-3d %-3d', binstr, s, L, LL);

    for it = 1 : length(OverflowAction) %#ok<*FXSET>
        x = fi(0, s, L, 0, 'OverflowAction', OverflowAction{it});
        x.bin = binstr;
        % Reduce integer bits
        z = fi(x, s, LL, 0);

        % Indicate if overflow has occurred; i.e., if the result doesn't match
        % the initial value.
        if it == 1
            fwrite(f, x ~= z, 'uint32');
        end
        fwrite(f, pad(z.hex, 64, 'left', '0'), 'char');
        fprintf(f2, ' % 256s', z.bin);
    end
    fprintf(f2, '\n');
end

fclose('all');

