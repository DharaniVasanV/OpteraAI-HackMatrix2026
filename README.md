# **OpteraAI**

## **A Multi-Agent AI Productivity Platform**

> One Dashboard. Multiple Intelligent Agents. Automated Workflows.

---


## **1. Team Details**

**Team Name:** Luminex

**Team Leader:** Dharani Vasan V

**Team Members:**
1. DHARANI VASAN V – Team Leader

2. MAHESWARA PANDIYAN A

3. SIVAGANESH B

4. SANTHOSH A P
---



## **2. Problem Statement**

Information is available in abundance through various sources like emails, meetings, internships, hackathons, certification, scholarships, job opportunities, and academics for the students and professionals.

The manual approach to handle all this information involves:

- Reading and organizing emails

- Identifying important opportunities

- Determining their priority

- Gathering relevant information

- Downloading and organizing documents

- Handling meetings

- Maintaining resumes

- Searching for additional information

- Applying for opportunities

- Managing calendars and reminders

- Tracking learning and career progression

Due to the fragmented approach, users end up spending a lot of time on such activities and can often fail to capture important opportunities or their respective deadlines.

Most of the productivity applications cater to individual tasks rather than an integrated solution that understands the information and performs all necessary workflows automatically.

---

## **3. Solution Overview**

OpteraAI is an integrated multi-agent AI productivity platform that intelligently converts the unstructured information into action items.

Post authentication using Google OAuth, OpteraAI can sync your Gmail account, classify the information coming in, set priorities, extract relevant information, process the documents, handle meetings, build your knowledge base, give you career & learning advice, automate applications, manage your calendar, notify you and deliver productivity metrics.
The platform utilizes different AI agents and each AI agent handles a specific task, but works together via API integrations and shared PostgreSQL database.

All the functionalities are available via a single unified dashboard and users don’t have to move around different agent dashboards.4

---

## **4. System Workflow**

                         Google OAuth
                              |
                              v
                     Unified Dashboard
                              |
                              v
                       Watcher Agent
                              |
                              v
                   Classification Agent
                              |
                              v
                       Priority Agent
                              |
                              v
                       Research Agent
                              |
              +---------------+---------------+
              |               |               |
              v               v               v
        Search Agent    Document Agent   Meeting Agent
              |               |               |
              +---------------+---------------+
                              |
                              v
                       Knowledge Agent
                              |
              +---------------+---------------+
              |               |               |
              v               v               v
         Career Agent   Learning Agent    Resume Agent
              |               |               |
              +---------------+---------------+
                              |
                              v
                    Application Agent
                              |
                              v
                      Calendar Agent
                              |
                              v
                   Notification Agent
                              |
                              v
                     Analytics Agent
                              |
                              v
                    Supervisor Agent
---

## **5. AI Agents**

OpteraAI is made up of 16 agents.


| No. | Agent | Primary Responsibility |

|----:|:------------------|:--------------------------------------------------------|

| 1 | Watcher Agent | Monitor and sync Gmail |

| 2 | Classification Agent | Classify incoming emails and information |

| 3 | Priority Agent | Prioritize emails and information |

| 4 | Research Agent | Parse unstructured info into structured format |

| 5 | Search Agent | Search and validate info on online sources |

| 6 | Document Agent | Download, process, classify and manage docs |

| 7 | Knowledge Agent | Provide RAG personal knowledge search |

| 8 | Meeting Agent | Automate meetings, generate transcripts and answer questions on behalf of user |

| 9 | Career Agent | Provide career guidance |

| 10 | Learning Agent | Create learning roadmap |

| 11 | Resume Agent | Resume management |

| 12 | Application Agent | Automate applications |

| 13 | Calendar Agent | Manage events, deadlines and schedule |

| 14 | Notification Agent | Intelligent notifications |

| 15 | Analytics Agent | Productivity analytics |

| 16 | Supervisor Agent | Agent health monitoring and workflow coordination |

---

## **6. Agent Responsibilities**


### **6.1 Watcher Agent**

Watcher Agent constantly monitors user’s Gmail.

Responsibilities:

- Synchronize Gmail

- Detect new emails

- Retrieve email content

- Retrieve email metadata

- Detect attachments

- Pass new information to downstream agents

### **6.2 Classification Agent**

The Classification Agent classifies the type of information received.

Example classifications:

