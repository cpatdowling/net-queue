
y = zeros(99,1);
x = zeros(25,1);
datatwoway = zeros(25,99);
dataoneway = zeros(25,99);

for i=1:25
    x(i,1) = i;
    for la = 0.01:0.01:0.99
        j = int64(la*100);
        y(j,1) = 2*la;
    end
end

for i=2:25
    for la=0.01:0.01:0.8
        j = int64(la*100);
        %datatwoway(i,j) = singlenoderejrate(i*la, 1, i, 3); %two way road
        dataoneway(i,j) = singlenoderejrate(i*la, 1, 2*i, 2); %twice as many servers available because blocks combine
    end
end


%plot(data(1,:), data(2:3,:))
%legend('one way', 'two way')
surf(y,x,datatwoway)
%hold on
%surf(dataoneway)
axis([0,2,2,25,0,2.0])
title('One-way street blockface queue rejection rates, unit service rate')
zlabel('rejection rate')
xlabel('external arrival rate')
ylabel('number of parking spaces (servers)')
view(225,45)
%hold off