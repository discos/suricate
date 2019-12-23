#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <hiredis.h>

int main(int argc, char **argv) {
    unsigned int j, isunix = 0;
    redisContext *c; 
    redisReply *reply;
    const char *hostname = (argc > 1) ? argv[1] : "192.168.200.207";

    if (argc > 2) {
        if (*argv[2] == 'u' || *argv[2] == 'U') {
            isunix = 1;
            /* in this case, host is the path to the unix socket */
            printf("Will connect to unix socket @%s\n", hostname);
        }
    }   

    int port = (argc > 2) ? atoi(argv[2]) : 6379;

    struct timeval timeout = { 1, 500000 }; // 1.5 seconds
    if (isunix) {
        c = redisConnectUnixWithTimeout(hostname, timeout);
    } else {
        c = redisConnectWithTimeout(hostname, port, timeout);
    }   
    if (c == NULL || c->err) {
        if (c) {
            printf("Connection error: %s\n", c->errstr);
            redisFree(c);
        } else {
            printf("Connection error: can't allocate redis context\n");
        }
        exit(1);
    }   

    reply = redisCommand(c,"HGETALL ANTENNA/Boss/rawAzimuth");
    int i;
    printf("\nHGETALL ANTENNA/Boss/rawAzimuth\n");
    for(i=0; i<reply->elements; i++) {
        if(i%2 == 0) {
            printf("* %s: ", reply->element[i]->str);
        }
        else {
            printf("%s\n", reply->element[i]->str);
        }
    }   
    freeReplyObject(reply);

    reply = redisCommand(c,"HGET ANTENNA/Boss/rawAzimuth value");
    printf("\nHGET ANTENNA/Boss/rawAzimuth value: %s\n", reply->str);
    freeReplyObject(reply);

    /* Disconnects and frees the context */
    redisFree(c);

    return 0;

