#!/bin/sh

g++-8 freeling_analyzer.cc -o freeling_analyzer -lfreeling -lboost_system -lstdc++fs -std=c++17 -fopenmp
./freeling_analyzer
