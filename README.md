# Secure Online Examination & AI Proctoring System

## Overview
A multithreaded Flask-based assessment platform engineered to secure the digital examination ecosystem. This system features real-time MediaPipe computer vision proctoring, achieving ~95% frontal face detection accuracy while optimizing CPU load via a lazy-loading architecture[cite: 1, 2]. Designed with a privacy-first approach, the platform utilizes strict Defense-in-Depth controls to neutralize common web vulnerabilities (STRIDE) and protect academic integrity[cite: 4].

## Core Features & Security Controls

*   **Real-Time Biometric Proctoring:** The system utilizes a threaded AI Engine for real-time facial recognition[cite: 4]. It captures the student's live camera feed, routing it to the admin dashboard, and issues automatic warnings when multiple faces or no face is detected.
*   **Lazy-Loading Optimization:** The architecture implements "lazy-loading" for the AI camera threads[cite: 4]. These computing resources are only activated upon a successful, authenticated student handshake, which mitigates Denial of Service (DoS) risks and minimizes server-side CPU load[cite: 1, 4].
*   **IDOR Mitigation & Session Validation:** The server cryptographically verifies the user's `session_id` against their requested resource before serving any video data[cite: 4]. This neutralizes Insecure Direct Object Reference (IDOR) vulnerabilities, strictly preventing students from modifying URLs to intercept peer webcam feeds[cite: 4].
*   **Role-Based Access Control (RBAC):** Backend routing logic features hardcoded privilege separation[cite: 4]. This permanently isolates the Candidate interface (standard privileges) from the Proctor command center (elevated privileges), effectively mitigating Elevation of Privilege (EoP) attacks[cite: 4].
*   **Immutable System Ledgers:** The application deploys timestamped, append-only audit logs[cite: 4]. These securely record all user authentications, exam submissions, and AI-triggered threat alerts to ensure non-repudiation and maintain a reliable system audit trail[cite: 4].

## System Architecture

The platform operates on a centralized Client-Server Architecture separated by a strict trust boundary[cite: 4]:
1.  **In-Transit Security:** Data crosses the trust boundary via HTTPS/TLS 1.3 encryption (Port 443) to prevent data interception[cite: 4].
2.  **Server-Side Processing:** A backend Web Server routes traffic, verifies secure session cookies, and connects to the Persistent Database[cite: 4].
3.  **Proctoring Engine:** The independent AI Engine continuously analyzes student behavior and feeds data back to the secure validation server[cite: 4].

## Tech Stack
*   **Backend:** Python, Flask
*   **Computer Vision:** MediaPipe, OpenCV
*   **Concurrency:** Python Multithreading
*   **Frontend:** HTML/CSS, JavaScript

## Installation & Setup

1. **Clone the repository:**
```bash
   git clone [https://github.com/Namenotvisible/Online-Examination-System.git]
   cd Online-Examination-System
