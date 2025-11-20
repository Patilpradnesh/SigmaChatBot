# SigmaChatBot – Real Estate Analysis Chatbot  
A full-stack AI-driven chatbot that analyzes real-estate data and provides insights such as location analysis, price trends, demand trends, and comparison between areas.  
This project was developed as part of the Sigmavalue Full Stack Developer Assignment 2025.

---

## 🚀 Features
### **Chatbot Capabilities**
- Analyze any location:  
  **“Analyze Wakad”**
- Show price growth for the last N years:  
  **“Show price growth for Akurdi over last 3 years”**
- Compare two locations:  
  **“Compare Aundh and Baner”**
- Show demand trend:  
  **“Show demand trend for Hinjewadi”**
- List available places  
  **“List places”**

### **UI Features**
- Interactive Chat UI
- Right-side visualization panel:
  - Price Trend Chart
  - Demand Trend Chart
  - Comparison Chart
  - Detailed Table View  
- Quick-action suggested prompts (ChatGPT-style)
- Responsive layout (Vite + Tailwind)

---

## 🏗 Tech Stack

### **Frontend**
- React (Vite)
- TailwindCSS
- Recharts (graphs)
- Deployed on **Vercel**

### **Backend**
- Django + Django REST Framework
- Pandas + OpenPyXL for data processing
- Gunicorn (production)
- Whitenoise (static files)
- CORS Headers enabled
- Deployed to **Render**

### **Dataset**
- Excel file containing real-estate statistics  
  (kept inside: `backend/dataset/realestate.xlsx`)

---

## 📁 Project Structure

SigmaChatBot
├── backend
│   ├── api
│   ├── dataset
│   ├── realestate
│   ├── requirements.txt
│   ├── Procfile
│   └── runtime.txt
└── frontend
    ├── src
    │   ├── components
    │   ├── App.jsx
    │   └── main.jsx
    ├── index.css
    └── package.json



## 🛠 How to Run Locally

### **Backend**
```bash
cd backend
pip install -r requirements.txt
python manage.py runserver

Frontend
cd frontend
npm install
npm run dev


🌐 Deployment URLs

Backend (Render):
https://your-backend-url.onrender.com

Frontend (Vercel):
https://your-frontend-url.vercel.app
