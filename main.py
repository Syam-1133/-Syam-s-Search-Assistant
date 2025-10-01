import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.utilities import ArxivAPIWrapper, WikipediaAPIWrapper
from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun, DuckDuckGoSearchRun
from langchain.agents import create_react_agent, AgentExecutor
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from langchain import hub
import os
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Syam's Search Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .chat-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
    }
    .assistant-message {
        background: white;
        color: #333;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        max-width: 80%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .source-link {
        color: #667eea;
        text-decoration: none;
        font-size: 0.9rem;
        margin: 5px 0;
        display: block;
    }
    .source-link:hover {
        text-decoration: underline;
    }
    .thinking-bubble {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 10px 15px;
        margin: 5px 0;
        border-radius: 4px;
        font-style: italic;
        color: #555;
    }
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 10px 20px;
        font-weight: 600;
    }
    .sources-section {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        margin-top: 15px;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# Initialize tools with enhanced configuration
@st.cache_resource
def initialize_tools():
    arxiv_wrapper = ArxivAPIWrapper(top_k_results=3, doc_content_chars_max=500)
    arxiv = ArxivQueryRun(api_wrapper=arxiv_wrapper)

    wikipedia_wrapper = WikipediaAPIWrapper(top_k_results=3, doc_content_chars_max=500)
    wiki = WikipediaQueryRun(api_wrapper=wikipedia_wrapper)

    search = DuckDuckGoSearchRun(name="WebSearch")
    
    return [search, arxiv, wiki]

# Initialize the agent executor
@st.cache_resource
def initialize_agent(api_key):
    try:
        llm = ChatGroq(
            groq_api_key=api_key, 
            model_name="llama-3.1-8b-instant", 
            streaming=True,
            temperature=0.1
        )
        tools = initialize_tools()
        prompt_template = hub.pull("hwchase17/react")
        agent = create_react_agent(llm, tools, prompt_template)
        agent_executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True, 
            handle_parsing_errors=True,
            max_iterations=5
        )
        return agent_executor
    except Exception as e:
        st.error(f"Error initializing agent: {str(e)}")
        return None

# Function to extract sources from response
def extract_sources(response_text):
    sources = []
    
    # Extract URLs
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, response_text)
    
    for url in urls:
        # Categorize sources based on URL patterns
        if 'arxiv.org' in url:
            sources.append({"title": "arXiv Academic Paper", "url": url, "type": "academic"})
        elif 'wikipedia.org' in url:
            sources.append({"title": "Wikipedia Article", "url": url, "type": "encyclopedia"})
        elif 'doi.org' in url:
            sources.append({"title": "Research Paper", "url": url, "type": "research"})
        else:
            sources.append({"title": "Web Source", "url": url, "type": "web"})
    
    # Add source indicators based on content
    if any(keyword in response_text.lower() for keyword in ['arxiv', 'paper', 'research', 'study']):
        if not any(s['type'] == 'academic' for s in sources):
            sources.append({"title": "arXiv Repository", "url": "https://arxiv.org", "type": "academic"})
    
    if any(keyword in response_text.lower() for keyword in ['wikipedia', 'wiki']):
        if not any(s['type'] == 'encyclopedia' for s in sources):
            sources.append({"title": "Wikipedia", "url": "https://wikipedia.org", "type": "encyclopedia"})
    
    return sources

# Header section
st.markdown('<div class="main-header"> Syam\'s Search Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Powered by AI • Real-time Web Search • Academic Sources</div>', unsafe_allow_html=True)

# Get API key from environment (hidden from user)
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("""
    ❌ GROQ_API_KEY not found in environment variables. 
    
    Please set up your API key:
    1. Create a `.env` file in your project directory
    2. Add: `GROQ_API_KEY=your_actual_api_key_here`
    3. Restart the application
    """)
    st.stop()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "Hello! I'm your Syam's Search Assistant. I can help you search the web, find academic papers, and browse Wikipedia. What would you like to explore today?",
            "sources": []
        }
    ]

if "agent" not in st.session_state:
    with st.spinner("🔄 Initializing research assistant..."):
        st.session_state.agent = initialize_agent(api_key)

