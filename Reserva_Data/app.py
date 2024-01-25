from flask import Flask, render_template, request, jsonify, redirect
import datetime
import json
import os

app = Flask(__name__)

# Get the directory path of the current script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Caminho para o arquivo de dados
DATA_FILE_PATH = os.path.join(BASE_DIR, 'reservas_data.txt')


# Função para carregar os dados de reservas do arquivo (se existir)
def load_reservas():
  if os.path.exists(DATA_FILE_PATH):
    with open(DATA_FILE_PATH, 'r') as file:
      reservas = json.load(file)
      # Converter as datas para o formato "dd/mm/aaaa"
      for date_str in list(reservas.keys()):  # Criar uma cópia das chaves
        try:
          date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
          reservas[date_obj.strftime("%d/%m/%Y")] = reservas.pop(date_str)
        except ValueError:
          pass  # Se a data não puder ser convertida, ignore
      # Ordenar as reservas por data crescente
      reservas = dict(
          sorted(reservas.items(),
                 key=lambda item: datetime.datetime.strptime(
                     item[0], '%d/%m/%Y')))
      return reservas
  return {}


# Função para salvar os dados de reservas no arquivo
def save_reservas(reservas):
  # Ordenar as reservas por data crescente
  reservas = dict(
      sorted(reservas.items(),
             key=lambda item: datetime.datetime.strptime(item[0], '%d/%m/%Y')))
  # Salvar os dados de reservas no arquivo
  with open(DATA_FILE_PATH, 'w') as file:
    json.dump(reservas, file, indent=4)


def generate_dates():
  reservas = load_reservas()

  if not reservas:
    start_date = datetime.date(2023, 8, 2)
    end_date = datetime.date(2023, 8, 10)
  else:
    dates = [
        datetime.datetime.strptime(date_str, "%d/%m/%Y").date()
        for date_str in reservas.keys()
    ]
    start_date = min(dates)
    end_date = max(dates)

  current_date = max(end_date, datetime.date.today())
  end_date = current_date + datetime.timedelta(days=5)

  dates = []
  while current_date <= end_date:
    dates.append(current_date.strftime("%d/%m/%Y"))
    current_date += datetime.timedelta(days=1)

  return dates


def find_reserva_by_date(data_reserva, reservas):
  return reservas.get(data_reserva)


@app.route('/get_reservas', methods=['GET'])
def get_reservas():
  reservas = load_reservas()
  return jsonify({'reservas': reservas})


@app.route('/', methods=['GET', 'POST'])
def index():
  if request.method == 'POST':
    nome = request.form['nome']
    data_reserva = request.form['data_reserva']
    periodo = request.form['periodo']

    reservas = load_reservas()

    # Formatar a data para o formato 'dd/mm/aaaa'
    try:
      date_obj = datetime.datetime.strptime(data_reserva, "%Y-%m-%d").date()
      data_reserva = date_obj.strftime("%d/%m/%Y")
    except ValueError:
      return jsonify({'success': False, 'message': 'Data inválida!'})

    if data_reserva in reservas:
      # Adicionar a nova reserva à lista de reservas para essa data
      reservas[data_reserva].append({'nome': nome, 'periodo': periodo})
    else:
      # Se não houver reservas para essa data, criar uma lista com a nova reserva
      reservas[data_reserva] = [{'nome': nome, 'periodo': periodo}]

    save_reservas(reservas)

    # Ordenar as reservas novamente antes de retornar o template
    reservas = dict(
        sorted(
            reservas.items(),
            key=lambda item: datetime.datetime.strptime(item[0], '%d/%m/%Y')))

    dates = generate_dates()  # Atualizar as datas para incluir a nova reserva

    return render_template('index.html',
                           dates=dates,
                           reservas=reservas,
                           message='Reserva feita com sucesso!')

  dates = generate_dates()
  reservas = load_reservas()
  reservas = dict(
      sorted(reservas.items(),
             key=lambda item: datetime.datetime.strptime(item[0], '%d/%m/%Y')))

  return render_template('index.html',
                         dates=dates,
                         reservas=reservas,
                         message='')


@app.route('/delete', methods=['POST'])
def delete_reserva():
  if request.method == 'POST':
    data_reserva = request.form['data_reserva']
    nome = request.form.get('nome')  # Get the name from the form data

    # Carregar as reservas existentes
    reservas = load_reservas()

    # Verificar se a reserva para essa data existe
    if data_reserva in reservas:
      # Verificar se o nome do paciente também foi fornecido
      if nome:
        # Encontrar a reserva com o nome especificado e removê-la
        reservas[data_reserva] = [
            reserva for reserva in reservas[data_reserva]
            if reserva['nome'] != nome
        ]
      else:
        # Se o nome não foi fornecido, remover todas as reservas para essa data
        del reservas[data_reserva]

      # Salvar as reservas atualizadas
      save_reservas(reservas)

      # Retornar uma resposta JSON para a solicitação POST
      return jsonify({'success': True, 'reservas': reservas})
    else:
      return jsonify({
          'success': False,
          'message': 'A reserva para essa data não foi encontrada!'
      })


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080)
