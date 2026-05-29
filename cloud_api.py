import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SmartResume Mobile API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SENDER_EMAIL = os.environ.get("EMAIL_ADDRESS", "")
SENDER_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD", "")
SENDER_NAME = os.environ.get("SENDER_NAME", "Pradeep Kumar Ramadoss")
STANDARD_DRAFT = os.environ.get(
    "STANDARD_DRAFT",
    "Hi [Recruiter Name],\n\nI am writing to express my interest in the [Role Name] role which I recently viewed on LinkedIn. "
    "With over 14 years of experience in the Banking and Finance domain specialising in business analysis, data analysis, "
    "financial analysis, and process automation, I believe this role matches my experience and skill set.\n\n"
    "Please find my resume attached for your review. I would appreciate the opportunity to discuss my qualifications "
    "in more detail during a call at your convenience.\n\n"
    "Current Location: Dallas, Texas\nVisa Status: H1B (Valid until Sep 2028)\n\n"
    "Best regards,\nPradeep Kumar Ramadoss\n+1 682-436-4050\nPradeepkumar089@gmail.com"
)


def extract_role_name(text: str) -> str:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return "the position"
    labels = ["Job Title:", "Position Title:", "Role:", "Position:", "Job Title -"]
    for line in lines[:5]:
        for label in labels:
            if line.startswith(label):
                return line[len(label):].strip().split("  ")[0].strip()
    keywords = ["Analyst", "Manager", "Lead", "Architect", "Engineer", "Developer",
                "Specialist", "Consultant", "Director", "Coordinator", "Administrator"]
    for line in lines[:2]:
        if any(kw.lower() in line.lower() for kw in keywords) and len(line.split()) <= 10:
            return line.strip()
    return "the position"


@app.get("/")
def health():
    configured = bool(SENDER_EMAIL and SENDER_PASSWORD)
    # Show all env var keys that don't look like system secrets (for debugging)
    user_keys = [k for k in os.environ.keys() if not k.startswith(("PATH", "HOME", "USER", "PYTHON", "PIP", "VIRTUAL"))]
    return {
        "status": "running",
        "email_configured": configured,
        "visible_env_keys": sorted(user_keys),
    }


@app.post("/mobile-send")
async def mobile_send(
    recruiter_email: str = Form(...),
    recruiter_name: str = Form(""),
    jd_text: str = Form(""),
    email_body: str = Form(""),
    resume: UploadFile = File(...),
):
    """
    Single endpoint for the iOS Shortcut.
    Accepts multipart form data: recruiter email, optional JD text, optional
    pre-written body, and the resume file. Generates the email body from the
    standard draft if none is supplied, then sends via Gmail SMTP.
    """
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        raise HTTPException(status_code=500, detail="Email credentials not configured on server")

    # Build email body from standard draft if caller didn't supply one
    if not email_body:
        role_name = extract_role_name(jd_text) if jd_text else "the position"
        name_placeholder = recruiter_name if recruiter_name else "Hiring Manager"
        email_body = (
            STANDARD_DRAFT
            .replace("[Recruiter Name]", name_placeholder)
            .replace("[Role Name]", role_name)
        )

    resume_data = await resume.read()
    resume_name = resume.filename or "Resume.docx"

    try:
        msg = MIMEMultipart()
        msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg["To"] = recruiter_email
        msg["Subject"] = f"Application for Position - {SENDER_NAME}"
        msg.attach(MIMEText(email_body, "plain"))

        part = MIMEBase("application", "octet-stream")
        part.set_payload(resume_data)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{resume_name}"')
        msg.attach(part)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "success", "message": f"Email sent to {recruiter_email}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8002)))