# Display chat messages with sources
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
    else:
        with st.chat_message("assistant"):
            st.markdown(f'<div class="assistant-message">{message["content"]}</div>', unsafe_allow_html=True)
            
            # Display sources if available
            if message.get("sources"):
                with st.container():
                    st.markdown('<div class="sources-section">', unsafe_allow_html=True)
                    st.markdown("**📚 Sources & References:**")
                    for source in message["sources"]:
                        if source.get("url"):
                            st.markdown(
                                f'<a href="{source["url"]}" class="source-link" target="_blank">🔗 {source["title"]}</a>', 
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(f'<div class="source-link">📄 {source["title"]}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

# Quick action buttons
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🎯 Latest AI Research", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": "Find the latest research papers about artificial intelligence from arXiv"})
        st.rerun()
with col2:
    if st.button("🌐 Search Wikipedia", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": "Search Wikipedia for current events in technology"})
        st.rerun()
with col3:
    if st.button("🔍 Web Search", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": "Search the web for recent developments in machine learning"})
        st.rerun()
with col4:
    if st.button("🧹 Clear Chat", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant", 
                "content": "Chat cleared! How can I assist you with your research today?",
                "sources": []
            }
        ]
        st.rerun()

# Chat input
st.markdown("---")
if prompt := st.chat_input("Ask me anything about research, news, or academic topics..."):
    if not st.session_state.agent:
        st.error("Research assistant is not properly initialized. Please check your API key.")
        st.stop()
    
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# Process the latest user message
if (st.session_state.messages and 
    st.session_state.messages[-1]["role"] == "user" and 
    st.session_state.agent):
    
    user_message = st.session_state.messages[-1]["content"]
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        sources_placeholder = st.empty()
        
        try:
            # Initialize callback handler with correct parameters
            st_cb = StreamlitCallbackHandler(
                st.container(), 
                expand_new_thoughts=False  # Removed invalid thought_label parameter
            )
            
            # Execute the agent
            with st.spinner("🔍 Searching for information..."):
                response = st.session_state.agent.invoke(
                    {"input": user_message}, 
                    {"callbacks": [st_cb]}
                )
            
            # Extract response
            output = response.get("output", "I apologize, but I couldn't generate a proper response.")
            
            # Extract sources from the response
            sources = extract_sources(output)
            
            # Add assistant response to chat
            st.session_state.messages.append({
                "role": "assistant", 
                "content": output,
                "sources": sources
            })
            
            # Display the response
            message_placeholder.markdown(f'<div class="assistant-message">{output}</div>', unsafe_allow_html=True)
            
            # Display sources
            if sources:
                with sources_placeholder.container():
                    st.markdown('<div class="sources-section">', unsafe_allow_html=True)
                    st.markdown("**📚 Sources & References:**")
                    for source in sources:
                        st.markdown(
                            f'<a href="{source["url"]}" class="source-link" target="_blank">🔗 {source["title"]}</a>', 
                            unsafe_allow_html=True
                        )
                    st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            error_msg = f"I encountered an issue while searching: {str(e)}. Let me provide a direct response instead."
            st.warning("Search tools are temporarily unavailable. Providing direct AI response...")
            
            try:
                # Fallback to direct LLM response
                llm = ChatGroq(groq_api_key=api_key, model_name="llama-3.1-8b-instant")
                direct_response = llm.invoke(user_message)
                fallback_content = direct_response.content
                
                # Extract sources even from fallback response
                fallback_sources = extract_sources(fallback_content)
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"{fallback_content}",
                    "sources": fallback_sources
                })
                
                message_placeholder.markdown(f'<div class="assistant-message">{fallback_content}</div>', unsafe_allow_html=True)
                
                # Display sources for fallback response
                if fallback_sources:
                    with sources_placeholder.container():
                        st.markdown('<div class="sources-section">', unsafe_allow_html=True)
                        st.markdown("**📚 Sources & References:**")
                        for source in fallback_sources:
                            st.markdown(
                                f'<a href="{source["url"]}" class="source-link" target="_blank">🔗 {source["title"]}</a>', 
                                unsafe_allow_html=True
                            )
                        st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as llm_error:
                final_error = "I'm experiencing technical difficulties. Please try again in a moment."
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": final_error,
                    "sources": []
                })
                message_placeholder.markdown(f'<div class="assistant-message">{final_error}</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>Powered by Groq • LangChain • Streamlit</p>
    <p>🔍 Web Search • 📚 arXiv • 🌐 Wikipedia</p>
</div>
""", unsafe_allow_html=True)