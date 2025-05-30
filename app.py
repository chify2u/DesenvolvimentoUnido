from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector

app = Flask(__name__)
app.secret_key = 'some_secret_key'


def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='alunolab',
        database='teste',
        port=3303
    )
    return connection


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cpf = request.form['cpf']
        senha = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_usuario, senha FROM usuarios WHERE CPF = %s", (cpf,))
        user = cursor.fetchone()
        if user and user[1] == senha:
            session['user_id'] = user[0]
            return redirect(url_for('index'))
        else:
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/index')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/esqueceuSenha')
def senha():
    return render_template('esqueceuSenha.html')


@app.route('/esqueceuSenha2')
def senha2():
    return render_template('esqueceuSenha2.html')


@app.route('/cadastro1', methods=['GET', 'POST'])
def cadastro1():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        cpf = request.form['cpf']
        senha = request.form['password']
        data_nascimento = request.form['dataNascimento']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO usuarios (Nome, email, CPF, senha, data_nascimento)
                          VALUES (%s, %s, %s, %s, %s)''', (nome, email, cpf, senha, data_nascimento))
        conn.commit()
        cursor.close()
        conn.close()
        session['email'] = email
        return redirect(url_for('cadastro2'))

    return render_template('cadastro1.html')


@app.route('/cadastro2', methods=['GET', 'POST'])
def cadastro2():
    if request.method == 'POST':
        estado_civil = request.form['estadoCivil']
        escolaridade = request.form['escolaridade']
        cep = request.form['cep']
        bairro = request.form['bairro']
        cidade = request.form['cidade']
        estado = request.form['estado']

        email = session.get('email')
        if not email:
            return redirect(url_for('cadastro1'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''UPDATE usuarios 
                              SET estado_civil = %s, escolaridade = %s
                              WHERE email = %s''', (estado_civil, escolaridade, email))
            cursor.execute('''INSERT INTO endereco (cep, bairro, cidade, estado, fk_usuarios_id_usuario)
                              VALUES (%s, %s, %s, %s, (SELECT id_usuario FROM usuarios WHERE email = %s))
                              ON DUPLICATE KEY UPDATE 
                              cep = VALUES(cep), bairro = VALUES(bairro), cidade = VALUES(cidade), estado = VALUES(estado)''',
                           (cep, bairro, cidade, estado, email))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('login'))
        except mysql.connector.Error:
            return redirect(url_for('cadastro2'))

    return render_template('cadastro2.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/canal', methods=['GET', 'POST'])
def canal():
    if request.method == 'POST':
        community_needs = request.form['community-needs']
        employment = request.form['employment']
        education = request.form['education']
        healthcare = request.form['healthcare']
        internet = request.form['internet']
        housing = request.form['housing']

        user_id = session.get('user_id')
        if not user_id:
            return redirect(url_for('login'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO respostas_socioeconomicas (fk_usuarios_id_usuario, infraestrutura, oportunidades_emprego, qualidade_ensino, acesso_saude, internet, housing)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (user_id, community_needs, employment, education, healthcare, internet, housing))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('index'))

    return render_template('canal.html')


@app.route('/submeter_ideia', methods=['GET', 'POST'])
def submeter_ideia():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        descricao = request.form['descricao']
        tipo_acao = request.form['tipo_acao']

        user_id = session.get('user_id')
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO acoes (descricao, tipo_acao)
            VALUES (%s, %s)
        ''', (descricao, tipo_acao))
        action_id = cursor.lastrowid
        cursor.execute(''' 
            UPDATE usuarios
            SET fk_acoes_id_acao = %s
            WHERE id_usuario = %s
        ''', (action_id, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('ideias'))

    return render_template('submeter_ideia.html')


@app.route('/ideias', methods=['GET', 'POST'])
def ideias():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    
    
    cursor.execute("SELECT Nome FROM usuarios WHERE id_usuario = %s", (session['user_id'],))
    user = cursor.fetchone()
    nome_usuario = user['Nome'] if user else "Usuário Desconhecido"
    
    if request.method == 'POST':
       

        nome_ideia = request.form['nome-ideia']  
        tipo_ideia = request.form['tipo-ideia'] 
        descricao_ideia = request.form['descricao-ideia'] 
        
     
        cursor.execute(''' 
            INSERT INTO acoes (nome, descricao, tipo_acao, fk_usuario_id_usuario)
            VALUES (%s, %s, %s, %s)
        ''', (nome_ideia, descricao_ideia, tipo_ideia, session['user_id']))

        conn.commit()

        return redirect(url_for('ideias'))

    
    cursor.execute(''' 
        SELECT acoes.id_acao, acoes.nome, acoes.descricao, acoes.tipo_acao, usuarios.Nome
        FROM acoes
        LEFT JOIN usuarios ON usuarios.id_usuario = acoes.fk_usuario_id_usuario
    ''')

    ideias = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('ideias.html', ideias=ideias, nome_usuario=nome_usuario)

@app.route('/inovacao')
def inovacao():
    return render_template('inovacao.html')


if __name__ == '__main__':
    app.run(debug=True, port=5000)
