%plotting probability of a blockface being full with varying lambda, with 5 spaces, 1/5
%service rate on a 4-regular graph

k = 5;
mu = 1/5;
d = 4;

A = zeros(1,4);
initVal = 1.0;
endVal = 5.0;
diff = abs(endVal - initVal);
res = 100;
inc = diff / res;

for jj = 1:100
    denom = initVal + (jj * inc);
    la = 1.0/denom;
    A(jj,1) = la;
    x = singlenoderejratemu(la, mu, k, d);
    A(jj,2) = x;
    y = la + d*x;
    A(jj,3) = y;
    A(jj,4) = (y - la)/y;
end

plot(A(:,1),A(:,4))
title('Model solution: 5 servers, 1/5 service rate, 4-regular graph')
xlabel('Arrival rate')
ylabel('Probability of being full')