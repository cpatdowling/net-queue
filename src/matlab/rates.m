%2 node example solution

function res=rates(Z)
para=textread('rates_para.txt','%f');
la1=para(1); la2=para(2);  mu1=para(3); mu2=para(4);
x=Z(1);
y=Z(2);
p=Z(3:6);
Q=[-(la1+la2+x+y) la1+x la2+y 0; 
    mu1 -(mu1+la2+y) 0 la2+y; 
    mu2 0 -(mu2+la1+x) la1+x; 
    0 mu1 mu2 -(mu1+mu2)];
res=zeros(7,1);
res(1)= ones(1,4)*p-1;
res(2)=x-(p(3)+p(4))*(la2+y);
res(3)=y-(p(2)+p(4))*(la1+x);
res(4:7)=Q'*p;
end