import json
import os
import re
import urllib.parse
import webbrowser
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph

# ==========================================
# ENVIRONMENT SETUP
# ==========================================
# Ensure you have set these environment variables before running
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not GROQ_API_KEY or not TAVILY_API_KEY:
    print("\033[91mError: Missing API Keys. Please set GROQ_API_KEY and TAVILY_API_KEY environment variables.\033[0m")
    exit(1)

class AgentState(BaseModel):
    question: str
    target_url: Optional[str] = None  # Added for the website connector feature
    custom_instructions: Optional[str] = None  # Added for custom user directives
    queries: List[str] = []
    search_results: List[Dict] = []
    iterations: int = 0
    final_answer: str = ""
    references: Dict[int, Dict] = {}

# Initialize Models and Tools
# Using 70b or 8b depending on your Groq access (updated model string to a standard Groq model for reliability)
fast = ChatGroq(model="llama3-70b-8192", temperature=0.1, api_key=GROQ_API_KEY)
reasoning = ChatGroq(model="llama3-70b-8192", temperature=0.2, api_key=GROQ_API_KEY)
search_tool = TavilySearchResults(max_results=5, tavily_api_key=TAVILY_API_KEY)

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def extract_domain(url: str) -> str:
    """Extracts the base domain from a provided URL to use with the site: operator."""
    if not url:
        return ""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return urllib.parse.urlparse(url).netloc

def format_console_output(text: str) -> str:
    """Replaces HTML <mark> tags with ANSI Yellow color for terminal output."""
    # ANSI escape code for bright yellow is \033[93m and reset is \033[0m
    text = re.sub(r'<mark>(.*?)</mark>', r'\033[93m\1\033[0m', text, flags=re.IGNORECASE)
    return text

def strip_charts_for_console(text: str) -> str:
    """Removes the JSON chart data from the text so the console output reads cleanly."""
    return re.sub(r'<chart>.*?</chart>', '\n\033[96m[Interactive Plotly Chart generated in HTML Report]\033[0m\n', text, flags=re.DOTALL)

