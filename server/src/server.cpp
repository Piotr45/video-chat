#include <cstdio>
#include <cstdlib>
#include <sys/socket.h>
#include <sys/epoll.h>
#include <arpa/inet.h>
#include <iostream>
#include <cstring>
#include <unistd.h>
#include <opencv2/opencv.hpp>
#include "database.cpp"

#define MAX_CLIENT   16
#define DEFAULT_PORT 3108
#define MAX_EVENTS   100
#define MAX_BUFFER_SIZE  2048


int g_svr_sockfd;                   /* global server socket fd */
int g_svr_port;                     /* global server port number */

struct client_data {
    int cli_sockfd;                 /* client socket fds */
    char cli_ip[20];                /* client connection ip */
} g_client[MAX_CLIENT];
struct client_data g_approved_clients[MAX_CLIENT];

int g_epoll_fd;                     /* epoll fd */

struct video_pair {
    int video_1;
    int video_2;
};

std::vector<video_pair> g_active_calls;
std::vector<int> g_command_sockets;
std::vector<int> g_video_sockets;

struct epoll_event g_events[MAX_EVENTS];

/**
 * Function prototypes
*/
void init_data();               /* initialize data. */
void init_server(int svr_port);     /* server socket bind/listen */
void epoll_init();              /* epoll fd create */
void epoll_cli_add(int cli_fd);     /* client fd add to epoll set */

void userpool_add(int cli_fd, char *cli_ip); /* Adds user to pool */


/**
 * This function initializes client structure values.
 */