- Internship
- Hackathon
- Job
- Meeting
- Certificate
- Scholarship
- Event
- Bill
- Academic information

Responsibilities:

- Email classification
- Category detection
- Classification confidence
- Assignment of processing workflow

### **6.3 Priority Agent**

The Priority Agent defines the priority of the information received.

Priority types:

- Emergency
- High
- Medium
- Low

Responsibilities:

- Deadline analysis
- Urgency detection
- Priority classification
- Priority score

### **6.4 Research Agent**

The Research Agent transforms unstructured data into structured information.

Information retrieved includes:

- Deadlines
- Tasks
- Meetings
- Application links
- Contacts
- Internship information
- Hackathon information
- Certificate information
- Instructions
- Summaries

### **6.5 Search Agent**

The Search Agent searches for information if there is not enough information provided.

Responsibilities:

- Searches on official websites
- Validates information
- Searches for missing information
- Finds URLs
- Downloads resources
- Gives extra information to the Research Agent

### **6.6 Document Agent**

The Document Agent deals with documents used by the platform.

Responsibilities:

- Downloads PDFs
- Downloads certificates
- Downloads and processes email attachments
- Extracts text from documents
- Processes PDF and DOCX files
- Documents categorization
- Stores document metadata
- Duplicate document detection
- Keeps track of documents
- Provides documents to other agents

Main consumers:

- Knowledge Agent
- Research Agent
- Career Agent
- Application Agent
- Resume Agent

### **6.7 Knowledge Agent**

The Knowledge Agent provides a personal RAG-based knowledge base.

RAG pipeline:

```text
Documents / Information
|
v
Text Extraction
|
v
Vector Embeddings
|
v
ChromaDB
|
v
User Query
|
v
Query Embedding
|
v
Cosine Similarity
|
v
Top-K Results
|
v
Groq API
|
v
AI Response
```

Responsibilities:

- Vector generation
- Vector storage
- Semantic search
- Retrieval of relevant information
- Answering queries contextually
- Providing sources

### 6.8 Meeting Agent
Meeting Agent is used for managing meeting workflows.
Tasks performed by this agent:
- Processing meeting links;
- Participating in supported online meetings;
- Recording meeting audio;
- Creating transcripts;
- Extracting actions;
- Storing meeting data;
- Generating meeting summaries.

### 6.9 Career Agent
Career Agent helps users in their careers.
Tasks performed by this agent:
- Resume analysis;
- Recommending career paths;
- Finding skills gaps;
- Recommending jobs;
- Recommending internships;
- Recommending certifications;
- Career roadmap creation.

### 6.10 Learning Agent
Learning Agent creates personalized learning plans for users.
Tasks performed by this agent:
- Planning the learning process;
- Recommending courses;
- Recommending projects;
- Recommending certifications;
- Planning skills development.

### 6.11 Resume Agent
Resume Agent manages users' resumes.
Tasks performed by this agent:
- Managing resumes masterly;
- Resumes updating;
- Versions of resumes;
- Making customized resumes;
- Optimizing resumes for ATS;
- Resumes creation;
- Resumes downloading.

### 6.12 Application Agent
This agent works with supported online applications.
Supported applications:
- Google Forms;
- Microsoft Forms.
Workflow:
```text
Opportunity
     |
     v
Application link
     |
     v
Application Agent
     |
     v
User Profile + Resume
     |
     v
Detect form fields
     |
     v
Fill required fields
     |
     v
Upload documents
     |
     v
Submit application
     |
     v
Store application status
```
This agent uses the data that is already stored in the user's profile and resume instead of making users fill the same data every time.

### 6.13 Calendar Agent
Calendar Agent is responsible for scheduling and tracking deadlines.
Tasks performed by this agent:
- Creating calendar events;
- Scheduling meetings;
- Tracking deadlines;
- Detecting scheduling conflicts;
- Scheduling reminders;
- Scheduling notifications;
- Updating events.

### 6.14 Notification Agent

Notification Agent works with scheduled notifications.

Functionality:

- Browser notifications

- Dashboard notifications

- Custom notification sounds

- Snooze

- Quiet hours

- Notification history

- Tracking delivery

- Notification preferences

### 6.15 Analytics Agent

Analytics Agent gives productivity insights.

Monitors:

- Number of emails processed

- Opportunities found

- Number of applications made

- Meetings

- Learning process

- Notifications

