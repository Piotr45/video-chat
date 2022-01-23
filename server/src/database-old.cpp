#include <iostream>
#include <sqlite3.h>
#include "utils.h"

std::vector<std::vector<std::string>> accounts;

/**
 * TODO doc
 * @param data
 * @param argc
 * @param argv
 * @param azColName
 * @return
 */
static int callback(void* data, int argc, char** argv, char** azColName)
{
    int i;
    std::vector<std::string> tmp;

    for (i = 0; i < argc; i++) {
//        printf("%s = %s\n", azColName[i], argv[i] ? argv[i] : "NULL");
        tmp.push_back(argv[i] ? argv[i]: "NULL");
    }
    accounts.push_back(tmp);
    return 0;
}

/**
 * This function opens database.
 * @param DB pointer to database
 * @return information about success
 */
bool database_is_opened(int exit){
    /* Open database */
    if (exit) {
        fprintf(stderr, "[ERROR] Could not open DB.\n");
        return false;
    }
    else {
        fprintf(stdout, "[DEBUG] Database opened successfully.\n");
        return true;
    }
}

/**
 * This function adds new user to database.
 * @param login login of new user
 * @param password password of new user
 */
int database_add_user(const std::string& login, const std::string& password){
    sqlite3 *DB;
    if (!database_is_opened(sqlite3_open("user_accounts.db", &DB))){
        sqlite3_close(DB);
        return -1;
    }
    //TODO add responds
    std::string query = "INSERT INTO ACCOUNTS('LOGIN', 'PASSWORD') VALUES('" + login + "','" + password + "');";
    std::cout << query << std::endl;
    int rc = sqlite3_exec(DB, query.c_str(), nullptr, nullptr, nullptr);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "[ERROR] Database insert error.\n");
    }
    else {
        fprintf(stdout, "[DEBUG] Record added successfully.\n");
    }

    if (sqlite3_close(DB)) {
        fprintf(stdout, "[DEBUG] Database closed successfully.\n");
    }
}

/**
 *
 * @param login user login to check
 * @param password user password to check
 * @return
 */
int database_check_user(const std::string& login, const std::string& password) {
    accounts.clear();
    sqlite3 *DB;
    if (!database_is_opened(sqlite3_open("user_accounts.db", &DB))){
        sqlite3_close(DB);
        return -1;
    }
    /* Read data in database and compare them with data that we received from client */
    std::string query("SELECT * FROM ACCOUNTS;");
    int rc = sqlite3_exec(DB, query.c_str(), callback, nullptr, nullptr);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "[ERROR] Query error.\n");
        return -1;
    }
    else {
        fprintf(stdout, "[DEBUG] Query executed successfully.\n");
    }

    if (sqlite3_close(DB)) {
        fprintf(stdout, "[DEBUG] Database closed successfully.\n");
    }

    int ret = is_in_vector(accounts, login, password);
    if (ret == 1) {
        fprintf(stdout, "[DEBUG] Login and password are correct.\n");
        return 1;
    }
    else if (ret == -2) {
        fprintf(stdout, "[DEBUG][ERROR] Login is correct, but password is incorrect.\n");
        return -2;
    }
    else if (ret == -3) {
        fprintf(stdout, "[DEBUG][ERROR] There is no user with login <%s>\n", login.c_str());
        return -3;
    }
}
