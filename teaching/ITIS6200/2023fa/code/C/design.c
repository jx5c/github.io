#include <stdio.h>
#include <stdlib.h> 

void bar(int a, int b){
    int age; 
    char name [12];
    printf("What is your name?\n");
    gets (name);
    printf("%s\n", name);
}

void foo(){
    bar(1,2);
}

int main() {
    foo();
    return 0;
}
