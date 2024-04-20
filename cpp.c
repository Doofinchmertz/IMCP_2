#include <iostream>
#include <vector>
#include <string>

using namespace std;

int main() {
    vector<string> names;
    names.push_back("John");
    names.push_back("Paul");
    names.push_back("George");
    names.push_back("Ringo");

    for (int i = 0; i < names.size(); i++) {
        cout << names[i] << endl;
    }

    return 0;
}