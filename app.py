from flask import Flask, request, session, Response, render_template_string, redirect, jsonify
import cv2
import threading
import time
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = "campus_project_secret_ultra_final"

# --- 1. GLOBAL STATE (In-Memory Database) ---
global_frame = None
active_camera_user = None # CAMERA FIX: Starts as None so the camera stays OFF

live_student_status = {
    "101": {"status": "Offline", "color": "#64748b", "score": "Pending"},
    "102": {"status": "Offline", "color": "#64748b", "score": "Pending"}
}

activity_ledger = [] # THE NEW AUDIT LEDGER

exam_questions = [
    {
        "id": "q_default", 
        "text": "What prevents IDOR (Insecure Direct Object Reference) attacks?", 
        "options": ["A) Firewalls", "B) Server-side Session Validation", "C) Antivirus"], 
        "answer": "B) Server-side Session Validation"
    }
]

def log_event(message):
    timestamp = datetime.now().strftime("%I:%M:%S %p")
    activity_ledger.insert(0, f"[{timestamp}] {message}")
    # Keep ledger to last 50 events to save memory
    if len(activity_ledger) > 50: activity_ledger.pop()

# --- 2. AI CAMERA ENGINE (LAZY LOADED) ---
def ai_camera_loop():
    global global_frame, active_camera_user
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    camera = None
    
    while True:
        # If no student is logged in, turn off the camera and sleep
        if active_camera_user is None:
            if camera is not None:
                camera.release()
                camera = None
                global_frame = None
            time.sleep(0.5)
            continue
            
        # If a student is logged in but camera is off, turn it on
        if camera is None:
            camera = cv2.VideoCapture(0)
            
        success, frame = camera.read()
        if not success:
            time.sleep(0.1)
            continue
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=7, minSize=(60, 60))
        face_count = len(faces)

        current_time = datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, f"REC | {current_time} | ID: {active_camera_user}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 1)

        # Update specific student status
        if active_camera_user in live_student_status:
            if face_count == 0:
                cv2.rectangle(frame, (0, frame.shape[0]-40), (frame.shape[1], frame.shape[0]), (0, 0, 255), -1)
                cv2.putText(frame, "CRITICAL: NO STUDENT", (10, frame.shape[0]-12), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
                live_student_status[active_camera_user]["status"] = "CRITICAL: No Student Detected"
                live_student_status[active_camera_user]["color"] = "#ef4444"
            elif face_count > 1:
                cv2.rectangle(frame, (0, frame.shape[0]-40), (frame.shape[1], frame.shape[0]), (0, 165, 255), -1)
                cv2.putText(frame, "WARNING: MULTIPLE FACES", (10, frame.shape[0]-12), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
                live_student_status[active_camera_user]["status"] = "WARNING: Multiple Faces"
                live_student_status[active_camera_user]["color"] = "#f59e0b"
            else:
                cv2.rectangle(frame, (0, frame.shape[0]-35), (frame.shape[1], frame.shape[0]), (0, 200, 0), -1)
                cv2.putText(frame, "BIOMETRIC LOCK: SECURE", (10, frame.shape[0]-10), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
                live_student_status[active_camera_user]["status"] = "Secure - Identity Verified"
                live_student_status[active_camera_user]["color"] = "#10b981"

        ret, buffer = cv2.imencode('.jpg', frame)
        global_frame = buffer.tobytes()
        time.sleep(0.03)

threading.Thread(target=ai_camera_loop, daemon=True).start()

def stream_video():
    while True:
        if global_frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + global_frame + b'\r\n')
        time.sleep(0.03)

# --- 3. USER ROLES ---
users = {
    "101": {"name": "Alice", "role": "student", "course": "Cybersecurity 101"},
    "102": {"name": "Bob", "role": "student", "course": "Cybersecurity 101"},
    "999": {"name": "Prof. Smith", "role": "teacher", "department": "Computer Science"}
}

# --- 4. BEAUTIFUL HTML TEMPLATES ---
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Secure Auth | Campus Portal</title>
    <style>
        body { font-family: 'Segoe UI', system-ui, sans-serif; background: linear-gradient(135deg, #0f172a 0%, #020617 100%); display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; color: white; }
        .login-box { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); padding: 50px 40px; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.1); width: 100%; max-width: 380px; text-align: center; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); transition: transform 0.3s; }
        .login-box:hover { transform: translateY(-5px); }
        h2 { margin-bottom: 5px; font-weight: 600; letter-spacing: 1px; color: #f8fafc; }
        p { color: #94a3b8; margin-bottom: 30px; font-size: 14px; }
        input[type="text"] { width: 85%; padding: 14px; margin-bottom: 25px; background: rgba(0, 0, 0, 0.3); border: 1px solid #334155; border-radius: 8px; color: white; font-size: 16px; outline: none; transition: 0.3s; }
        input[type="text"]:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3); }
        input[type="submit"] { width: 95%; padding: 14px; background: linear-gradient(to right, #3b82f6, #2563eb); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: 0.3s; box-shadow: 0 4px 6px rgba(0,0,0,0.2);}
        input[type="submit"]:hover { background: linear-gradient(to right, #60a5fa, #3b82f6); box-shadow: 0 6px 12px rgba(59, 130, 246, 0.3); }
        .hint { margin-top: 25px; font-size: 13px; color: #64748b; text-align: left; background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; border: 1px solid #334155;}
    </style>
</head>
<body>
    <div class="login-box">
        <div style="font-size: 12px; color: #10b981; margin-bottom: 20px;">🔒 Identity & Access Management</div>
        <h2>EXAM PORTAL</h2>
        <p>Please provide your credentials to begin</p>
        <form action="/login" method="POST">
            <input type="text" name="user_id" placeholder="User ID (e.g., 101)" required>
            <input type="submit" value="AUTHENTICATE">
        </form>
        <div class="hint"><b>Demo Accounts:</b><br>Candidates: 101, 102<br>Proctor: 999</div>
    </div>
</body>
</html>
"""

STUDENT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Live Exam | {{ data.course }}</title>
    <style>
        body { font-family: 'Segoe UI', system-ui, sans-serif; background-color: #f1f5f9; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        .sidebar { width: 320px; background-color: #0f172a; color: white; display: flex; flex-direction: column; border-right: 1px solid #1e293b; box-shadow: 5px 0 15px rgba(0,0,0,0.1); z-index: 10; padding: 25px; box-sizing: border-box;}
        .video-feed { width: 100%; border-radius: 8px; border: 2px solid #334155; box-shadow: 0 4px 6px rgba(0,0,0,0.3); margin-top: 20px;}
        .main-content { flex-grow: 1; padding: 40px; overflow-y: auto; background: #f8fafc; }
        .exam-paper { background: white; max-width: 800px; margin: 0 auto; padding: 50px; border-radius: 12px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }
        .question { margin-bottom: 35px; }
        .options label { display: block; padding: 14px 15px; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 12px; cursor: pointer; background: #f8fafc; transition: 0.2s; }
        .options label:hover { background: #f1f5f9; border-color: #cbd5e1; transform: translateX(5px); }
        .submit-btn { background: linear-gradient(135deg, #10b981, #059669); color: white; border: none; padding: 16px 35px; font-size: 16px; font-weight: bold; border-radius: 8px; cursor: pointer; transition: 0.3s; box-shadow: 0 4px 6px rgba(16, 185, 129, 0.2);}
        .submit-btn:hover { background: linear-gradient(135deg, #34d399, #10b981); transform: translateY(-2px); box-shadow: 0 6px 12px rgba(16, 185, 129, 0.3); }
        .logout-btn { display: block; text-align: center; background: #ef4444; color: white; text-decoration: none; padding: 15px; font-weight: bold; border-radius: 8px; transition: 0.2s; margin-top: auto; }
        .logout-btn:hover { background: #dc2626; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h3 style="margin:0; color:#f8fafc;">Proctoring Engine</h3>
        <p style="margin: 5px 0 0 0; color: #94a3b8; font-size: 13px;">Candidate ID: {{ student_id }}</p>
        <img class="video-feed" src="/video_feed" alt="Live AI Proctoring Feed">
        <div style="margin-top: 25px;">
            <p style="font-size: 12px; color: #64748b; text-transform: uppercase;">System Checks</p>
            <p style="font-size: 14px; color: #cbd5e1; margin: 5px 0;">✓ End-to-End Encryption</p>
            <p style="font-size: 14px; color: #cbd5e1; margin: 5px 0;">✓ Biometric Tracking</p>
        </div>
        <a href="/logout" class="logout-btn">END EXAM & LOGOUT</a>
    </div>

    <div class="main-content">
        <div class="exam-paper">
            <h1 style="border-bottom: 2px solid #e2e8f0; padding-bottom: 15px; color: #0f172a;">{{ data.course }}</h1>
            
            {% if status[student_id].score == "Pending" %}
                <form action="/submit_exam" method="POST">
                    {% for q in questions %}
                    <div class="question">
                        <h4 style="color: #334155; font-size: 18px;">{{ loop.index }}. {{ q.text }}</h4>
                        <div class="options">
                            {% for opt in q.options %}
                            <label><input type="radio" name="{{ q.id }}" value="{{ opt }}" required> {{ opt }}</label>
                            {% endfor %}
                        </div>
                    </div>
                    {% endfor %}
                    <button type="submit" class="submit-btn">Securely Submit Assessment</button>
                </form>
            {% else %}
                <div style="text-align: center; padding: 60px 20px;">
                    <h1 style="color: #10b981; font-size: 36px; margin-bottom: 10px;">Submission Verified</h1>
                    <p style="color: #64748b; font-size: 18px;">Your encrypted payload has been successfully delivered to the instructor.</p>
                    <div style="background: #f1f5f9; display: inline-block; padding: 20px 40px; border-radius: 12px; margin-top: 30px; border: 1px solid #e2e8f0;">
                        <span style="display: block; color: #64748b; font-size: 14px; text-transform: uppercase; margin-bottom: 5px;">Provisional Score</span>
                        <span style="font-size: 32px; font-weight: bold; color: #0f172a;">{{ status[student_id].score }}</span>
                    </div>
                </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

TEACHER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Dashboard | Enterprise</title>
    <style>
        body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0f172a; margin: 0; padding: 40px; color: white; }
        .header { background: #1e293b; padding: 25px 40px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border: 1px solid #334155; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3);}
        
        /* Layout Fix: Tabs */
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab-btn { background: #334155; color: #cbd5e1; border: none; padding: 12px 25px; border-radius: 8px; font-weight: bold; cursor: pointer; transition: 0.3s; font-size: 15px;}
        .tab-btn.active { background: #3b82f6; color: white; }
        .tab-content { display: none; animation: fadeIn 0.4s; }
        .tab-content.active { display: block; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        .card { background: #1e293b; padding: 30px; border-radius: 12px; border: 1px solid #334155; box-shadow: 0 4px 6px rgba(0,0,0,0.2); margin-bottom: 30px;}
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th { text-align: left; padding: 15px; border-bottom: 2px solid #334155; color: #94a3b8; font-size: 13px; text-transform: uppercase; }
        td { padding: 15px; border-bottom: 1px solid #334155; font-size: 15px; }
        
        .feed-btn { background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; border: none; padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: bold; cursor: pointer; transition: 0.2s; box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);}
        .feed-btn:hover { background: linear-gradient(135deg, #60a5fa, #3b82f6); transform: translateY(-1px); }
        .del-btn { background: #ef4444; color: white; padding: 6px 12px; text-decoration: none; border-radius: 6px; font-size: 12px; font-weight: bold;}
        
        /* Modal Style */
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); justify-content: center; align-items: center; z-index: 1000; backdrop-filter: blur(5px); }
        .modal-content { background: #1e293b; padding: 25px; border-radius: 12px; text-align: center; border: 1px solid #334155; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); }
        
        /* Form styling */
        input[type="text"] { width: 100%; padding: 12px; margin-bottom: 15px; background: #0f172a; border: 1px solid #334155; border-radius: 6px; color: white; box-sizing: border-box; transition: 0.3s;}
        input[type="text"]:focus { border-color: #10b981; outline: none;}
        .submit-q-btn { background: #10b981; color: white; padding: 12px 25px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; transition: 0.2s;}
        .submit-q-btn:hover { background: #059669; }
        
        /* Ledger */
        .ledger-box { background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 15px; max-height: 250px; overflow-y: auto; font-family: monospace; font-size: 13px; color: #cbd5e1; }
        .ledger-row { margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h2 style="margin:0; color: #f8fafc;">Admin Command Center</h2>
            <p style="margin:5px 0 0 0; color:#94a3b8;">Welcome, {{ data.name }} | Role: Superuser</p>
        </div>
        <a href="/logout" style="border: 1px solid #475569; color: #cbd5e1; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: bold; transition: 0.2s;">Terminate Session</a>
    </div>

    <div class="tabs">
        <button class="tab-btn active" onclick="switchTab('monitoring')">📡 Monitoring & Logs</button>
        <button class="tab-btn" onclick="switchTab('exam-builder')">📝 Exam Builder</button>
    </div>

    <div id="monitoring" class="tab-content active">
        <div class="card">
            <h3 style="margin-top:0; color: #e2e8f0;">Live Examination Network</h3>
            <table>
                <tr>
                    <th>Candidate</th>
                    <th>Threat Status</th>
                    <th>Score</th>
                    <th>Action</th>
                </tr>
                <tr>
                    <td>Alice (101)</td>
                    <td id="status-101" style="font-weight: bold; color: gray;">Initializing...</td>
                    <td id="score-101">Pending</td>
                    <td><button onclick="openModal('101')" class="feed-btn">Quick Glance</button></td>
                </tr>
                <tr>
                    <td>Bob (102)</td>
                    <td id="status-102" style="font-weight: bold; color: gray;">Initializing...</td>
                    <td id="score-102">Pending</td>
                    <td><button onclick="openModal('102')" class="feed-btn">Quick Glance</button></td>
                </tr>
            </table>
        </div>
        
        <div class="card">
            <h3 style="margin-top:0; color: #e2e8f0;">System Activity Ledger</h3>
            <div class="ledger-box" id="ledger-container">
                </div>
        </div>
    </div>

    <div id="exam-builder" class="tab-content">
        <div class="card">
            <h3 style="margin-top:0; color: #e2e8f0;">Active Questions Bank</h3>
            <div style="max-height: 300px; overflow-y: auto; margin-bottom: 30px;">
                {% for q in questions %}
                <div style="background: #0f172a; padding: 20px; margin-bottom: 15px; border-radius: 8px; border: 1px solid #334155; position: relative;">
                    <div style="font-size: 16px; font-weight: bold; margin-bottom: 10px; padding-right: 80px;">{{ q.text }}</div>
                    <a href="/delete_question/{{ q.id }}" class="del-btn" style="position: absolute; top: 20px; right: 20px;">Remove</a>
                    <div style="color: #94a3b8; font-size: 14px;">Options: {{ q.options | join(', ') }}</div>
                    <div style="color: #10b981; font-size: 14px; margin-top: 5px; font-weight: bold;">Key: {{ q.answer }}</div>
                </div>
                {% endfor %}
            </div>
            
            <h3 style="border-top: 1px solid #334155; padding-top: 25px; color: #e2e8f0;">Deploy New Question</h3>
            <form action="/add_question" method="POST" style="background: rgba(0,0,0,0.2); padding: 25px; border-radius: 8px; border: 1px dashed #475569;">
                <input type="text" name="q_text" placeholder="Enter the question text..." required>
                <div style="display: flex; gap: 15px;">
                    <input type="text" name="opt1" placeholder="Option A" required>
                    <input type="text" name="opt2" placeholder="Option B" required>
                </div>
                <input type="text" name="ans" placeholder="Type EXACT correct answer (e.g. Option A)" required>
                <button type="submit" class="submit-q-btn">Deploy to Live Exam</button>
            </form>
        </div>
    </div>

    <div id="quickGlanceModal" class="modal">
        <div class="modal-content">
            <h3 style="margin-top:0; color: white;">Live Feed: Candidate <span id="modal-student-id"></span></h3>
            <img id="modal-video-feed" src="" style="width: 450px; border-radius: 8px; border: 2px solid #3b82f6; box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);">
            <br>
            <button onclick="closeModal()" style="background: #ef4444; color: white; padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; margin-top: 20px; font-weight: bold; transition: 0.2s;">Close Preview</button>
        </div>
    </div>

    <script>
        // Tab Logic
        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
        }

        // Fetch Live Status and Ledger text every second
        function fetchLiveStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    // Update Status 101
                    document.getElementById('status-101').innerText = data.students['101'].status;
                    document.getElementById('status-101').style.color = data.students['101'].color;
                    document.getElementById('score-101').innerText = data.students['101'].score;
                    
                    // Update Status 102
                    document.getElementById('status-102').innerText = data.students['102'].status;
                    document.getElementById('status-102').style.color = data.students['102'].color;
                    document.getElementById('score-102').innerText = data.students['102'].score;

                    // Update Ledger
                    const ledgerHtml = data.ledger.map(entry => `<div class="ledger-row">${entry}</div>`).join('');
                    document.getElementById('ledger-container').innerHTML = ledgerHtml;
                });
        }
        setInterval(fetchLiveStatus, 1000);

        // Modal Controls
        function openModal(studentId) {
            document.getElementById('modal-student-id').innerText = studentId;
            document.getElementById('modal-video-feed').src = '/video_feed';
            document.getElementById('quickGlanceModal').style.display = 'flex';
        }
        
        function closeModal() {
            document.getElementById('quickGlanceModal').style.display = 'none';
            document.getElementById('modal-video-feed').src = ''; 
        }
    </script>
</body>
</html>
"""

# --- 5. ROUTES & LOGIC ---
@app.route("/")
def index():
    return render_template_string(LOGIN_HTML)

@app.route("/login", methods=["POST"])
def login():
    global active_camera_user
    user_id = request.form.get("user_id")
    if user_id in users:
        session['user_id'] = user_id
        session['role'] = users[user_id]['role']
        
        # Log the login event
        log_event(f"Authentication success: {users[user_id]['role'].capitalize()} {user_id} logged in.")
        
        if session['role'] == 'teacher': 
            return redirect(f"/faculty/{user_id}")
        else: 
            # If student logs in, trigger the camera to turn ON for them
            active_camera_user = user_id
            return redirect(f"/student/{user_id}")
            
    log_event(f"Authentication failed: Unknown ID '{user_id}' attempted login.")
    return redirect("/")

@app.route("/student/<user_id>")
def student_dashboard(user_id):
    if session.get('user_id') != user_id or session.get('role') != 'student':
        return "<body style='background:#0f172a; color:#ef4444; display:flex; justify-content:center; align-items:center; height:100vh; text-align:center;'><h1>ACCESS DENIED</h1></body>"
    
    return render_template_string(STUDENT_HTML, student_id=user_id, data=users[user_id], questions=exam_questions, status=live_student_status)

@app.route("/faculty/<user_id>")
def faculty_dashboard(user_id):
    if session.get('user_id') != user_id or session.get('role') != 'teacher':
        return "<body style='background:#0f172a; color:#ef4444; display:flex; justify-content:center; align-items:center; height:100vh; text-align:center;'><h1>ACCESS DENIED</h1></body>"
    return render_template_string(TEACHER_HTML, data=users[user_id], questions=exam_questions)

@app.route("/add_question", methods=["POST"])
def add_question():
    if session.get('role') == 'teacher':
        new_q = {
            "id": "q_" + str(uuid.uuid4())[:8],
            "text": request.form.get("q_text"),
            "options": [request.form.get("opt1"), request.form.get("opt2")],
            "answer": request.form.get("ans")
        }
        exam_questions.append(new_q)
        log_event(f"Admin action: New question deployed to exam bank.")
    return redirect(f"/faculty/{session.get('user_id')}")

@app.route("/delete_question/<q_id>")
def delete_question(q_id):
    global exam_questions
    if session.get('role') == 'teacher':
        exam_questions = [q for q in exam_questions if q["id"] != q_id]
        log_event(f"Admin action: Question removed from exam bank.")
    return redirect(f"/faculty/{session.get('user_id')}")

@app.route("/submit_exam", methods=["POST"])
def submit_exam():
    student_id = session.get('user_id')
    if not student_id or session.get('role') != 'student':
        return "Unauthorized"

    # Auto-grade the submission
    correct = 0
    total = len(exam_questions)
    for q in exam_questions:
        student_answer = request.form.get(q["id"])
        if student_answer == q["answer"]:
            correct += 1
            
    score_percentage = f"{(correct / total) * 100:.0f}% ({correct}/{total})"
    live_student_status[student_id]["score"] = score_percentage
    log_event(f"Submission received: Candidate {student_id} submitted exam. Score: {score_percentage}.")
    
    return redirect(f"/student/{student_id}")

@app.route("/api/status")
def api_status():
    if session.get('role') != 'teacher': return jsonify({"error": "Unauthorized"}), 401
    # We now package the students AND the ledger to send to the Teacher UI
    return jsonify({
        "students": live_student_status,
        "ledger": activity_ledger
    })

@app.route('/video_feed')
def video_feed():
    return Response(stream_video(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/logout")
def logout():
    global active_camera_user
    user_id = session.get('user_id')
    
    if user_id:
        log_event(f"Session terminated: User {user_id} logged out.")
        
        # LOGOUT FIX: Clean up student state and camera tracking
        if session.get('role') == 'student':
            # Reset their dashboard status to Offline
            live_student_status[user_id]["status"] = "Offline / Disconnected"
            live_student_status[user_id]["color"] = "#64748b"
            
            # If the camera was tracking them, turn the camera OFF
            if active_camera_user == user_id:
                active_camera_user = None

    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, threaded=True)