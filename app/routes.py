import Championship

from flask import render_template, request, redirect
from app import app

@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/championships")
@app.route("/championship")
def championship():
    game = [{"name":"Example", "number":1}]
    ### TODO: get available championships for the user
    return render_template("championship.html", championships=game)

@app.route("/new_champ")
def new_champ():
    return render_template("new_champ.html")

@app.route("/create_champ", methods=["POST"])
def create_champ():
    champ, champ_id = Championship.createChamp(request.form["type"])
    for num in range((len(request.form)-1)//2):
        champ.add_player(request.form["player_"+str(num)], request.form["num_"+str(num)])
    champ.next_round()
    Championship.save_champ(champ)
    return redirect("/championship/"+str(champ_id))

@app.route("/championship/<champ_num>")
def championships(champ_num):
    champ = Championship.load_champ(champ_num)
    if champ is None:
        return redirect("/championship")
    if (champ.pairings == []):
        return render_template("finished_championship.html", champ = champ)
    return render_template("current_championship.html", champ = champ)


@app.route("/process_champ/<champ_num>", methods=["POST"])
def process_champs(champ_num):
    champ = Championship.load_champ(champ_num)
    if not champ:
        return redirect("/championship/"+champ_num)
    for match in champ.pairings:
        champ.match_result(match[0], match[1], (int(request.form["player_"+str(match[0])]), int(request.form["player_"+str(match[1])])))
    champ.next_round()
    if champ.finished:
        return redirect("/championship/"+champ_num)
    if (champ.pairings == []):
        champ.finished = True
    Championship.save_champ(champ)
    return redirect("/championship/"+champ_num)
    
@app.route("/championship/<champ_num>/results")
def results(champ_num):
    champ = Championship.load_champ(champ_num)
    result = champ.get_result()
    return render_template("results.html", champ=champ, result=result)

@app.route("/login")
def login():
    return render_template("login.html")