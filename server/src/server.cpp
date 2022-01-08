#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <sys/epoll.h>
#include <arpa/inet.h>
#include <iostream>
#include <string.h>
#include <unistd.h>
#include <opencv2/opencv.hpp>

#define MAX_CLIENT   10
#define DEFAULT_PORT 3108
#define MAX_EVENTS   100
#define MAX_BUFFER_SIZE  1000000


int g_svr_sockfd;                   /* global server socket fd */
int g_svr_port;                     /* global server port number */

struct {
    int cli_sockfd;                 /* client socket fds */
    char cli_ip[20];                /* client connection ip */
} g_client[MAX_CLIENT];

int g_epoll_fd;                     /* epoll fd */

struct epoll_event g_events[MAX_EVENTS];
char buf[MAX_BUFFER_SIZE];

/**
 * Function prototypes
*/
void init_data(void);               /* initialize data. */
void init_server(int svr_port);     /* server socket bind/listen */
void epoll_init(void);              /* epoll fd create */
void epoll_cli_add(int cli_fd);     /* client fd add to epoll set */

void userpool_add(int cli_fd, char *cli_ip); /* Adds user to pool */


/**
 * This function initializes client structure values.
 */
void init_data(void) {
    int i;

    for (i = 0; i < MAX_CLIENT; i++) {
        g_client[i].cli_sockfd = -1;
    }
}

/**
 * This function initializes server.
 * @param svr_port server port (has to be positive e.g. 1234)
 */
