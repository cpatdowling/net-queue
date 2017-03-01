function [ B ] = poparrivalarray(mu, k, d )
    %This function populates a look-up table, where given a range of
    %arrival rates
    %lambda, degree, number of servers, and service rate, the occupancy
    %level and probability of being full are calculated
    las = fliplr(0.1:0.1:200);
    A = zeros(length(las),5);
    kk = 1;
    occup = 0.0;
    while occup < 1.0
        if kk == length(las)
            break
        end
        la = 1/las(kk);
        x = singlenoderejratemu(la, mu, k, d);
        y = la + d*x;
        stat = stationarydist(y, mu, k);
        occup = (stat' * (0:1:k)')/k;
        if occup > 0.99
           break
        end
        A(kk,1) = la; %ex. arrival rate
        A(kk,2) = x; %rejection rate
        A(kk,3) = y; %total arrival
        A(kk,4) = (y - la)/y; %pi_k
        A(kk,5) = occup; %expected value
        kk = kk + 1;
    end
    B = A(1:kk-1,:);
end

