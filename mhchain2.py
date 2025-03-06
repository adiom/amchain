import sys
import socket
import hashlib
import json
from textwrap import dedent
from time import time
from urllib.parse import urlparse
from uuid import uuid4
import requests
from flask import Flask, jsonify, request
import logging

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        # Генезис-блок
        self.new_block(prevhash='1', proof=100)

    def register_node(self, address):
        """
        Вносим новый узел в список узлов, проверяя корректность адреса.
        
        :param address: <str> адрес узла , например: 'http://192.168.0.5:5000'
        :return: None
        """
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
            logger.info(f"Узел добавлен: {parsed_url.netloc}")
        else:
            logger.error("Некорректный адрес")

    def valid_chain(self, chain):
        """
        Проверяем, является ли внесенный в блок хеш корректным.
        
        :param chain: <list> blockchain
        :return: <bool> True если она действительна, False, если нет
        """
        if not chain:
            logger.error("Цепочка пуста")
            return False

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            logger.info(f'Проверка блока: {block}')
            
            if block['previous_hash'] != self.hash(last_block):
                logger.error("Неверный хеш предыдущего блока")
                return False

            if not self.valid_proof(last_block['proof'], block['proof']):
                logger.error("Неверное доказательство работы")
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        Алгоритм Консенсуса, который разрешает конфликты,
        заменяя нашу цепь на самую длинную в сети.
        
        :return: <bool> True, если цепь была заменена, False, если нет.
        """
        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in neighbours:
            try:
                response = requests.get(f'http://{node}/chain')

                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']

                    if length > max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain
            except requests.ConnectionError:
                logger.error(f"Не удалось подключиться к узлу {node}")

        if new_chain:
            self.chain = new_chain
            logger.info("Цепь была заменена")
            return True

        logger.info("Цепь является авторитетной")
        return False

    def new_block(self, proof, prevhash=None):
        """
        Создает новый блок в блокчейне.
        
        :param proof: <int> Доказательство работы
        :param prevhash: (Optional) <str> Хеш предыдущего блока
        :return: <dict> Новый блок
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': prevhash or self.hash(self.chain[-1]),
        }

        self.current_transactions = []
        self.chain.append(block)
        return block

    def valid_proof(self, last_proof, proof):
        """
        Подтверждает доказательство работы.
        
        :param last_proof: <int>
        :param proof: <int>
        :return: <bool> True если доказательство корректно, False если нет.
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    @staticmethod
    def hash(block):
        """
        Создает SHA-256 хеш блока.
        
        :param block: <dict> Блок
        :return: <str>
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

app = Flask(__name__)
blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.chain[-1]
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    blockchain.new_transaction(
        sender="0",
        recipient=str(uuid4()).replace('-', ''),
        amount=1,
    )

    block = blockchain.new_block(proof)

    response = {
        'message': "Новый блок создан",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'Nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }
    return jsonify(response), 200

@app.route('/save', methods=['GET'])
def save_json():
    try:
        with open('file.json', 'w') as fw:
            json.dump(blockchain.chain, fw)

        response = {
            'message': 'Json file saved',
            'filename': 'file.json',
        }
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Ошибка при сохранении файла: {e}")
        return jsonify({'message': 'Ошибка при сохранении файла'}), 500

@app.route('/load', methods=['GET'])
def load_json():
    try:
        with open('file.json', 'r') as fr:
            blockchain.chain = json.load(fr)

        response = {
            'message': 'Json file loaded',
            'filename': 'file.json',
        }
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла: {e}")
        return jsonify({'message': 'Ошибка при загрузке файла'}), 500

@app.route('/chain/<int:index>', methods=['GET'])
def get_block(index):
    try:
        response = {
            'chain': blockchain.chain[index-1],
        }
        return jsonify(response), 200
    except IndexError:
        logger.error("Блок с данным индексом не найден")
        return jsonify({'message': 'Блок не найден'}), 404

if __name__ == '__main__':
    if len(sys.argv) < 4 or sys.argv[1] != 'server':
        raise RuntimeError("Используйте: mhchain.py server [host] [port]")

    host = sys.argv[2]
    port = int(sys.argv[3])
    logger.info(f'Добро пожаловать в mhchain на {host}:{port}')
    app.run(host, port)