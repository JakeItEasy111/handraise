from flask import Flask, Response, request, jsonify
from flask_cors import CORS
import queue 

app = Flask(__name__)
CORS(app, supports_credentials=True) # Allows requests from other apps 

#teachers visit /classrooms/<class_id>/stream 
classrooms = {
        "test" : { 
            "name": "Class 101",
            "teacher_queues" : [], #subscribers, where signals are sent 
            "students": [], #connected students information 
            "signals" : [], 
        }, 
    }

signal_types = {
            "pencil" : "I need a sharpened pencil",
            "water" : "I need to get water",
            "tissue" : "I need a tissue",
            "restroom" : "I need to use the restroom",
            "emergency" : "There's an emergency.",
            "question" : "I have a question",
            "sick" : "I am not feeling well.",
            "move" : "I want to move seats"
        }

# --- GET data ---

# Teacher: GET class info  
@app.route("/classrooms/<class_id>")
def get_class(class_id): #Path parameter 
    if class_id not in classrooms:
        return "Classroom not found", 404
    
    class_data = classrooms[class_id].copy()
    class_data.pop("teacher_queues", None)  # remove queues before sending JSON
    return jsonify(class_data), 200

@app.route("/classrooms/<class_id>/students")
def get_students(class_id):
    if class_id not in classrooms:
        return "Classroom not found", 404
    
    return jsonify(classrooms[class_id]["students"]), 200 

@app.route("/classrooms/<class_id>/signals")
def get_signals(class_id):
    if class_id not in classrooms:
        return "Classroom not found", 404
    
    return jsonify(classrooms[class_id]["signals"]), 200 

@app.route("/signal-types")
def get_signal_types():
    return jsonify(signal_types), 200 

# Teacher: POST classroom
@app.route("/classrooms/<class_id>/create", methods = ["POST"])
def create_classroom(class_id): 
    data = request.get_json()

    if class_id in classrooms:
        return "Class already exists", 409
    
    classrooms[class_id] = {
        "name": data["name"], #for UI 
        "teacher_queues" : [], #subscribers, where signals are sent 
        "students": [], #connected students 
        "signals" : []
    }

    class_data = classrooms[class_id].copy()
    class_data.pop("teacher_queues", None)  # remove queues before sending JSON
    return jsonify(class_data), 201

# Student: POST student  
@app.route("/classrooms/<class_id>/join", methods = ["POST"])
def join_classroom(class_id):
    if class_id not in classrooms:
        return "Classroom not found", 404

    data = request.get_json()

    name = data.get("name")

    if not name:
        return "Name required", 400
    
    if name in classrooms[class_id]["students"]:
        return "Student already in class", 400

    classrooms[class_id]["students"].append(name) 

    return jsonify(classrooms[class_id]["students"]), 201 

# Student: POST transmit signal 
@app.route("/classrooms/<class_id>/signal", methods = ["POST"])
def send_signal(class_id):
    if class_id not in classrooms:
        return "Classroom not found", 404

    data = request.get_json()
    student = data.get("name")
    signal_type = data.get("signal_type")

    if signal_type not in signal_types:
        return "Cannot send that kind of signal", 404 
    
    text = signal_types[signal_type]
    msg = f"{student}: {text}"

    classrooms[class_id]["signals"].append(msg)

    for q in classrooms[class_id]["teacher_queues"]:
        q.put(msg)

    return {"status" : "sent"}, 201

# --- DELETE ---

# Teacher: Waive signal 
@app.route("/classrooms/<class_id>/signal/remove", methods = ["DELETE"])
def remove_signal_from_queue(class_id):
    if class_id not in classrooms:
        return "Classroom not found", 404
    
    data = request.get_json()
    signal = data["signal"]
    signals = classrooms[class_id]["signals"]

    if signal in signals:
        signals.remove(signal) 
    return jsonify(signals), 200

# Student: Leave classroom 
@app.route("/classrooms/<class_id>/leave", methods = ["DELETE"])
def remove_student(class_id):
    if class_id not in classrooms:
        return "Classroom not found", 404
    
    data = request.get_json() 
    name = data["name"]

    classrooms[class_id]["students"].remove(name) 

    return {"deleted" : name}, 200

# --- STREAM --- 

# Teachers: Connect and stay connected for signals 
@app.route("/classrooms/<class_id>/stream")
def classroom_stream(class_id):
    if class_id not in classrooms:
        return "Classroom not found", 404

    q = queue.Queue()
    classrooms[class_id]["teacher_queues"].append(q)

    def event_stream(q):
        yield b"data: connected\n\n"  # <- string, not bytes

        try:
            while True:
                msg = q.get()
                yield f"data: {msg}\n\n"
        except GeneratorExit:
            classrooms[class_id]["teacher_queues"].remove(q)
            print(f"Teacher disconnected from {class_id}")

    return Response(event_stream(q), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(debug=True, threaded=True)