player_num = 0

function add_player(){
	var newFields = document.getElementById('player_stuff').cloneNode(true);
    newFields.id = '';
    newFields.style.display = "block";
	var newField = newFields.childNodes;
	for (var i=0;i<newField.length;i++) {
		var theName = newField[i].name
		if (theName)
			newField[i].name = theName + player_num;
	}
	var insertHere = document.getElementById('new_players');
    insertHere.parentNode.insertBefore(newFields,insertHere);
    player_num++;
    document.getElementById("player_num").innerHTML = "Number of players: "+player_num
}