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
    plot.fillColor("#66ff99");    
    plot.backgroundColor("orange");
    plot.strokeColor(rgb2hex(0x2F, 0b00010001, 198));
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
