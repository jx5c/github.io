#include <stdio.h>
#include <stdlib.h> 

void foo(int a, int b){
    int age; 
    char name [12];
    printf("What is your name?\n");
    gets (name);
    printf("%s\n", name);
}

int main() {
    foo(1,2);
    return 0;
}