void init_data() {
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
    struct sockaddr_in serv_addr{};

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
void epoll_init() {
    struct epoll_event events{};

    g_epoll_fd = epoll_create(MAX_EVENTS);
    if (g_epoll_fd < 0) {
        fprintf(stderr, "[ERROR] Epoll Create Fails : Can't initialize epoll.\n");
        close(g_svr_sockfd);
        exit(0);
    }
    fprintf(stdout, "[START] Created epoll file descriptor with success.\n");

    /* event control set */
    events.events = EPOLLIN;
    events.data.fd = g_svr_sockfd;

    /* server events set(read for accept) */
    if (epoll_ctl(g_epoll_fd, EPOLL_CTL_ADD, g_svr_sockfd, &events) < 0) {
        fprintf(stderr, "[ERROR] Epoll Control Fails: <EPOLL_CTL_ADD> failed.\n");
        close(g_svr_sockfd);
        close(g_epoll_fd);
        exit(0);
    }

    fprintf(stdout, "[START] Epoll events set success for server.\n");
}

/**
 * This function adds client file descriptor to epoll events.
 * @param cli_fd client socket descriptor.
 */
void epoll_cli_add(int cli_fd) {

    struct epoll_event events{};

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
 * Funtion that sends message to client.
 * @tparam T type of message
 * @param fd client file descriptor
 * @param message actual message
 * @param message_size message length (size)
 */
template<typename T>
void send_message(int fd, const T &message, int message_size) {
    int bytes;

    if ((bytes = send(fd, message, message_size, 0)) == -1) {
        fprintf(stderr, "[ERROR] Send failed, send %d bytes", bytes);
    }
}

/**
 * Gets account using client file descriptor.
 * @param fd client file descriptor
 * @return account associated with client file descriptor
 */
Account get_account(int fd) {
    for (Account &account: g_users) {
        if (account.get_fd() == fd) {
            return account;
        }
    }
}
Account get_account2(int fd) {
    for (Account &account: g_users) {
        if (account.get_vid_fd() == fd) {
            return account;
        }
    }
}

/**
 * Send all active friends to all active users.
 */
void send_active_friends() {
    std::string str;
    int bytes;
    for (int fd: g_command_sockets) {
        str.clear();
        str.append("ACTIVE\n");
//        get_account(fd);
        for (Account &account: get_account(fd).get_friend_list()) {
            str.append(account.get_login());
            str.push_back('\n');
        }
        if ((bytes = send(fd, str.c_str(), str.size(), 0)) == -1) {
            fprintf(stderr, "[ERROR] Send failed, send %d bytes", bytes);
        }
    }
}

/**
 * Checks if file descriptor belongs to video sockets.
 * @param event_fd client video socket
 * @return True if file descriptor belongs to video sockets, otherwise False.
 */
bool is_video_socket(int event_fd) {
    for (auto socket: g_video_sockets) {
        if (socket == event_fd) {
            return true;
        }
    }
    return false;
}

/**
 * Adds user to active users and links client file descriptor to command socket of a account.
 * @param event_fd client file descriptor (command socket)
 * @param login user login
 */
void add_connection(int event_fd, const std::string &login) {
    for (Account &account: g_users) {
        if (account.get_login() == login) {
            account.set_fd(event_fd);
            account.set_is_connected(true);
            return;
        }
    }
}

/**
 * Handles registration process.
 * @param event_fd client file descriptor (command socket)
 * @param login user login
 * @param password user password
 */
void handle_registration(int event_fd, const std::string &login, const std::string &password) {
    int ret = register_account(login, password);
    if (ret == 1) {
        send(event_fd, "1", strlen("1"), 0);
    } else if (ret == -1) {
        send(event_fd, "-1", strlen("-1"), 0);
    }
}

/**
 * Handles log in process
 * @param event_fd client file descriptor (command socket)
 * @param login user login
 * @param password user password
 */
void handle_login(int event_fd, const std::string &login, const std::string &password) {
    int ret = login_account(login, password);
    if (ret == 1) {
        add_connection(event_fd, login);
        send(event_fd, "1", strlen("1"), 0);
    } else if (ret == -2) {
        send(event_fd, "-2", strlen("-2"), 0);
    } else if (ret == -3) {
        send(event_fd, "-3", strlen("-3"), 0);
    } else if (ret == -4) {
        send(event_fd, "-4", strlen("-4"), 0);
    }
}

/**
 * Handles adding friend process.
 * @param event_fd client file descriptor (command socket)
 * @param friend_name user name that we want add to friend list
 */
void handle_adding_friends(int event_fd, std::string &friend_name) {
    std::string str;

    if (get_account(event_fd).in_friend_list(friend_name)) {
        str.append("ADD-FRIEND\n-2\n");
        send_message(event_fd, str.c_str(), str.size());
        return;
    }
    if (get_account(event_fd).get_login() == friend_name) {
        str.append("ADD-FRIEND\n-3\n");
        send_message(event_fd, str.c_str(), str.size());
        return;
    }

    for (Account &account: g_users) {
        //and account.get_login() != get_account(event_fd).get_login()
        if (account.get_login() == friend_name) {
            for (Account& acc : g_users) {
                if (acc.get_fd() == event_fd) {
                    acc.add_friend(account);
                }
            }
//            get_account(event_fd).add_friend(account);

            account.add_friend(get_account(event_fd));

            get_account(event_fd).print_friend_list();

            str.append("ADD-FRIEND\n1\n");
            send_message(event_fd, str.c_str(), str.size());
            return;
        }
    }
    str.append("ADD-FRIEND\n-1\n");
    send_message(event_fd, str.c_str(), str.size());
}

/**
 * Checks if client is already in video call.
 * @param fd client file descriptor (video socket)
 * @return True if client is in video chat, False otherwise
 */
bool is_chatting(int fd) {
    for (auto& pair : g_active_calls) {
        if (pair.video_1 == fd or pair.video_2 == fd) {
            return true;
        }
    }
    return false;
}

/**
 * Handles calling.
 * @param event_fd client file descriptor (command socket)
 * @param name user name that we want to call
 */
void handle_call(int event_fd, std::string& name) {
    std::string call = "CALL\n";
    for (Account& account : g_users) {
        if (account.get_login() == name and !is_chatting(account.get_vid_fd()) and account.get_is_connected()) {
            call.append("1\n");

            video_pair pair;
            pair.video_1 = account.get_vid_fd();
            pair.video_2 = get_account(event_fd).get_vid_fd();
            // Respond to client
            send_message(event_fd, call.c_str(), call.size());
            // Respond to friend
            send_message(account.get_fd(), call.c_str(), call.size());

            g_active_calls.push_back(pair);
            return;
        }
    }
    call.append("-1\n");
    send_message(event_fd, call.c_str(), call.size());
}

/**
 * Handles paring sockets
 * @param fd file descriptor
 * @param socket_type type of file descriptor (COMMAND, VIDEO)
 * @param login user login
 * @param password user password
 */
void handle_pairing(int fd, std::string& socket_type, std::string& login, std::string& password) {
    for (Account& account : g_users) {
        if(account.get_login() == login and account.get_password() == password) {
            if (socket_type == "COMMAND") {
                g_command_sockets.push_back(fd);
                account.set_fd(fd);
            }
            if (socket_type == "VIDEO") {
                g_video_sockets.push_back(fd);
                account.set_vid_fd(fd);
            }
        }
    }
}

/**
 * Handles hanging up
 * @param fd file descriptor (command descriptor)
 */
void handle_hang_up(int fd) {
    std::string str = "HANG UP\n";
    for (video_pair& pair : g_active_calls) {
        if (pair.video_2 == get_account(fd).get_vid_fd()) {
            str.append("1\n");
            send_message(fd, str.c_str(), str.size());
            send_message(get_account2(pair.video_1).get_fd(), str.c_str(), str.size());
            pair.video_1 = -1;
            pair.video_2 = -1;
            break;
        }
        if (pair.video_1 == get_account(fd).get_vid_fd()) {
            str.append("1\n");
            send_message(fd, str.c_str(), str.size());
            send_message(get_account2(pair.video_2).get_fd(), str.c_str(), str.size());
            pair.video_1 = -1;
            pair.video_2 = -1;
            break;
        }
    }
}

/**
 * This function receives message from client.
 * @param event_fd event descriptor
 */
void client_recv(int event_fd) {
    char r_buffer[MAX_BUFFER_SIZE];
    int len;

    /* read from socket */
    len = recv(event_fd, r_buffer, MAX_BUFFER_SIZE, 0);

    if (len < 0 || len == 0) {
        userpool_delete(event_fd);
        close(event_fd); /* epoll set fd also deleted automatically by this call as a spec */
        return;
    }

    std::vector<std::string> tokens = split(r_buffer, '\n');
    if (tokens[0] == "PAIR") {
        handle_pairing(event_fd, tokens[1], tokens[2], tokens[3]);
        return;
    }
    if (tokens[0] == "REGISTER") {
        handle_registration(event_fd, tokens[1], tokens[2]);
        return;
    }
    if (tokens[0] == "LOGIN") {
        handle_login(event_fd, tokens[1], tokens[2]);
        return;
    }
    if (tokens[0] == "ACTIVE") {
        send_active_friends();
        return;
    }
    if (tokens[0] == "ADD-FRIEND") {
        handle_adding_friends(event_fd, tokens[1]);
        send_active_friends();
        return;
    }
    if (tokens[0] == "CALL") {
        handle_call(event_fd, tokens[1]);
        return;
    }
    if (tokens[0] == "HANG UP") {
        handle_hang_up(event_fd);
        return;
    }
}

int dupa = 0;
/**
 * Receives and forwards messages between two clients.
 * @param event_fd client file descriptor (video socket)
 */
void recv_and_forward_image(int event_fd) {
    if (! is_chatting(event_fd)) {
        return;
    }

    cv::Mat img;
    img = cv::Mat::zeros(240, 320, CV_8UC3);
    int imgSize = img.total() * img.elemSize();
    uchar *iptr = img.data;
    int bytes = 0;

    // Make image continuous
    if (!img.isContinuous()) {
        img = img.clone();
    }

    if ((bytes = recv(event_fd, iptr, imgSize, MSG_WAITALL)) == -1) {
        std::cerr << "recv failed, received bytes = " << bytes << std::endl;
    }
//    send(event_fd, img.data, imgSize, MSG_NOSIGNAL);
    for (video_pair& pair : g_active_calls) {
        if(pair.video_2 == event_fd) {
            send(pair.video_1, img.data, imgSize, MSG_NOSIGNAL);
        }
        else if (pair.video_1 == event_fd) {
            send(pair.video_2, img.data, imgSize, MSG_NOSIGNAL);
        }
    }
}

/**
 * This function processes epoll events.
 */
void server_process() {
    struct sockaddr_in cli_addr{};
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

        if (is_video_socket(g_events[i].data.fd)) {
            recv_and_forward_image(g_events[i].data.fd);
        } else {
            client_recv(g_events[i].data.fd);
        }

//        send_active_accounts();
    } /* end of for 0-nfds */
//    print_accounts();
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