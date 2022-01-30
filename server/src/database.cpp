#include <iostream>
#include <sqlite3.h>
#include "utils.h"

class Account {
private:
    std::string login;
    std::string password;
    int fd = -1;
    int vid_fd = -1;
    bool is_connected = false;
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
    std::vector<Account> get_friend_list() const {
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
    void add_friend(const Account &friend_acc) {
        this->friend_list.push_back(friend_acc);
    }
    void reset_fd() {
        set_vid_fd(-1);
        set_fd(-1);
    }
    bool in_friend_list(std::string& name){
        for (Account& account : get_friend_list()) {
            if(account.get_login() == name) {
                return true;
            }
        }
        return false;
    }
    void set_is_connected(bool status){
        this->is_connected = status;
    }
    bool get_is_connected() {
        return this->is_connected;
    }

    Account() {}
};

std::vector<Account> g_users;

void print_accounts(){
    for (Account& account : g_users) {
        std::cout << account.get_login() << "\t" << account.get_password() << "\t" << account.get_fd() << "\t" << account.get_vid_fd() << "\t" << account.get_is_connected()<< std::endl;
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
                account.set_is_connected(true);
                return 1;
            } else {
                return -2;
            }
        }
    }
    return -3;
}
