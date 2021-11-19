#include <sys/time.h>
#include <stdio.h>
#include <stdlib.h>

unsigned long usec, sec;

int main(int argc, char **argv)
{
    if(argc<3)
    {
      perror("Not enough input arguments!: setclock delta_sec delta_us");
      exit(1);
    }
    sscanf(argv[1],"%lu",&sec);
    sscanf(argv[2],"%lu",&usec);
    struct timeval delta;
    delta.tv_sec = sec;
    delta.tv_usec = usec;
    int status = settimeofday(&delta,NULL);
    return 0;
}
