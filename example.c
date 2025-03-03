/*
clang -Xclang -ast-dump -fsyntax-only example.c
 */
#include <stdbool.h>
#define M_PI PI()
#define M_E  E()
#define Inf  INFINITY()

CPlot plot;

int isGreater(int a, int b) {
    if (a > b) {
        return 1;
    } else {
        return 0;
    }
}

int main() {
    int a = 2;
    double foo, bar, foobar = a, test = isGreater(2, 1);
    foo = foo + 1;
    foo *= pow(1.1003, 2);
    foo--;

    bar = ((1==012) && (M_PI>=0xE5));
    while(!(-4 < 1+0b101)) {
        plot.line(sqrt(cbrt(abs(-2))), 4+5, 5-2, 4*5/9-5*9);
        for (int idx = foo + bar + 4; idx > bar * 83; idx -= sqrt(test)) {
            plot.quad(4, 4-5, 5*2, 4+5-9*5/9, foo + 2, sqrt(5), cbrt(12)/4+5, foo / (bar + foobar) - idx);
        }
        for (int angle = 0; angle < 360; angle += 30) {
            plot.text("ABCD", "center", 5, 5, angle);
        }
        if (isGreater(abs(-3), 1)) {
            foo = 300;
        } else if (foo == 300) {
            foo = 50;
        } else {
            foo = 200;
        }
    }
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