/*
AMChain is trying for creating peer-to-peer
decentraliztion virtual super-computing soft and hard <\\>ware
a Marxist application perfomance interface
with neurologic implemetation
for Blockchain Bigdata analysing

2022 (c) AMChain

MHCHain is Meta Humanist blockchain realization for AMChain Protocol

This code is RaW-PrImEr for our humanity future generations

перед вами реализация на языке C++
классовая модель основного Атома (блока)
работающего в AMChain
*/


//    код работает на gcc в lubuntu 22.04
// 
#include <string>


struct Blockchain
{
   std::string index; // index блока
   std::string timestamp; // ага богаты на ОЗУ храним всё в стринг
   std::string data; //data for current block
   std::string prev_hash; // stores hah for previous block
   std::string other; // доп данные еее

   std::string Hi() {
         std::string r ="HHH";
      return r;
   }
};

int main() {
   Blockchain blockchain;
   printf(blockchain);
}