- Agents activity

Provides:

- Productivity dashboards

- Reports

- Statistics

- Insights of productivity

### 6.16 Supervisor Agent

Supervisor Agent monitors the whole multi-agent ecosystem.

Responsible for:

- Agents health monitoring

- Agents status monitoring

- Failures detection

- Workflow monitoring

- Errors tracking

- Service performance monitoring

- Agents coordination in their execution

---

## 7. Unified Dashboard

OpteraAI provides a unified dashboard which integrates all agents functionality.

User will never have to visit different agents dashboards.

Modules of unified dashboard:

1. Home

2. Inbox

3. Opportunities

4. Documents

5. Calendar

6. Meetings

7. Knowledge

8. Career

9. Learning

10. Resume

11. Applications

12. Notifications

13. Analytics

14. AI Agents

15. Settings

Unified dashboard provides access to:

- Gmail activities

- Email classification

- Priority information

- Information about extracted opportunities

- Document management

- Meetings information

- Personal knowledge search

- Career recommendations

- Learning roadmaps

- Resume management

- Application automation

- Calendar events

- Notifications

- Productivity analytics

- Agent health monitoring

---

## 8. Example End-to-End Workflow

Upon the receipt of the internship email:

When an internship email arrives:

```text
Gmail
  |
  v
Watcher Agent
  |
  v
Classification Agent
  |
  |--> Internship
  |
  v
Priority Agent
  |
  |--> High Priority
  |
  v
Research Agent
  |
  +--> Company
  +--> Role
  +--> Deadline
  +--> Skills
  +--> Application URL
  |
  +----------------------+
  |                      |
  v                      v
Search Agent         Document Agent
  |                      |
  v                      v
Verify Details       Process Files
  |                      |
  +----------+-----------+
             |
             v
      Unified Dashboard
             |
             v
      Application Agent
             |
             v
         Auto Fill
             |
             v
          Submit
             |
             v
       Calendar Agent
             |
             v
     Notification Agent
             |
             v
       Analytics Agent
```

---
## 9. Technology Stack
### 9.1 Frontend
- React.js
- Vite
- TypeScript
- Tailwind CSS
- shadcn/ui
- Lucide React
- Framer Motion
- Recharts
- Zustand
### 9.2 Backend
- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Uvicorn
- APScheduler
### 9.3 Database
- PostgreSQL
- Render PostgreSQL
### 9.4 AI & RAG
- Groq API
- Sentence Transformers
- Vector Embeddings
- Retrieval-Augmented Generation
- Cosine Similarity
- ChromaDB
### 9.5 Automation
- Playwright
### 9.6 Meetings Processing
- Whisper
- FFmpeg
- Playwright
### 9.7 Document Processing
- PyMuPDF
- pdfplumber
- python-docx
- OCR when needed
### 9.8 Authentication & Integration
- Google OAuth
- JWT
- Gmail API
### 9.9 Deployment
- Render
---


## **10. Authentication**

OpteraAI employs Google OAuth for its authentication process.

Login Process:

```text
Google OAuth
     |
     v
User Authentication
     |
     v
Create / Get User
     |
     v
Session / JWT
     |
     v
Unified Dashboard
```

Once authentication succeeds, the user will be redirected to the unified dashboard page.

---

## **11. Database**

PostgreSQL acts as the primary relational database for the application's data storage.

This database will manage data related to:

- Users
- Gmail accounts
- Emails
- Classifications
- Priorities
- Research findings
- Documents
- Meetings
- Resumes
- Applications
- Calendar events
- Notification jobs
- Notification history
- Careers
- Learning
- Analytics

The vector knowledge layer uses a separate system called ChromaDB.

---

## **12. Project Presentation and Demo**

**Live Demo:** https://drive.google.com/drive/folders/1cVyBKyX5FMpy2AnCwwitJmcTknelBWNu?usp=sharing

**Project Presentation (PPT):** https://drive.google.com/drive/folders/1jCI23z_xEA2_DDKTJCrwOWrJfKlKp4aN?usp=sharing

---

## **13. Setup Instructions**

### **13.1 Pre-requisites**

Before starting, please make sure you have the following installed on your machine:

- Python 3.10 and above
- Node.js 18 and above for Vite React frontend
- PostgreSQL, local or cloud-based

### **13.2 Backend (Microservices) Setup**

#### **Step 1: Clone Repository**

