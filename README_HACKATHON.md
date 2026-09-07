# SkillBridge AI — Hackathon Upgrade

## New vertical slice

Resume PDF -> Alibaba Cloud Qwen skill extraction -> live job market -> market-aware skill gap -> personalized roadmap -> current job matches.

### New backend modules
- `backend/ai_service.py`
- `backend/resume_parser.py`
- `backend/job_market.py`
- `backend/market_pipeline.py`

### Setup
Install requirements:
```bash
pip install -r requirements.txt
```

Set your Alibaba Cloud Model Studio API key. Windows CMD:
```cmd
set DASHSCOPE_API_KEY=YOUR_API_KEY
```

Optional:
```cmd
set DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
set DASHSCOPE_MODEL=qwen-plus
```

Run:
```bash
uvicorn backend.main:app --reload
streamlit run frontend/frontend.py
```

Never commit the API key.
