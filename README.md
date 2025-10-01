# Syam's Search Assistant - Development Documentation

![Search Assistant Banner](https://img.shields.io/badge/Syam's-Search%20Assistant-8A2BE2)

A powerful, AI-driven search assistant that seamlessly integrates web search, academic paper discovery, and encyclopedic knowledge into a single intuitive interface.

## 📋 Overview

Syam's Search Assistant is a Streamlit-powered web application that leverages the power of large language models and specialized search tools to provide comprehensive answers to user queries. The application can search the web, find academic papers, and browse Wikipedia articles to provide well-researched, accurate responses with proper source attribution.

## ✨ Features

- **Multi-source Research**: Integrates DuckDuckGo web search, arXiv academic papers, and Wikipedia articles
- **AI-Powered Responses**: Uses Groq's LLama 3.1 model to provide coherent, contextual answers
- **Real-time Streaming**: Displays AI thinking process and results as they arrive
- **Source Attribution**: Automatically extracts and displays sources used to generate responses
- **Elegant UI**: Professional, intuitive interface with gradient styling and responsive design
- **Quick Action Buttons**: One-click access to common search operations
- **Fallback Mechanisms**: Graceful error handling with alternative response strategies

## 🛠️ Technologies Used

- **Frontend**: Streamlit
- **AI Model**: Groq LLama 3.1 8B Instant
- **Orchestration**: LangChain (ReAct Agent)
- **Search Tools**:
  - DuckDuckGo Search API
  - arXiv API
  - Wikipedia API
- **Environment**: Python 3.x with dotenv for configuration

## 🚀 Getting Started

### Prerequisites

- Python 3.x
- Groq API key

### Installation

1. Clone the repository
   ```bash
   git clone <https://github.com/Syam-1133/Syam-Search-Assistant>
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root and add your Groq API key
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

### Running the Application

```bash
streamlit run main.py
```

Navigate to the URL provided by Streamlit (typically `http://localhost:8501`) to access the application.

## 💻 Usage

1. **Ask a Question**: Type your query in the chat input box at the bottom of the page
2. **Quick Actions**: Use the preset buttons for common search operations:
   - Latest AI Research
   - Search Wikipedia
   - Web Search
   - Clear Chat
3. **View Sources**: Each response includes a "Sources & References" section that links to the original information sources

## 📊 How It Works

1. **User Input Processing**: The application takes the user's query and passes it to the LangChain ReAct agent
2. **Tool Selection**: The agent decides which search tools to use based on the query
3. **Information Retrieval**: The selected tools search for relevant information from their respective sources
4. **Response Synthesis**: The LLM processes all retrieved information and generates a comprehensive answer
5. **Source Extraction**: The application automatically identifies and extracts source URLs from the response
6. **Rendering**: The answer and sources are displayed in the chat interface

## 🔧 Development Process

### Initial Setup and Planning

I started by identifying the core problem: users often need to search multiple sources for comprehensive information. I wanted to create a unified interface that would leverage AI to pull information from diverse sources and present it in a cohesive manner.

1. **Requirements Analysis**:
   - Needed access to web search, academic papers, and encyclopedic knowledge
   - Required an AI model capable of understanding complex queries
   - Wanted a user-friendly interface with real-time responses
   - Needed to properly attribute information sources

2. **Technology Selection**:
   - Chose Streamlit for rapid UI development and its Python compatibility
   - Selected Groq's Llama 3.1 for its speed and quality of responses
   - Implemented LangChain for its agent framework and tool integration capabilities
   - Integrated DuckDuckGo, arXiv, and Wikipedia as information sources

### Implementation Details

1. **Setting Up the Environment**:
   - Created a Python virtual environment
   - Installed necessary packages (Streamlit, LangChain, dotenv)
   - Set up API key management using environment variables

2. **Building the LangChain Agent**:
   - Configured the ChatGroq LLM with optimal temperature settings
   - Created tool wrappers for DuckDuckGo, arXiv, and Wikipedia
   - Set up a ReAct agent to intelligently choose between tools
   - Added error handling and fallback mechanisms

3. **Developing the UI**:
   - Designed a modern interface with gradient styling
   - Implemented chat message containers with user/assistant styling
   - Added source attribution section with clickable links
   - Created quick action buttons for common queries
   - Added CSS for responsive and professional appearance

4. **Advanced Features Implementation**:
   - Built a custom source extraction function using regex pattern matching
   - Implemented streaming responses using Streamlit callback handlers
   - Added session state management to maintain conversation history
   - Created graceful error handling with fallback to direct LLM responses

5. **Testing and Refinement**:
   - Tested with various query types to ensure appropriate tool selection
   - Optimized search parameters for each tool (top_k, document length)
   - Added user-friendly error messages for common issues
   - Fine-tuned the UI for better user experience

## ⚙️ Configuration

The application uses the following key configuration:

- **LLM Model**: llama-3.1-8b-instant
- **Temperature**: 0.1 (focused, deterministic responses)
- **Max Iterations**: 5 (for the ReAct agent)
- **Search Settings**:
  - arXiv: Top 3 results, max 500 characters per document
  - Wikipedia: Top 3 results, max 500 characters per document

## 📝 Code Examples

Here are some key implementation details that showcase how the application was built:

### Tool Initialization

```python
# Initialize tools with enhanced configuration
@st.cache_resource
def initialize_tools():
    arxiv_wrapper = ArxivAPIWrapper(top_k_results=3, doc_content_chars_max=500)
    arxiv = ArxivQueryRun(api_wrapper=arxiv_wrapper)

    wikipedia_wrapper = WikipediaAPIWrapper(top_k_results=3, doc_content_chars_max=500)
    wiki = WikipediaQueryRun(api_wrapper=wikipedia_wrapper)

    search = DuckDuckGoSearchRun(name="WebSearch")
    
    return [search, arxiv, wiki]
```

### Agent Creation

```python
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
```

### Custom Source Extraction

```python
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
    
    return sources
```

## 🛡️ Error Handling

The application includes robust error handling:

- **API Connectivity Issues**: Falls back to direct LLM responses if search tools are unavailable
- **Missing API Key**: Clear error message with setup instructions
- **Agent Parsing Errors**: Automatic handling with graceful degradation





## 📄 License

[MIT License](LICENSE)

## 👨‍💻 Author

Syam Gudipudi

---

*Powered by Groq • LangChain • Streamlit*
