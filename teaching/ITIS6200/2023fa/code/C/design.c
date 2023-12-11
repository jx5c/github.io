#include <stdio.h>
#include <stdlib.h> 

void bar(int a){
    char name [20];
    printf("What is your name?\n");
    gets (name);
    printf("%s\n", name);
}

void foo(int a){
    bar(1);
}

int main() {
    foo(2);
    return 0;
}
