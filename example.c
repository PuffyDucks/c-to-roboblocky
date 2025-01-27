/*
 * clang -Xclang -ast-dump -fsyntax-only example.c
 */
#include <stdbool.h>

CPlot plot;

int main() {

    int a = 3;
    int foo, bar, foobar = a, test = 9;
    int b = 3 + 3;
    foo = foo + 1;
    plot.line(foo, 0, 4, 9);

    bar = ((1==3) && (3>=5));
    while(!(-4 < 1+0)) {
        plot.line(2, 4+5, 5-2, 4*5/9-5*9);
        while(4 < 1+0) {
            plot.line(2, 4+5, 5-2, 4*5/9-5*9);
            plot.line(4, 4-5, 5*2, 4+5-9*5/9);
        }
        plot.line(4, 4-5, 5*2, 4+5-9*5/9);
    }
}