void init_server(int svr_port) {
    struct sockaddr_in serv_addr;

    /* Open TCP Socket */
    if ((g_svr_sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        fprintf(stderr, "[ERROR] Server Start Fails : Can't open stream socket.\n");
        exit(0);
    }

    /* Address Setting */
    memset(&serv_addr, 0, sizeof(serv_addr));

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    serv_addr.sin_port = htons(svr_port);

    /* Set Socket Option  */
    int nSocketOpt = 1;
    if (setsockopt(g_svr_sockfd, SOL_SOCKET, SO_REUSEADDR, &nSocketOpt, sizeof(nSocketOpt)) < 0) {
        fprintf(stderr, "[ERROR] Server Start Fails : Can't set reuse address.\n");
        close(g_svr_sockfd);
        exit(0);
    }

    /* Bind Socket */
    if (bind(g_svr_sockfd, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0) {
        fprintf(stderr, "[ERROR] Server Start Fails : Can't bind local address.\n");
        close(g_svr_sockfd);
        exit(0);
    }

    /* Listening */
    listen(g_svr_sockfd, 30); /* connection queue is 15. */

    fprintf(stdout, "[START] Now Server listening on port %d\n", svr_port);
    fprintf(stdout, "[DEBUG] Server ip: %s\n", inet_ntoa(serv_addr.sin_addr));
}

/**
 * This function initializes epoll.
 */
void epoll_init(void) {
    struct epoll_event events;

    g_epoll_fd = epoll_create(MAX_EVENTS);
    if (g_epoll_fd < 0) {
        fprintf(stderr, "[ERROR] Epoll Create Fails : Can't initialize epoll.\n");
        close(g_svr_sockfd);
        exit(0);
    }
    fprintf(stdout, "[START] Epoll creation success.\n");

    /* event control set */
    events.events = EPOLLIN;
    events.data.fd = g_svr_sockfd;

    /* server events set(read for accept) */
    if (epoll_ctl(g_epoll_fd, EPOLL_CTL_ADD, g_svr_sockfd, &events) < 0) {
        fprintf(stderr, "[ERROR] Epoll Control Fails : TODO\n");
        close(g_svr_sockfd);
        close(g_epoll_fd);
        exit(0);
    }

    fprintf(stdout, "[START] Epoll events set success for server.\n");
}

/**
 * This function adds client to epoll events.
 * @param cli_fd client socket descriptor.
 */
void epoll_cli_add(int cli_fd) {

    struct epoll_event events;

    /* event control set for read event */
    events.events = EPOLLIN;
    events.data.fd = cli_fd;

    if (epoll_ctl(g_epoll_fd, EPOLL_CTL_ADD, cli_fd, &events) < 0) {
        fprintf(stderr, "[ERROR] Epoll Control Fails : Can't add client to epoll event. <epoll_cli_add>\n");
    }

}

/**
 * This function adds new client to userpool.
 * @param cli_fd client socket descriptor
 * @param cli_ip client ip address
 */
void userpool_add(int cli_fd, char *cli_ip) {
    /* get empty element */
    int i;

    for (i = 0; i < MAX_CLIENT; i++) {
        if (g_client[i].cli_sockfd == -1) break;
    }
    if (i >= MAX_CLIENT) close(cli_fd);

    g_client[i].cli_sockfd = cli_fd;
    memset(&g_client[i].cli_ip[0], 0, 20);
    strcpy(&g_client[i].cli_ip[0], cli_ip);

}

/**
 * This function deletes user from userpool.
 * @param cli_fd client socket descriptor
 */
void userpool_delete(int cli_fd) {
    int i;

    for (i = 0; i < MAX_CLIENT; i++) {
        if (g_client[i].cli_sockfd == cli_fd) {
            g_client[i].cli_sockfd = -1;
            break;
        }
    }
}

/**
 * This function sends message to all users from userpool.
 * @param buffer message buffer
 */
void userpool_send(char *buffer) {
    int i;
    int len;

    len = strlen(buffer);

    for (i = 0; i < MAX_CLIENT; i++) {
        if (g_client[i].cli_sockfd != -1) {
            len = send(g_client[i].cli_sockfd, buffer, len, 0);
            fprintf(stdout, "[DEBUG] Send to %d : %s\n", g_client[i].cli_sockfd, buffer);
            // TODO code
        }
    }

}

/**
 * This function receives message from client.
 * @param event_fd event descriptor
 */
void client_recv(int event_fd) {
    char r_buffer[MAX_BUFFER_SIZE]; /* for test.  packet size limit 1K */
    int len;
    // TODO code2
    /* there need to be more precise code here */
    /* for example , packet check(protocol needed) , real recv size check , etc. */

    /* read from socket */
    len = recv(event_fd, r_buffer, MAX_BUFFER_SIZE, 0);

    if (len < 0 || len == 0) {
        userpool_delete(event_fd);
        close(event_fd); /* epoll set fd also deleted automatically by this call as a spec */
        return;
    }
    fprintf(stdout, "[DEBUG] Client send: %s\n", r_buffer);

//    userpool_send("Message received.\n");
}

void client_recv2(int event_fd) {
    cv::Mat img;
    img = cv::Mat::zeros(480 , 640, CV_8UC3);
    int imgSize = img.total() * img.elemSize();
    uchar *iptr = img.data;
    int bytes = 0;
    int key;

    //make img continuos
    if ( ! img.isContinuous() ) {
        img = img.clone();
    }

    std::cout << "Image Size:" << imgSize << std::endl;

    cv::namedWindow("CV Video Client",1);

    while (key != 'q') {

        if ((bytes = recv(event_fd, iptr, imgSize , MSG_WAITALL)) == -1) {
            std::cerr << "recv failed, received bytes = " << bytes << std::endl;
        }

        cv::imshow("CV Video Client", img);

        if ((key = cv::waitKey(10)) >= 0) break;
    }
}

/**
 * This function processes epoll events.
 */
void server_process(void) {
    struct sockaddr_in cli_addr;
    int i, nfds;
    int cli_sockfd;
    int cli_len = sizeof(cli_addr);
    int isFirst = 1;

    nfds = epoll_wait(g_epoll_fd, g_events, MAX_EVENTS, 100); /* timeout 100ms */

    if (nfds == 0) return; /* no event , no work */
    if (nfds < 0) {
        fprintf(stderr, "[ERROR] Epoll Wait Error.\n");
        return; /* return but this is epoll wait error */
    }

    for (i = 0; i < nfds; i++) {
        if (g_events[i].data.fd == g_svr_sockfd) {
            cli_sockfd = accept(g_svr_sockfd, (struct sockaddr *) &cli_addr, (socklen_t *) &cli_len);
            if (cli_sockfd < 0) /* accept error */
            {
            } else {
                fprintf(stdout, "[DEBUG][ACCEPT] New client connected. fd:%d, ip:%s\n", cli_sockfd,
                        inet_ntoa(cli_addr.sin_addr));
                userpool_add(cli_sockfd, inet_ntoa(cli_addr.sin_addr));
                epoll_cli_add(cli_sockfd);
            }
            continue; /* next fd */
        }
        /* if not server socket , this socket is for client socket, so we read it */
        if ((nfds >= 20) && (isFirst == 1)) {
//            userpool_send("$");
            isFirst = 0;
        }

        client_recv2(g_events[i].data.fd);
    } /* end of for 0-nfds */
}

/**
 * This function shuts down server.
 * @param sig
 */
void end_server(int sig) {
    close(g_svr_sockfd); /* close server socket */
    fprintf(stdout, "[DEBUG][SHUTDOWN] Server closed by signal %d\n", sig);
    exit(0);
}