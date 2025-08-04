
#include <stdio.h>
#include <stdlib.h> 

void func(int len, char *data) {
    char buf[64];
    if (len > 64)
        return;
    printf("You should not be here when len = -1");
}

int main() {
    func(-1,NULL);
    return 0;
}