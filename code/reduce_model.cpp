#include <iostream>
#include <map>
#include <set>
#include <fstream>
#include <sstream>
#include <string>
#include <string.h>
#include <lemon/list_graph.h>

using namespace lemon;
using namespace std;

int main(int argc, char** argv)
{
	if(argc == 1)
	{
		std::cerr << "No input file given";
		return -1;
	}

	ifstream input;
	input.open(argv[1]);
	if(input.bad())
	{
		std::cerr << "Error opening " << argv[1];
		return -1;
	}

	ofstream output;
	output.open(string(string(argv[1]) + ".reduced.lp").c_str());
	if(output.bad())
	{
		std::cerr << "Error opening " << argv[1] << ".reduced.lp";
		return -1;
	}

	char* read_buffer = new char[1024*1024]; //we have long lines lol

	enum 
	{
		LOOKING_FOR_ZSUM_START,
		LOOKING_FOR_ZSUM_END,
		LOOKING_FOR_CSET_START,
		LOOKNIG_FOR_CSET_END,
		LOOKING_FOR_GENERALS,
		LOOKING_FOR_BINARIES
	} state;
	state = LOOKING_FOR_ZSUM_START;

	const char* START_ZSUM = "\\* START ZSUM *\\";
	const char* END_ZSUM = "\\* END ZSUM *\\";

	map<int, set<int> > z_vars;
	map<int, int> instances_of_talks;
	int z_vars_count = 0;

	#define GET_TOKEN std::getline(parse, token, ' ')
	while(!input.eof())
	{
		input.getline(read_buffer, 1024*1024);

		switch(state)
		{
			case LOOKING_FOR_ZSUM_START:
				if(memcmp(read_buffer, START_ZSUM, strlen(START_ZSUM)) == 0)
				{
					std::cout << "Found ZSUM start" << endl;
					state = LOOKING_FOR_ZSUM_END;
				}
				else
					output << read_buffer << endl;
				break;
			case LOOKING_FOR_ZSUM_END:
				if(memcmp(read_buffer, END_ZSUM, strlen(END_ZSUM)) == 0)
					state = LOOKING_FOR_CSET_START;
				else
				{
					string token;
					istringstream parse(read_buffer);
					while(!parse.eof() && !parse.bad())
					{
						int tid = -1;
						GET_TOKEN; //constraint number
						if(token == "\\*")
							break;
						while(token != "=")
						{
							GET_TOKEN;
							if(token[0] == 'z')
							{
								int underscore_pos = token.find('_', 3);
								string tid_str = token.substr(3, underscore_pos - 3);
								string hid_str = token.substr(underscore_pos + 2, string::npos);
								tid = atoi(tid_str.c_str());
								int hid = atoi(hid_str.c_str());
								z_vars[tid].insert(hid);
								z_vars_count++;
							}
						}
						if(tid == -1)
						{
							std::cerr << "Error parsing ZSUM line:" << endl << read_buffer;
							return -1;
						}
						GET_TOKEN; // number of instances of talk
						instances_of_talks[tid] = atoi(token.c_str());
						std::cout << "Talk " << tid << " has " << z_vars[tid].size() << " possible hours and is given " << instances_of_talks[tid] << " times" << endl;
					}
				}
				break;
			default:
				output << read_buffer << endl;
				break;
		}

	}
	

	delete [] read_buffer;
}