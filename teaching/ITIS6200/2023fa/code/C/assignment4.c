#include <stdio.h>
#include <stdlib.h> 

char name[32];

void echo ( void ) {
    char echo_str [16];
    printf("What do you want me to echo back?\n"); 
    gets ( echo_str ) ;
    printf("%s\n", echo_str);
}

int main ( void ) {
    printf("What’s your name?\n"); 
    fread(name, 1, 32, stdin); 
    printf("Hi %s\n", name);
    while (1) { 
        echo ( ) ;
    }
    return 0; 
}