#include <iostream>
#include <sqlite3.h>
#include "utils.h"

class Account {
private:
    std::string login;
    std::string password;
    int fd = 0;
    int vid_fd = 0;
    std::vector<Account> friend_list;
public:
    Account(const std::string& login, const std::string& password) {
        this->login = login;
        this->password = password;
    }
    std::string get_login(){
        return this->login;
    }
    std::string get_password(){
        return this->password;
    }
    int get_fd() {
        return this->fd;
    }
    int get_vid_fd() {
        return this->vid_fd;
    }
    std::vector<Account> get_friend_list() {
        return this->friend_list;
    }
    void set_fd(int socket) {
        this->fd = socket;
    }
    void set_vid_fd(int socket) {
        this->vid_fd = socket;
    }
    void set_friend_list(std::vector<Account> friend_list) {
        this->friend_list = friend_list;
    }
    void add_friend(Account friend_acc) {
        this->friend_list.push_back(friend_acc);
    }
//    void remove_friend(Account friend_acc) {
//        
//    }
};

std::vector<Account> g_users;

void print_accounts(){
    for (auto account : g_users) {
        std::cout << account.get_login() << "\t" << account.get_password() << std::endl;
    }
}

int register_account(const std::string& login, const std::string& password){
    Account new_acc = Account(login, password);

    for (auto account : g_users) {
        if (account.get_login() == new_acc.get_login()) {
            return -1;
        }
    }
    g_users.push_back(new_acc);
    return 1;
}

int login_account(const std::string& login, const std::string& password) {
    for (auto account : g_users) {
        if (account.get_login() == login) {
            if (account.get_password() == password) {
                return 1;
            } else {
                return -2;
            }
        }
    }
    return -3;
}
