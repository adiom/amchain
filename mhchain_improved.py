
import sys
import socket
import hashlib
import json
from textwrap import dedent
from time import time
from urllib.parse import urlparse
from uuid import uuid4
import requests
from flask import Flask, jsonify, request, render_template, abort
import logging
from werkzeug.exceptions import HTTPException

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        # Генезис-блок
        self.new_block(previous_hash='1', proof=100)

    def register_node(self, address):
        """
        Добавить новый узел в список узлов
        """
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    def valid_chain(self, chain):
        """
        Проверка того, является ли блокчейн действительным
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            logger.info(f'{last_block}')
            logger.info(f'{block}')
            logger.info("-----------")
            # Проверка правильности хеша блока
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # Проверка доказательства работы
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        Это наш алгоритм консенсуса, он решает конфликты путем замены нашей цепи на самую длинную в цепи.
        """
        neighbours = self.nodes
        new_chain = None

        # Мы ищем только цепи длиннее нашей
        max_length = len(self.chain)

        # Получаем и проверяем цепи от всех узлов в нашей сети
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Проверяем, если длина больше и цепь валидна
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Заменяем нашу цепь, если нашли другую валидную цепь большей длины
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def new_block(self, proof, previous_hash=None):
        """
        Создание нового блока в блокчейне
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Обнуляем текущий список транзакций
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Создание новой транзакции, которая будет добавлена в следующий блок
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """
        Создает SHA-256 хеш блока
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_block):
        """
        Простой алгоритм доказательства работы:
        - Поиск числа p' такое, что hash(pp') содержит 4 ведущих нуля, где p это предыдущий p'
        - p это предыдущий proof, а p' это новый proof
        """
        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        """
        Проверка доказательства: содержит ли hash(last_proof, proof) 4 ведущих нуля?
        """
        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

# Создание веб-приложения с Flask
app = Flask(__name__)

# Создание экземпляра блокчейна
blockchain = Blockchain()

@app.errorhandler(HTTPException)
def handle_exception(e):
    """Возвращаем JSON вместо HTML для HTTP ошибок."""
    response = e.get_response()
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response

@app.route('/mine', methods=['GET'])
def mine():
    # Запуск алгоритма доказательства работы для получения следующего доказательства...
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # Должен получить награду за нахождение доказательства.
    blockchain.new_transaction(
        sender="0",
        recipient=str(uuid4()).replace('-', ''),
        amount=1,
    )

    # Создаем новый блок, добавляем его в цепь
    block = blockchain.new_block(proof)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Проверка, что все необходимые поля присутствуют
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Создание новой транзакции
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

@app.route('/register_node', methods=['POST'])
def register_node():
    values = request.get_json()

    # Проверка, что поле адреса присутствует
    required = ['nodes']
    if not all(k in values for k in required):
        return "Error: Please supply a valid list of nodes", 400

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
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

# Веб-интерфейс
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transaction_form')
def transaction_form():
    return render_template('transaction_form.html')

@app.route('/mine_block')
def mine_block():
    return render_template('mine_block.html')

if __name__ == '__main__':
    # Получение порта из системных переменных для более безопасного использования в облачных средах
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    app.run(host='0.0.0.0', port=port)
