/*
clang -Xclang -ast-dump -fsyntax-only example.c
 */
#include <stdbool.h>

CPlot plot;

int main() {

    int a = 3 + 19;
    double foo, bar, foobar = a, test = 9;
    foo = foo + 1;

    bar = ((1==3) && (3>=5));
    while(!(-4 < 1+0)) {
        plot.line(sqrt(cbrt(abs(-2))), 4+5, 5-2, 4*5/9-5*9);
        for (int hamburger = foo + bar + 4; hamburger > bar * 83; hamburger -= sqrt(test)) {
            plot.quad(4, 4-5, 5*2, 4+5-9*5/9, foo + 2, sqrt(5), cbrt(12)/4+5, foo / (bar + foobar) - test);
        }
        if (2+2 == 5) {
            foo = 300;
        } else if (foo == 300) {
            foo = 50;
        } else {
            foo = 200;
        }
    }
    int h = 0xE5;
    int b = 0b110001001;
    int H = 0X93;
    int B = 0b101;
    int o = 012;
    int O = 0;
    int i = 200;
}

/*
abs(-2);

sqrt(9);

sin(1.57);

deg2rad(45);

0 % 2 == 0;

round(3.1);

round(0*pow(10, 2))/pow(10, 2);

constrain(5, 1, 10);

randint(1, 100);

randdouble(1, 100);

urand(NULL);

randfrac(x, 10);

pow(2, 3);

mean(var);

sort(var2, var);

divisornum(12);

gcd(6, 12);

permutation(4, 2);

distance(0, 0, 6, 6);

midpoint(0, 0, 6, 6, x, y);

linearfit(x, y, m, b);

linearcorrcoef(x, y);

linsolvesi(2, 4, -0.5, -2, x, y);
quartiles(a, min, q1, med, q3, max, range, iqr);
quadratic(1, -5, 6, x1, x2);

polygonperi(x, y);

triangleSSS(4, 5, 30, 8, 7, 5, x2, y2, x3, y3);
perpendicularLinesi(-2, 3, 2, -4, x, y);
*/