def generate_html_report(text: str, references: Dict, topic: str) -> str:
    """Parses charts and citations to generate a beautiful interactive HTML report."""
    # 1. Replace citations with clickable links
    for key, ref in references.items():
        if ref.get('url'):
            link = f'<a href="{ref["url"]}" target="_blank" style="text-decoration:none; color:#1a73e8; font-weight:bold;">[{key}]</a>'
            text = re.sub(rf'\[\s*{key}\s*\]', link, text)

    # 2. Extract and render charts
    html_parts = []
    parts = re.split(r'<chart>\s*(.*?)\s*</chart>', text, flags=re.DOTALL)
    
    for i, part in enumerate(parts):
        if i % 2 == 0:
            # Format text: basic markdown to HTML
            part = part.replace('\n', '<br>')
            part = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', part)
            part = re.sub(r'### (.*?)<br>', r'<h3>\1</h3>', part)
            part = re.sub(r'## (.*?)<br>', r'<h2>\1</h2>', part)
            part = re.sub(r'# (.*?)<br>', r'<h1>\1</h1>', part)
            html_parts.append(f'<div style="font-family: Arial, sans-serif; line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 10px 20px;">{part}</div>')
        else:
            # It's a chart, render with Plotly
            try:
                chart_data = json.loads(part.strip())
                chart_type = chart_data.get("type", "bar").lower()
                
                if chart_type == "gauge":
                    val = float(chart_data.get("value", 0))
                    max_range = 100 if val <= 100 else val * 1.5
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=val,
                        title={'text': chart_data.get("title", "Gauge Chart")},
                        gauge={'axis': {'range': [None, max_range]}}
                    ))
                else:
                    df = pd.DataFrame({
                        "Category": chart_data.get("labels", []),
                        "Value": [float(v) for v in chart_data.get("values", [])]
                    })
                    if chart_type == "pie":
                        fig = px.pie(df, values="Value", names="Category", title=chart_data.get("title"), hole=0.4)
                    elif chart_type == "bar":
                        fig = px.bar(df, x="Category", y="Value", title=chart_data.get("title"), color="Category")
                    elif chart_type == "line":
                        fig = px.line(df, x="Category", y="Value", title=chart_data.get("title"), markers=True)
                    elif chart_type == "windrose":
                        fig = px.bar_polar(df, r="Value", theta="Category", color="Category", title=chart_data.get("title"), template="plotly_white")
                    else:
                        fig = None
                
                if fig:
                    fig.update_layout(margin=dict(t=50, b=20, l=10, r=10), height=450)
                    chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
                    html_parts.append(f'<div style="max-width: 900px; margin: 30px auto; border: 1px solid #eee; border-radius: 8px; padding: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">{chart_html}</div>')
            except Exception as e:
                html_parts.append(f'<div style="color: red; max-width: 900px; margin: 0 auto;">[Chart Rendering Error: {e}]</div>')

    full_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Research Report: {topic}</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{ background-color: #f8f9fa; color: #333; margin: 0; padding: 20px; }}
            mark {{ background-color: #ffe066; padding: 2px 4px; border-radius: 3px; font-weight: 500; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; font-family: Arial, sans-serif; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #0d233a; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1 style="text-align: center; font-family: Arial, sans-serif; color: #0d233a; margin-top: 40px;">Research Report: {topic}</h1>
        {"".join(html_parts)}
        <div style="font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; border-top: 2px solid #ddd;">
            <h2 style="color: #0d233a;">Documented Source Registry</h2>
            <ul style="line-height: 1.8;">
    '''
    for key in sorted(references.keys()):
        ref = references[key]
        full_html += f'<li><strong>[{key}]</strong> <a href="{ref.get("url", "#")}" target="_blank" style="color: #1a73e8; text-decoration: none;">{ref.get("title", "Source")}</a></li>\n'
        
    full_html += '''
            </ul>
        </div>
    </body>
    </html>
    '''
    return full_html

# ==========================================
# GRAPH NODES
# ==========================================
def plan_research_node(state: AgentState) -> Dict:
    custom_directive = f"\nKeep in mind the user's custom instructions: {state.custom_instructions}" if getattr(state, "custom_instructions", None) else ""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Return ONLY JSON: {{\"queries\": [\"query1\", \"query2\"]}}"),
        ("human", f"Generate 3 distinct search queries to thoroughly research: {{question}}{custom_directive}")
    ])
    planner = prompt | fast
    response = planner.invoke({"question": state.question})
    try:
        result = json.loads(response.content)
        queries = result.get("queries", [state.question])
    except:
        queries = [state.question, state.question + " statistics data", state.question + " market trends"]
    return {"queries": queries, "iterations": 1}

def execute_search_node(state: AgentState) -> Dict:
    batch_results = []
    domain = extract_domain(state.target_url)
    
    for query in state.queries:
        # If a target URL is provided, restrict the search to that specific domain
        search_query = f"{query} site:{domain}" if domain else query
        print(f"[*] Executing Search: {search_query}")
        try:
            results = search_tool.invoke({"query": search_query})
            batch_results.append(results)
        except Exception as e:
            print(f"[!] Search failed for query '{search_query}': {e}")
            batch_results.append([])
    
    seen_urls = {res["url"] for res in state.search_results}
    new_results = list(state.search_results)
    
    for results in batch_results:
        if not isinstance(results, list):
            continue
        for item in results:
            if item.get("url") not in seen_urls:
                seen_urls.add(item["url"])
                new_results.append(item)
    
    return {"search_results": new_results}

def evaluate_research_node(state: AgentState) -> Literal["finalize", "continue"]:
    if state.iterations >= 3 or len(state.search_results) >= 10:
        return "finalize"
    return "continue"

def continue_research_node(state: AgentState) -> Dict:
    return {
        "queries": [state.question + " data analytics empirical statistics figures"],
        "iterations": state.iterations + 1
    }

def finalize_answer_node(state: AgentState) -> Dict:
    formatted_context = []
    references = {}
    
    print(f"[*] Synthesizing final report from {min(len(state.search_results), 15)} sources...")
    
    for idx, res in enumerate(state.search_results[:15], start=1):
        references[idx] = {"title": res.get("title", f"Source {idx}"), "url": res.get("url", "")}
        content = res.get("content", "")[:1200] 
        formatted_context.append(f"SOURCE [{idx}]\nTitle: {res.get('title', '')}\nContent: {content}\n")
    
    context_str = "\n---\n".join(formatted_context)
    
    custom_directive = f"\n\nUSER CUSTOM INSTRUCTIONS (PRIORITY):\n{state.custom_instructions}\nEnsure you adapt your tone, focus, and content to satisfy these specific instructions while maintaining the core structural requirements below." if getattr(state, "custom_instructions", None) else ""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an expert university-level research professor. Write an exhaustive academic "
            "deep-dive report using the provided sources. Do not summarize or cut corners."
            f"{custom_directive}\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. INLINE CITATIONS (WORKING LINKS): You MUST use inline citations at the end of relevant sentences using the source index provided. "
            "For example: 'The data indicates a 20% growth [1].' or 'Multiple sources agree on this metric [2][4].'\n"
            "2. YELLOW HIGHLIGHTING: You MUST highlight crucial important points, key takeaways, and critical metrics by wrapping them "
            "in HTML mark tags. For example: <mark>This is a highly critical finding that changed the industry</mark>.\n"
            "3. VISUALS (5 PLOTLY CHARTS REQUIRED): You must generate exactly FIVE data charts to support your analysis.\n"
            "   - You MUST use all 5 of these distinct chart types exactly once: 'bar', 'pie', 'line', 'gauge', and 'windrose'. Do not repeat types.\n"
            "   - Intelligently select which chart fits the specific data you are referencing.\n"
            "   - Format for bar/pie/line/windrose:\n"
            "     <chart>{{\"title\": \"Chart Title\", \"type\": \"bar\", \"labels\": [\"A\", \"B\"], \"values\": [10, 20]}}</chart>\n"
            "   - Format for gauge ONLY:\n"
            "     <chart>{{\"title\": \"Score\", \"type\": \"gauge\", \"value\": 85}}</chart>\n"
            "   - Output this exact JSON structure wrapped strictly inside <chart></chart> tags. DO NOT use markdown code blocks like ```json inside the tags.\n"
            "4. STRUCTURE: Must follow this exact outline:\n"
            "   - Abstract & Executive Introduction\n"
            "   - Historical Framework & Literature Review (Include exactly ONE Markdown Table here evaluating data)\n"
            "   - Comprehensive Analytical Deep-Dive\n"
            "   - Statistical Insights (Include your 5 charts well-spaced throughout this and previous sections)\n"
            "   - Final Summary (4-5 high-impact bullet points)\n\n"
            "Sources:\n{context}"
        )),
        ("human", "Compile the detailed academic portfolio evaluating: {question}")
    ])
    
    synthesizer = prompt | reasoning
    response = synthesizer.invoke({"context": context_str, "question": state.question})
    
    return {"final_answer": response.content, "references": references}

# ==========================================
# WORKFLOW DEFINITION
# ==========================================
workflow = StateGraph(AgentState)
workflow.add_node("planner", plan_research_node)
workflow.add_node("search_engine", execute_search_node)
workflow.add_node("continue_research", continue_research_node)
workflow.add_node("finalizer", finalize_answer_node)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "search_engine")
workflow.add_conditional_edges(
    "search_engine",
    evaluate_research_node,
    {"continue": "continue_research", "finalize": "finalizer"}
)
workflow.add_edge("continue_research", "search_engine")
workflow.add_edge("finalizer", END)

app = workflow.compile()

# ==========================================
# CLI APPLICATION
# ==========================================
def main():
    print("\n" + "="*60)
    print(" 🎓 ACADEMIC DEEP-RESEARCH & ANALYTICS ENGINE (CLI)")
    print("="*60)
    
    research_topic = input("\n[?] Enter your Research Topic Identifier:\n> ").strip()
    if not research_topic:
        print("\n\033[91mError: Research topic is required to proceed.\033[0m")
        return

    print("\n[?] Enter a specific Website URL to restrict the search to (Optional, press Enter to search the whole web):")
    target_url = input("> ").strip()
    
    if target_url:
        print(f"\n[*] Connector Active: Searches will be restricted to domain -> {extract_domain(target_url)}")
    else:
        print("\n[*] Connector Inactive: Searching the entire internet.")
        
    print("\n[?] Enter any custom instructions for the report (Optional, e.g., 'Focus only on the economic impact', 'Write in a casual tone', or press Enter to skip):")
    custom_instructions = input("> ").strip()
        
    print("\n[*] Initializing analytical engine. Please wait (this may take 30-60 seconds)...\n")
    
    try:
        # Run the graph
        final_state = app.invoke({
            "question": research_topic, 
            "target_url": target_url if target_url else None,
            "custom_instructions": custom_instructions if custom_instructions else None
        })
        
        output_text = final_state.get("final_answer", "")
        references = final_state.get("references", {})
        
        # Prepare and colorize the text for the terminal
        clean_text = strip_charts_for_console(output_text)
        colored_output = format_console_output(clean_text)
        
        print("\n" + "="*60)
        print(" 📖 COMPREHENSIVE LITERARY MANUSCRIPT")
        print("="*60 + "\n")
        
        print(colored_output)
        
        print("\n" + "="*60)
        print(" 🌐 DOCUMENTED SOURCE REGISTRY")
        print("="*60 + "\n")
        
        for key in sorted(references.keys()):
            ref = references[key]
            print(f"[{key}] {ref['title']}")
            if ref.get('url'):
                print(f"    URL: {ref['url']}\n")
                
        # Save to interactive HTML file with working links and Plotly graphs
        html_filename = "research_report.html"
        html_content = generate_html_report(output_text, references, research_topic)
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(html_content)
                
        print(f"\n[*] Success! A fully interactive report has been saved to '{html_filename}'.")
        print("[*] Note: Important points are highlighted yellow, citations are clickable links, and all 5 Plotly charts are interactive.")
        print("[*] Automatically opening the report in your web browser...")
        
        try:
            webbrowser.open('file://' + os.path.realpath(html_filename))
        except Exception as e:
            print(f"[!] Could not auto-open browser: {e}")
        
    except Exception as e:
        print(f"\n\033[91m[!] Pipeline Interruption: {str(e)}\033[0m")

if __name__ == "__main__":
    main()
