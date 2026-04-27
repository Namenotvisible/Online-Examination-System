import cv2

# 1. Load the built-in OpenCV Face Detector 
# (This is hardcoded into OpenCV, so it never fails on M1 Macs)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# 2. Turn on the Webcam
cap = cv2.VideoCapture(0)

print("AI Proctor Running... Press ESC to stop.")

while cap.isOpened():
    success, image = cap.read()
    if not success:
        continue

    # AI processes black & white video much faster than color
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 3. Detect faces in the frame
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    face_count = len(faces)

    # Draw a blue box around any faces found
    for (x, y, w, h) in faces:
        cv2.rectangle(image, (x, y), (x+w, y+h), (255, 0, 0), 2)

    # 4. Threat Mitigation Logic (Your Project Core)
    if face_count == 0:
        cv2.putText(image, "WARNING: No Student Detected!", (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
    elif face_count > 1:
        cv2.putText(image, "WARNING: Multiple People Detected!", (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
    else:
        cv2.putText(image, "Status: Secure. One Student.", (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Show the live security feed
    cv2.imshow('AI Exam Proctor - Security Feed', image)

    # Listen for the 'ESC' key to quit the program safely
    if cv2.waitKey(5) & 0xFF == 27:
        break

# Shut down the camera when done
cap.release()
cv2.destroyAllWindows()