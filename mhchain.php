<?php

/*
AMChain is trying for creating peer-to-peer
decentraliztion virtual super-computing soft and hard <\\>ware
a Marxist application perfomance interface
with neurologic implemetation
for Blockchain Bigdata analysing

2022 (c) AMChain

MHCHain is Meta Humanist blockchain realization for AMChain Protocol

This code is RaW-PrImEr for our humanity future generations

перед вами реализация на языке PHP
классовая модель основного Атома (блока)
работающего в AMChain
*/


// 	код работает на
//	PHP 8.1.2 (cli) (built: Jun 13 2022 13:52:54) (NTS)


class Blockchain {
	public  $index, $timestamp, $data, $previousHash, $other;

	function Hi() {
		echo "Приветик, Мой Хуёвый Блокчейн";
	}

	function md5Hash() {
		$r = md5($this->index . $this->timestamp . $this->data . $this->previousHash . $this->other);
		return $r;
	}

}

$blockchain = new Blockchain();
$blockchain->index = 0;
$blockchain->timestamp=time();
$blockchain->data="BLOB8BLOB";
$blockchain->previousHash=md5("122887");
$blockchain->Hi();

echo "\n BEGIN \n APP started here \n";

echo "HASH previous block is: " . $blockchain->md5Hash() . "\n";
print_r($blockchain);

?>
