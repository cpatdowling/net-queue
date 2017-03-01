function [ res ] = probfullpolymu(xit, la, mu, k, d)
    %probfull polynomial calculation with respect to
    %rejection rate
    yrn = @(x) la + d*x; %effective arrival rate
    
    polysum = 0;
    for i=0:k
        coeff = (((k-i)/mu^(k-i-1))-(la/mu^(k-i)))/factorial(k-i);
        y = yrn(xit)^(k-i);
        polysum = polysum + coeff*y;
    end
    res = polysum;
end