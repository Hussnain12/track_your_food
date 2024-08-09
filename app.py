from flask import Flask, render_template, g, request
from datetime import datetime
from database import connect_db, get_db
app = Flask(__name__)
app.config['DEBUG'] = True
#

def convert_pretty_date(date):
    d = datetime.strptime(date, '%Y%m%d')
    return datetime.strftime(d, '%B %d, %y')


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/', methods=['POST', 'GET'])
def index():
    db = connect_db()
    if request.method == 'POST':
        date = request.form['date']
        db_date = datetime.strptime(date, '%Y-%m-%d')
        format_time = datetime.strftime(db_date, '%Y%m%d')
        db.execute('insert into log_date (entry_date) values (?)',
                   [format_time])
        db.commit()
    cur = db.execute('''select log_date.entry_date, sum(food.protein) as protein, sum(food.carbohydrates) as carbohydrates, sum(food.fat) as fat, sum(food.calories) as calories 
                     from log_date 
                     left join food_date on food_date.log_date_id=log_date.id 
                     left join food on food.id=food_date.food_id GROUP BY log_date.id ORDER BY log_date.entry_date desc''')
    results = cur.fetchall()
    pretty_results = []
    for i in results:
        single_date = {}
        single_date['date'] = i['entry_date']
        single_date['entry_date'] = convert_pretty_date(str(i['entry_date']))
        single_date['protein'] = i['protein']
        single_date['carbohydrates'] = i['carbohydrates']
        single_date['fat'] = i['fat']
        single_date['calories'] = i['calories']
        pretty_results.append(single_date)
    return render_template('home.html', results=pretty_results)


@app.route('/view/<dates>', methods=['GET', 'POST'])
def view(dates):
    print(f"{dates} is dats")
    db = connect_db()
    cur = db.execute(
        'select id, entry_date from log_date where entry_date = ?', [dates])
    date_results = cur.fetchone()
    print(date_results, 'date results')

    if request.method == 'POST':
        db.execute('insert into food_date (food_id,log_date_id) values (?, ?)', [
                   request.form['food-select'], date_results['id']])
        db.commit()
    pretty_date = convert_pretty_date(str(date_results['entry_date']))
    cur = db.execute('select id,name from food')
    food_result = cur.fetchall()
    log_cur = db.execute(
        'select \
            food.name,food.protein,food.carbohydrates,food.fat,food.calories \
                from log_date \
                    join food_date on food_date.log_date_id = log_date.id \
                        join food on food.id = food_date.food_id \
                            where log_date.entry_date = ?', [dates])
    log_result = log_cur.fetchall()

    totals = {}
    totals['protein'] = 0
    totals['carbohydrates'] = 0
    totals['fat'] = 0
    totals['calories'] = 0
    for food in log_result:
        totals['protein'] += food['protein']
        totals['carbohydrates'] += food['carbohydrates']
        totals['fat'] += food['fat']
        totals['calories'] += food['calories']

    return render_template('day.html', date_result=pretty_date, foods=food_result, log_results=log_result, totals=totals, db_date=date_results['entry_date'])


@app.route('/food', methods=['POST', 'GET'])
def add_food():
    db = connect_db()
    if request.method == 'POST':
        food_name = request.form['food-name']
        protein = int(request.form['protein'])
        carbs = int(request.form['carbs'])
        fat = int(request.form['fat'])
        calories = protein*4+carbs*4+fat*9
        db.execute('insert into food (name, protein, carbohydrates, fat, calories) values (?, ?, ?, ?,?)', [
                   food_name, protein, carbs, fat, calories])
        db.commit()
        # return f'<h1>{food_name},{protein},{carbs},{fat}</h1>'
    cur = db.execute('select * from food')
    results = cur.fetchall()
    return render_template('add_food.html', food_list=results)


if __name__ == "__main":
    app.run(debug=True)
