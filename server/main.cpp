#include "src/server.cpp"

#pragma clang diagnostic push
#pragma ide diagnostic ignored "EndlessLoop"
int main( int argc , char *argv[])
{
    fprintf(stdout, "[START] VIDEO CHAT SERVER\n");

    /* Custom port check*/
    if(argc < 3) g_svr_port = DEFAULT_PORT;
    else
    {
        if(strcmp("-port",argv[1]) ==  0 )
        {
            g_svr_port = atoi(argv[2]);
            if(g_svr_port < 1024)
            {
                fprintf(stderr, "[ERROR] Server Start Fails : Invalid port number: %d\n", g_svr_port);
                exit(0);
            }
        }
    }

    /* init data */
    init_data();
    /* init server */
    init_server(g_svr_port);
    /* init epoll */
    epoll_init();

    /* main loop */
    while(1)
    {
        server_process();  /* accept process. */
    }

}
#pragma clang diagnostic pop