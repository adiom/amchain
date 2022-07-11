
/*
AMChain is trying for creating peer-to-peer
decentraliztion virtual super-computing soft and hard <\\>ware
a Marxist application perfomance interface
with neurologic implemetation
for Blockchain Bigdata analysing

2022 (c) AMChain

MHCHain is Meta Humanist blockchain realization for AMChain Protocol

This code is RaW-PrImEr for our humanity future generations

перед вами реализация на языке GoLang
классовая модель основного Атома (блока)
работающего в AMChain
*/

// https://digitrain.ru/articles/14302/
// https://russianblogs.com/article/94951179971/

package main

type Block struct {
	Hash		[]byte
	Data		[]byte
	PrevHash	[]byte
}

type BlockChain struct{
	blocks []*Block
}

func (b *Block) DeriveHash() {
  info := bytes.Join([][]byte{b.Data, b.PrevHash}, []byte{})
  // This will join our previous block hash with current block data
  
  hash := sha256.Sum256(info)
  //The actual hashing algorithm
  
  b.Hash = hash[:] 
}

func CreateBlock(data string, prevHash []byte) *Block {
    block := &Block{[]byte{}, []byte(data), prevHash}
        //It is simple subtituing value to block
    block.DeriveHash()
    return block
}

func (chain *BlockChain) AddBlock(data string) {
	prevBlock := chain.blocks[len(chain.blocks)-1]
}

func main() {
	println(Block)
}