clear all; clc;
typesim = 'blockface'; %network or blockface

typeserv = 'fixservice'; %fixservice or vary service

modeldatapath = '/home/chase/projects/net-queue-full/data/simulation/belltownsims/belltowndata/belltownmodeldata/';
parampath = '/home/chase/projects/net-queue-full/data/simulation/belltownsims/';
days = {'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'};
%days = {'Saturday'};

for n = 1:numel(days)
    day = days{1,n};
    %network or individual blockface occupancy data
    occupdata = csvread(strcat(modeldatapath,day,'_',typesim,'_Average_Loads_Matlab.csv'));
    supplydata = csvread(strcat(modeldatapath,'belltown-supply-array.txt'));
    degdata = csvread(strcat(modeldatapath,'belltown-outdegree-array.txt'));
    servicedata = csvread(strcat(modeldatapath,'belltown-service-minutes-array.txt'));
    if typeserv == 'fixservice'
        servicedata = 105.0 * eye(256);
    end
    effarrivals = zeros(size(256,12));
    truearrivals = zeros(size(256,12));
    rejections = zeros(size(256,12));
    
    dims = size(occupdata);
    for row = 1:dims(1,1)
        disp(row)
        for hour = 1:dims(1,2)
            if degdata(row,row) == 0
                degdata(row,row) = 1;
            end
            B = poparrivalarray(1/servicedata(row,row), supplydata(row,row), degdata(row,row));
            maxArow = size(B);
            jj = 1;
            while B(jj,5) < occupdata(row,hour) %switch inequality when switching directions
                jj = jj + 1;
                if jj == maxArow(1,1)
                    break
                end
            end
            if strcmp(typesim,'network') %matlab equality test for strings
                %for networkwork wide arrival estimates
                for rowi = 1:256
                    truearrivals(rowi,hour) = 1.0/B(jj,1);
                    effarrivals(rowi,hour) = 1.0/B(jj,3);
                end
            else
                truearrivals(row,hour) = 1.0/B(jj,1);
                effarrivals(row,hour) = 1.0/B(jj,3);
                rejections(row,hour) = 1.0/B(jj,2);
            end
        end
    end
    outdir = strcat('local_uniformity_',typeserv);
    mkdir(modeldatapath,outdir);
    csvwrite(strcat(modeldatapath,outdir,'/',day,'_',typesim,'_True_Arrivals_By_Block.csv'), truearrivals); %true is just lambda
    csvwrite(strcat(modeldatapath,outdir,'/',day,'_',typesim,'_Effective_Arrivals_By_Block.csv'), effarrivals); %effective is lambda + d*x
    csvwrite(strcat(modeldatapath,outdir,'/',day,'_',typesim,'_Rejections_By_Block.csv'), rejections)
end

