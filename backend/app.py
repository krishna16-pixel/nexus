import json
import os
import re
import urllib.parse
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# ENVIRONMENT SETUP
# ==========================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not GROQ_API_KEY or not TAVILY_API_KEY:
    raise ValueError("Missing API Keys. Please set GROQ_API_KEY and TAVILY_API_KEY environment variables.")

# FastAPI Setup
api = FastAPI(title="Academic Research API")
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentState(BaseModel):
    question: str
    target_url: Optional[str] = None
    custom_instructions: Optional[str] = None
    queries: List[str] = []
    search_results: List[Dict] = []
    iterations: int = 0
    final_answer: str = ""
    references: Dict[int, Dict] = {}

class ResearchRequest(BaseModel):
    topic: str
    target_url: Optional[str] = None
    custom_instructions: Optional[str] = None

# Initialize Models and Tools
fast = ChatGroq(model="llama3-70b-8192", temperature=0.1, api_key=GROQ_API_KEY)
reasoning = ChatGroq(model="llama3-70b-8192", temperature=0.2, api_key=GROQ_API_KEY)
search_tool = TavilySearchResults(max_results=5, tavily_api_key=TAVILY_API_KEY)

def extract_domain(url: str) -> str:
    if not url: return ""
    if not url.startswith(('http://', 'https://')): url = 'https://' + url
    return urllib.parse.urlparse(url).netloc

def generate_html_report(text: str, references: Dict, topic: str) -> str:
    """Parses charts and citations to generate a beautiful interactive HTML report."""
    for key, ref in references.items():
        if ref.get('url'):
            link = f'<a href="{ref["url"]}" target="_blank" style="text-decoration:none; color:#1a73e8; font-weight:bold;">[{key}]</a>'
            text = re.sub(rf'\[\s*{key}\s*\]', link, text)

    html_parts = []
    parts = re.split(r'<chart>\s*(.*?)\s*</chart>', text, flags=re.DOTALL)
    
    for i, part in enumerate(parts):
        if i % 2 == 0:
            part = part.replace('\n', '<br>')
            part = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', part)
            part = re.sub(r'### (.*?)<br>', r'<h3>\1</h3>', part)
            html_parts.append(f'<div style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 10px 20px;">{part}</div>')
        else:
            try:
                chart_data = json.loads(part.strip())
                chart_type = chart_data.get("type", "bar").lower()
                if chart_type == "gauge":
                    val = float(chart_data.get("value", 0))
                    fig = go.Figure(go.Indicator(mode="gauge+number", value=val, title={'text': chart_data.get("title")}))
                else:
                    df = pd.DataFrame({"Category": chart_data.get("labels", []), "Value": [float(v) for v in chart_data.get("values", [])]})
                    if chart_type == "pie": fig = px.pie(df, values="Value", names="Category", title=chart_data.get("title"), hole=0.4)
                    elif chart_type == "bar": fig = px.bar(df, x="Category", y="Value", title=chart_data.get("title"), color="Category")
                    elif chart_type == "line": fig = px.line(df, x="Category", y="Value", title=chart_data.get("title"), markers=True)
                    elif chart_type == "windrose": fig = px.bar_polar(df, r="Value", theta="Category", color="Category", title=chart_data.get("title"), template="plotly_white")
                    else: fig = None
                if fig:
                    fig.update_layout(margin=dict(t=50, b=20, l=10, r=10), height=450)
                    chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
                    html_parts.append(f'<div style="max-width: 900px; margin: 30px auto; border: 1px solid #eee; border-radius: 8px; padding: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">{chart_html}</div>')
            except Exception as e:
                html_parts.append(f'<div style="color: red;">[Chart Error: {e}]</div>')

    return f'''
    <!DOCTYPE html><html><head><script src="https://cdn.plot.ly/plotly-latest.min.js"></script></head>
    <body><h1 style="text-align:center;">Research Report: {topic}</h1>{"".join(html_parts)}</body></html>
    '''

def plan_research_node(state: AgentState) -> Dict:
    custom_directive = f"\nInstructions: {state.custom_instructions}" if state.custom_instructions else ""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Return ONLY JSON: {{\"queries\": [\"query1\", \"query2\"]}}"),
        ("human", f"Generate 3 search queries: {{question}}{custom_directive}")
    ])
    response = (prompt | fast).invoke({"question": state.question})
    try:
        queries = json.loads(response.content).get("queries", [state.question])
    except:
        queries = [state.question]
    return {"queries": queries, "iterations": 1}

def execute_search_node(state: AgentState) -> Dict:
    batch_results = []
    domain = extract_domain(state.target_url)
    for query in state.queries:
        search_query = f"{query} site:{domain}" if domain else query
        results = search_tool.invoke({"query": search_query})
        batch_results.append(results)
    
    seen = {res["url"] for res in state.search_results}
    new_results = list(state.search_results)
    for batch in batch_results:
        for item in batch:
            if item.get("url") not in seen:
                seen.add(item["url"])
                new_results.append(item)
    return {"search_results": new_results}

def evaluate_research_node(state: AgentState) -> str:
    return "finalize" if state.iterations >= 2 else "continue"

def continue_research_node(state: AgentState) -> Dict:
    return {"queries": [state.question + " statistics"], "iterations": state.iterations + 1}

def finalize_answer_node(state: AgentState) -> Dict:
    formatted_context = "\n---\n".join([f"SOURCE [{i}]\n{res.get('content', '')[:1000]}" for i, res in enumerate(state.search_results[:10], start=1)])
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert professor. Write a deep-dive report with citations [1], HTML <mark>yellow highlights</mark>, and 5 plotly charts inside <chart></chart> tags."),
        ("human", "Research: {question}\nSources: {context}")
    ])
    response = (prompt | reasoning).invoke({"context": formatted_context, "question": state.question})
    return {"final_answer": response.content}

workflow = StateGraph(AgentState)
workflow.add_node("planner", plan_research_node)
workflow.add_node("search_engine", execute_search_node)
workflow.add_node("continue_research", continue_research_node)
workflow.add_node("finalizer", finalize_answer_node)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "search_engine")
workflow.add_conditional_edges("search_engine", evaluate_research_node, {"continue": "continue_research", "finalize": "finalizer"})
workflow.add_edge("continue_research", "search_engine")
workflow.add_edge("finalizer", END)
graph_app = workflow.compile()

@api.post("/research")
async def perform_research(request: ResearchRequest):
    try:
        final_state = graph_app.invoke({
            "question": request.topic,
            "target_url": request.target_url,
            "custom_instructions": request.custom_instructions
        })
        
        references = {i: {"title": res.get("title"), "url": res.get("url")} for i, res in enumerate(final_state.get("search_results", [])[:10], start=1)}
        html_report = generate_html_report(final_state["final_answer"], references, request.topic)
        
        return {"report_html": html_report, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=8000)
