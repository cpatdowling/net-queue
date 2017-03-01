function [ y ] = singlenoderejratemu( la, mu, k, d )
    %this function attempts to solve for the positive root of the
    %polynomial corresponding to the probability of a single queue 
    %in a queue network under rejection being full, and gives the 
    %value of the rejection rate
    x = 0.5*la;
    tol = 0.0001;
    up = 1000;
    polysum = up;
    
    low = 0;
    jj = 0;
    maxiter = 10000;
    while abs(polysum) > tol
        if jj > maxiter
            break
        end
        polysum = probfullpolymu(x, la, mu, k, d);
        if abs(polysum) < tol
            break
        elseif polysum < 0 %solution to right, positive derivative
            low = x;
            half = 0.5*(up - x);
            x = x + half;
        else %solution to left
            up = x;
            half = 0.5*(x - low); 
            x = x - half;
        end
        jj = jj + 1;
    end
    y = x;
end

