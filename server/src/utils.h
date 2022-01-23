#include <iostream>
#include <vector>
#include <filesystem>
#include <string>

#ifndef SERVER_UTILS_H
#define SERVER_UTILS_H


/**
 * This function splits string
 * @param s
 * @param delimiter
 * @return vector of strings
 */
std::vector<std::string> split(const std::string &s, char delimiter) {
    std::vector<std::string> tokens;
    std::string token;
    std::istringstream tokenStream(s);
    while (std::getline(tokenStream, token, delimiter)) {
        tokens.push_back(token);
    }
    return tokens;
}

int is_in_vector(const std::vector<std::vector<std::string>>& array, const std::string &login, const std::string &password) {
    for (auto vector : array) {
        if (vector[1] == login) {
            if (vector[2] == password) {
                return 1;
            }
            else {
                return -2;
            }
        }
    }
    return -3;
}

#endif //SERVER_UTILS_H
