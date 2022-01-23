#include <iostream>
#include <sqlite3.h>
#include "utils.h"

class Account {
private:
    std::string login;
    std::string password;
    int fd = 0;
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
    void set_fd(int fd) {
        this->fd = fd;
    }
};

std::vector<Account> g_accounts;

void print_accounts(){
    for (auto account : g_accounts) {
        std::cout << account.get_login() << "\t" << account.get_password() << std::endl;
    }
}

int register_account(const std::string& login, const std::string& password){
    Account new_acc = Account(login, password);

    for (auto account : g_accounts) {
        if (account.get_login() == new_acc.get_login()) {
            return -1;
        }
    }
    g_accounts.push_back(new_acc);
    return 1;
}

int login_account(const std::string& login, const std::string& password) {
    for (auto account : g_accounts) {
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