```bash
git clone https://github.com/DharaniVasanV/OpteraAI-HackMatrix2026
cd AgentOS
```

#### **Step 2: Setup Python virtual environment**

For Windows,

```powershell
python -m venv .venv
.venv\Scripts\activate
```

For Mac/Linux,

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### **Step 3: Install python dependencies**

```bash
pip install -r requirements.txt
```

#### **Step 4: Install Playwright browser binaries**

The Playwright Chromium is required for the Meeting and Filler agents.

```bash
playwright install chromium
```

#### **Step 5: Setup environment variables**

Create a new `.env` file from the `.env.example` or copy the `.env.example` to `.env`.

```bash
cp .env.example .
```
Ensure you fill out the critical variables in `.env`:

```env
DATABASE_URL=postgresql+asyncpg://<user>:<password>@localhost:5432/<db_name>

GROQ_API_KEY=your_groq_api_key
GROQ_API_KEY2=your_groq_api_key_2
GROQ_API_KEY3=your_groq_api_key_3

GEMINI_API_KEY=your_gemini_api_key

SMTP_USER=your_smtp_user
SMTP_PASSWORD=your_smtp_password

GROQ_API_KEY2, GROQ_API_KEY3, and other Groq keys should be defined for automatic key rotation when available from the application.
Gmail OAuth keys and SMTP credentials should also be defined based on the environmental settings of the project.
### 13.3 Frontend Setup
Enter the frontend folder and install the Node modules:
```bash
cd frontend
npm install
cd ..
```
### 13.4 Platform Execution
OpteraAI makes use of the unified startup script which enables the microservices, unified proxy, and React frontend to start up together.
Windows PowerShell:
```powershell
.\start_all.ps1
```
Mac/Linux:
```bash
chmod +x start_all.sh
./start_all.sh
```
### 13.5 Application Access
After the startup script has started all services, you will have to access the applications via the following URLs:
- Frontend Dashboard: http://localhost:3000
- Central API Gateway: http://127.0.0.1:9000/docs
- Database Logs/Traces: View the log output on the console where each microservice is reporting its status.
---
## 14. Team Members
| Role     | Name                         |
|----------|------------------------------|
| Team Lead| DHARANI VASAN V              |
| Team Member | MAHESWARA PANDIYAN A       |
| Team Member | SIVAGANESH B               |
| Team Member | SANTHOSH A P               |
---

## 15. Impact of Project

OpteraAI seeks to eliminate the repetitive tasks involved in managing opportunities for education and profession.

Traditional Workflow:

```text

Read -> Understand -> Prioritize -> Organize -> Apply -> Schedule -> Remember

```

OpteraAI Workflow:

```text
Read -> Understand -> Prioritize -> Organize -> Apply -> Schedule -> Remember
```

OpteraAI workflow:

```text
Receive
   |
   v
Understand
   |
   v
Prioritize
   |
   v
Extract
   |
   v
Organize
   |
   v
Act
   |
   v
Notify
   |
   v
Track
```
This will help users devote lesser time on administrative tasks and more on education, career, and productive activities.

---

## 16. Future Scope

Future improvements that could be considered include:

1. Mobile Application

2. More email providers

3. More meeting platforms

4. More application platforms

5. Agent Orchestration

6. Mobile Push Notifications

7. Multilingual Support

8. Enterprise Edition

9. Advance Career Matching

10. Advance Workflow Automation

---

## 17. License

Include license of the project here.

Example:

```text

MIT License

```

---

## 18. Acknowledgements

Open source tools and services used for development of the project include:

- Python

- FastAPI

- React

- PostgreSQL

- Playwright

- ChromaDB

- Sentence Transformers

- Whisper

- Groq API

- Google APIs

---

## 19. Project Objective

Objective of OpteraAI is to convert scattered academic and professional information into automated workflows.

The platform brings together AI agents, automation, information extraction, document processing, RAG based knowledge retrieval, scheduling, application automation and analytics in one productivity platform.

---

## 20. Conclusion

OpteraAI is a unified platform for management of academic and professional activities using AI agents.

Combining email intelligence, opportunity discovery, document processing, meetings, knowledge management, career development, learning, applications, scheduling, notifications and analytics, the platform allows users to manage workflows from one interface.

---

# OpteraAI

One Dashboard. Multiple Intelligent Agents. Automated Workflows.
