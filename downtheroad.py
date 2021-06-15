# MAKE NOTES A LATER OPTION

##############################################################
#              routes for notes                              #
##############################################################

####     All Trail Notes            ######
@app.route('/users/<int:user_id>/trails/<int:trail_id>/notes', methods=['GET'])
def get_trail_notes(trail_id):
    '''Get all notes for a trail'''

    notes = Note.query.filter(Note.trail_id==trail_id).all()
    noteList = [{"id": note.id, 
                "comment": note.comment,
                "timestamp": note.timestamp,
                "trail_id": trail_id} for note in notes]
        
    return jsonify(noteList)
    

####     Add Note to Trail           ######
@app.route('/users/<int:user_id>/trails/<int:trail_id>/notes', methods=['POST'])
def add_trail_note(trail_id):
    '''Add a note to a trail'''
    comment = request.json['comment']
    note = Note(comment=comment, trail_id=trail_id)
    db.session.add(note)
    db.session.commit()
    response = jsonify(note={"id": note.id, "comment": note.comment,
                "timestamp": note.timestamp, "trail_id": note.trail_id})
    
    return (response, 201);


####     Delete Trail Note         ######
@app.route('/users/<int:user_id>/trails/<int:trail_id>/notes/<int:note_id>', methods=['DELETE'])
def delete_note(trail_id, note_id):
    '''Delete a note'''
    note = Note.query.filter(Note.id==note_id, Note.trail_id==trail_id).one_or_none()
    db.session.delete(note)
    db.session.commit()

    return jsonify(message="deleted")