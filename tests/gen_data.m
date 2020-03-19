% Loop through subfolders and run MATLAB scripts, generating documentation

if ~getenv('FIXEDPOINTNUMITERATIONS')
    numits = input('Number of iterations? ', 's');
    setenv('FIXEDPOINTNUMITERATIONS', numits);
end
fprintf(1, 'NUM_ITERATIONS: %s\n', getenv('FIXEDPOINTNUMITERATIONS'));

nrand = str2num(getenv('FIXEDPOINTRANDOMSEED'));
if isempty(nrand)
    nrand = randi([0 2^30]);
    setenv('FIXEDPOINTRANDOMSEED', num2str(nrand));
end

D = dir;
D = D(3:end);
home = D(1).folder;
for d = 3 : length(D)
    directory = D(d);
    if directory.isdir
        cd(directory.name);
        mfiles = dir('*.m');
        for m = 1 : length(mfiles)
            mfile = mfiles(m);
            setenv('FIXEDPOINTRANDOMSEED', num2str(randi([0, 2^30])));
            fprintf(1, '%s random seed: %s\n', mfile.name, getenv('FIXEDPOINTRANDOMSEED'));
            fprintf(1, 'Evaluating %s\\%s...\n', mfile.folder, mfile.name);
            try
                eval(mfile.name(1:end-2));
            catch ME
                % Ignore 'not enough arguments'; we don't want to call
                % functions.
                if ~strcmp(ME.identifier, 'MATLAB:minrhs')
                    rethrow(ME);
                end
            end
        end
        cd(home);
    end
end
