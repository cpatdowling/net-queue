function [ pi_out ] = stationarydist(y, mu, k)
    %returns the stationary disitrubiton of a queue under rejection in a
    %d-regular network with effective arrival y, service rate mu, and k
    %servers
    pi = zeros(k+1,1);
    denom = 0.0;
    for i = 0:k
        denom = denom + (y/mu)^(i)/factorial(i);
    end
    for j = 0:k
        coeff = (y/mu)^(j)/factorial(j);
        pi((j+1),1) = coeff;
    end
    pi_out = (1.0/denom) * pi;
end